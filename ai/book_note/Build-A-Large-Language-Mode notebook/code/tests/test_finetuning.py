"""第 5～7 章整理代码的无网络轻量测试。"""

from __future__ import annotations

import math

import pytest

torch = pytest.importorskip("torch")
pd = pytest.importorskip("pandas")
np = pytest.importorskip("numpy")

import torch.nn.functional as F
from torch import nn

from llm_from_scratch.classification import (
    SpamDataset,
    classification_loader_loss,
    configure_classifier,
)
from llm_from_scratch.checkpoint import (
    load_training_checkpoint,
    save_training_checkpoint,
)
from llm_from_scratch.config import GPTConfig
from llm_from_scratch.instruction import (
    collate_instruction_batch,
    format_instruction_example,
    format_instruction_prompt,
    generate_instruction_responses,
)
from llm_from_scratch.lora import (
    LinearWithLoRA,
    LoRALayer,
    apply_lora,
    count_trainable_parameters,
)
from llm_from_scratch.model import GPTModel
from llm_from_scratch.openai_weights import assign_parameter
from llm_from_scratch.training import (
    causal_lm_loader_loss,
    clip_gradient_norm,
    cosine_decay_lr,
    linear_warmup_lr,
    train_causal_lm,
)


class ToyLanguageModel(nn.Module):
    def __init__(self, vocab_size: int = 8) -> None:
        super().__init__()
        self.vocab_size = vocab_size

    def forward(self, input_ids: torch.Tensor) -> torch.Tensor:
        logits = torch.zeros(
            *input_ids.shape,
            self.vocab_size,
            dtype=torch.float32,
            device=input_ids.device,
        )
        preferred = input_ids.remainder(self.vocab_size).unsqueeze(-1)
        return logits.scatter(-1, preferred, 2.0)


class ToyClassifier(nn.Module):
    def forward(self, input_ids: torch.Tensor) -> torch.Tensor:
        score = input_ids[:, 0].float() - 1.0
        final_logits = torch.stack((-score, score), dim=-1)
        return final_logits.unsqueeze(1).expand(-1, input_ids.shape[1], -1)


class FakeTokenizer:
    def encode(self, text: str, **_: object) -> list[int]:
        if not text:
            return []
        try:
            return [int(piece) for piece in text.split()]
        except ValueError:
            return [1, 2, 3]

    def decode(self, token_ids: list[int]) -> str:
        return " ".join(str(token_id) for token_id in token_ids)


def test_instruction_formatting_with_and_without_input() -> None:
    with_input = {"instruction": "Sort", "input": "b, a", "output": "a, b"}
    without_input = {"instruction": "Say hi", "input": "", "output": "Hi"}

    assert "### Input:\nb, a" in format_instruction_prompt(with_input)
    assert "### Input:" not in format_instruction_prompt(without_input)
    assert format_instruction_example(with_input).endswith("### Response:\na, b")


def test_instruction_collate_masks_padding_and_keeps_eos_after_truncation() -> None:
    inputs, targets = collate_instruction_batch(
        ([0, 1, 2, 3, 4], [5, 6], [7, 8, 9]),
    )
    assert inputs.device.type == "cpu"
    assert inputs.tolist() == [
        [0, 1, 2, 3, 4],
        [5, 6, 50256, 50256, 50256],
        [7, 8, 9, 50256, 50256],
    ]
    assert targets.tolist() == [
        [1, 2, 3, 4, 50256],
        [6, 50256, -100, -100, -100],
        [8, 9, 50256, -100, -100],
    ]

    truncated_inputs, truncated_targets = collate_instruction_batch(
        ([0, 1, 2, 3, 4, 5],),
        allowed_max_length=4,
    )
    assert truncated_inputs.tolist() == [[0, 1, 2, 3]]
    assert truncated_targets.tolist() == [[1, 2, 3, 50256]]


def test_causal_lm_loader_loss_is_weighted_by_valid_tokens() -> None:
    model = ToyLanguageModel()
    batches = [
        (
            torch.tensor([[0, 1, 2], [1, 2, 3]]),
            torch.tensor([[1, 2, -100], [2, 3, 4]]),
        ),
        (torch.tensor([[4, 5, 6]]), torch.tensor([[5, -100, -100]])),
    ]

    loss = causal_lm_loader_loss(batches, model, "cpu")
    loss_sum = 0.0
    valid_tokens = 0
    for inputs, targets in batches:
        logits = model(inputs)
        loss_sum += F.cross_entropy(
            logits.flatten(0, 1),
            targets.flatten(),
            ignore_index=-100,
            reduction="sum",
        ).item()
        valid_tokens += int((targets != -100).sum())
    assert loss == pytest.approx(loss_sum / valid_tokens)
    assert math.isnan(causal_lm_loader_loss([], model, "cpu"))
    with pytest.raises(ValueError, match="num_batches"):
        causal_lm_loader_loss(batches, model, "cpu", num_batches=0)


def test_classification_loader_loss_is_weighted_by_examples() -> None:
    model = ToyClassifier()
    batches = [
        (torch.tensor([[0, 0], [2, 0]]), torch.tensor([0, 1])),
        (torch.tensor([[1, 0]]), torch.tensor([1])),
    ]

    loss = classification_loader_loss(batches, model, "cpu")
    expected_sum = sum(
        F.cross_entropy(model(inputs)[:, -1, :], targets, reduction="sum").item()
        for inputs, targets in batches
    )
    assert loss == pytest.approx(expected_sum / 3)
    assert math.isnan(classification_loader_loss([], model, "cpu"))
    with pytest.raises(ValueError, match="num_batches"):
        classification_loader_loss(batches, model, "cpu", num_batches=-1)


def test_configure_classifier_only_unfreezes_expected_layers() -> None:
    config = GPTConfig(
        vocab_size=32,
        context_length=8,
        emb_dim=12,
        n_heads=3,
        n_layers=2,
        drop_rate=0.0,
    )
    model = configure_classifier(GPTModel(config), num_classes=2)
    assert model.out_head.out_features == 2
    assert not any(parameter.requires_grad for parameter in model.trf_blocks[0].parameters())
    assert all(parameter.requires_grad for parameter in model.trf_blocks[-1].parameters())
    assert all(parameter.requires_grad for parameter in model.final_norm.parameters())
    assert all(parameter.requires_grad for parameter in model.out_head.parameters())


def test_lora_layer_starts_with_zero_update() -> None:
    torch.manual_seed(123)
    layer = LoRALayer(in_dim=3, out_dim=2, rank=2, alpha=4.0)
    inputs = torch.randn(5, 3)

    torch.testing.assert_close(layer(inputs), torch.zeros(5, 2))
    assert layer.A.shape == (3, 2)
    assert layer.B.shape == (2, 2)
    assert layer.scaling == pytest.approx(2.0)


def test_apply_lora_preserves_initial_output_and_freezes_base_model() -> None:
    torch.manual_seed(123)
    model = nn.Sequential(
        nn.Linear(3, 4),
        nn.ReLU(),
        nn.Sequential(nn.Linear(4, 2)),
    )
    inputs = torch.randn(5, 3)
    output_before = model(inputs).detach()

    replacements = apply_lora(model, rank=2, alpha=4.0)
    output_after = model(inputs)

    assert replacements == 2
    assert sum(
        isinstance(module, LinearWithLoRA)
        for module in model.modules()
    ) == 2
    torch.testing.assert_close(output_before, output_after)

    wrapped_layers = [
        module
        for module in model.modules()
        if isinstance(module, LinearWithLoRA)
    ]
    assert all(
        not parameter.requires_grad
        for layer in wrapped_layers
        for parameter in layer.linear.parameters()
    )
    assert all(
        parameter.requires_grad
        for layer in wrapped_layers
        for parameter in layer.lora.parameters()
    )
    assert count_trainable_parameters(model) == 26


def test_apply_lora_rejects_invalid_or_repeated_configuration() -> None:
    with pytest.raises(ValueError, match="rank"):
        LoRALayer(in_dim=3, out_dim=2, rank=0, alpha=1.0)
    with pytest.raises(ValueError, match="alpha"):
        LoRALayer(in_dim=3, out_dim=2, rank=1, alpha=float("inf"))

    model = nn.Sequential(nn.Linear(3, 2))
    apply_lora(model, rank=1, alpha=1.0)
    with pytest.raises(ValueError, match="已经包含"):
        apply_lora(model, rank=1, alpha=1.0)


def test_spam_dataset_uses_training_length_for_padding(tmp_path: object) -> None:
    csv_path = tmp_path / "messages.csv"
    pd.DataFrame(
        {"Label": [0, 1], "Text": ["1 2", "3 4 5 6"]}
    ).to_csv(csv_path, index=False)
    dataset = SpamDataset(csv_path, FakeTokenizer(), max_length=3, pad_token_id=7)

    first_tokens, first_label = dataset[0]
    second_tokens, second_label = dataset[1]
    assert first_tokens.tolist() == [1, 2, 7]
    assert second_tokens.tolist() == [3, 4, 5]
    assert (first_label.item(), second_label.item()) == (0, 1)


def test_assign_parameter_checks_shape_and_preserves_dtype() -> None:
    left = nn.Parameter(torch.zeros(2, 3, dtype=torch.float64))
    assigned = assign_parameter(left, np.ones((2, 3), dtype=np.float32))
    assert assigned.dtype == torch.float64
    assert assigned.device == left.device
    with pytest.raises(ValueError, match="Shape mismatch"):
        assign_parameter(left, np.ones((3, 2), dtype=np.float32))


def test_training_checkpoint_round_trip(tmp_path: object) -> None:
    config = GPTConfig(
        vocab_size=16,
        context_length=4,
        emb_dim=8,
        n_heads=2,
        n_layers=1,
        drop_rate=0.0,
    )
    model = GPTModel(config)
    optimizer = torch.optim.AdamW(model.parameters(), lr=1e-3)
    loss = model(torch.tensor([[0, 1, 2]])).sum()
    loss.backward()
    optimizer.step()

    checkpoint_path = tmp_path / "training.pth"
    save_training_checkpoint(
        model,
        optimizer,
        checkpoint_path,
        completed_epochs=3,
        tokens_seen=144,
    )

    restored_model = GPTModel(config)
    restored_optimizer = torch.optim.AdamW(restored_model.parameters(), lr=1e-3)
    metadata = load_training_checkpoint(
        restored_model,
        restored_optimizer,
        checkpoint_path,
    )

    assert metadata == {"completed_epochs": 3, "tokens_seen": 144}
    for original, restored in zip(model.parameters(), restored_model.parameters()):
        torch.testing.assert_close(original, restored)
    assert restored_optimizer.state_dict()["state"]


def test_train_causal_lm_runs_one_update() -> None:
    class TrainableLanguageModel(nn.Module):
        def __init__(self) -> None:
            super().__init__()
            self.embedding = nn.Embedding(8, 4)
            self.output = nn.Linear(4, 8)

        def forward(self, input_ids: torch.Tensor) -> torch.Tensor:
            return self.output(self.embedding(input_ids))

    model = TrainableLanguageModel()
    batch = (torch.tensor([[0, 1, 2]]), torch.tensor([[1, 2, 3]]))
    loader = [batch]
    optimizer = torch.optim.AdamW(model.parameters(), lr=1e-3)
    before = model.output.weight.detach().clone()
    history = train_causal_lm(
        model,
        loader,
        loader,
        optimizer,
        "cpu",
        num_epochs=1,
        eval_freq=1,
        eval_iter=1,
    )
    assert len(history[0]) == len(history[1]) == len(history[2]) == 1
    assert not torch.equal(before, model.output.weight)


def test_linear_warmup_lr_reaches_and_keeps_peak() -> None:
    learning_rates = [
        linear_warmup_lr(
            step,
            warmup_steps=4,
            initial_lr=1e-5,
            peak_lr=4e-4,
        )
        for step in range(7)
    ]

    assert learning_rates == pytest.approx(
        [1e-5, 0.0001075, 0.000205, 0.0003025, 4e-4, 4e-4, 4e-4]
    )
    assert linear_warmup_lr(
        0,
        warmup_steps=0,
        initial_lr=1.0,
        peak_lr=4e-4,
    ) == pytest.approx(4e-4)


@pytest.mark.parametrize(
    "kwargs",
    [
        {"step": -1, "warmup_steps": 4, "initial_lr": 0.0, "peak_lr": 1e-3},
        {"step": 0, "warmup_steps": -1, "initial_lr": 0.0, "peak_lr": 1e-3},
        {"step": 0, "warmup_steps": 4, "initial_lr": -1e-4, "peak_lr": 1e-3},
        {"step": 0, "warmup_steps": 4, "initial_lr": 2e-3, "peak_lr": 1e-3},
    ],
)
def test_linear_warmup_lr_rejects_invalid_values(
    kwargs: dict[str, int | float],
) -> None:
    with pytest.raises(ValueError):
        linear_warmup_lr(**kwargs)


def test_cosine_decay_lr_maps_peak_to_minimum() -> None:
    learning_rates = [
        cosine_decay_lr(
            step,
            warmup_steps=20,
            total_training_steps=120,
            peak_lr=1.0,
            min_lr=0.1,
        )
        for step in (20, 70, 120, 140)
    ]

    assert learning_rates == pytest.approx([1.0, 0.55, 0.1, 0.1])


@pytest.mark.parametrize(
    "kwargs",
    [
        {
            "step": 19,
            "warmup_steps": 20,
            "total_training_steps": 120,
            "peak_lr": 1.0,
            "min_lr": 0.1,
        },
        {
            "step": 20,
            "warmup_steps": 20,
            "total_training_steps": 20,
            "peak_lr": 1.0,
            "min_lr": 0.1,
        },
        {
            "step": 20,
            "warmup_steps": 20,
            "total_training_steps": 120,
            "peak_lr": 0.1,
            "min_lr": 1.0,
        },
    ],
)
def test_cosine_decay_lr_rejects_invalid_values(
    kwargs: dict[str, int | float],
) -> None:
    with pytest.raises(ValueError):
        cosine_decay_lr(**kwargs)


def test_clip_gradient_norm_rescales_total_l2_norm() -> None:
    model = nn.Linear(2, 2, bias=False)
    original_gradient = torch.tensor([[1.0, 2.0], [2.0, 4.0]])
    model.weight.grad = original_gradient.clone()

    norm_before_clipping = clip_gradient_norm(model, max_norm=1.0)

    assert norm_before_clipping.item() == pytest.approx(5.0)
    assert torch.linalg.vector_norm(model.weight.grad).item() == pytest.approx(
        1.0,
        abs=1e-6,
    )
    torch.testing.assert_close(
        model.weight.grad,
        original_gradient / 5.0,
        rtol=1e-5,
        atol=1e-6,
    )


def test_clip_gradient_norm_keeps_small_gradient_and_validates_threshold() -> None:
    model = nn.Linear(2, 1, bias=False)
    original_gradient = torch.tensor([[0.3, 0.4]])
    model.weight.grad = original_gradient.clone()

    norm_before_clipping = clip_gradient_norm(model, max_norm=1.0)

    assert norm_before_clipping.item() == pytest.approx(0.5)
    torch.testing.assert_close(model.weight.grad, original_gradient)
    for invalid_max_norm in (0.0, -1.0, float("inf"), float("nan")):
        with pytest.raises(ValueError, match="max_norm"):
            clip_gradient_norm(model, max_norm=invalid_max_norm)


def test_train_causal_lm_applies_warmup_before_optimizer_step() -> None:
    class TrainableLanguageModel(nn.Module):
        def __init__(self) -> None:
            super().__init__()
            self.embedding = nn.Embedding(8, 4)
            self.output = nn.Linear(4, 8)

        def forward(self, input_ids: torch.Tensor) -> torch.Tensor:
            return self.output(self.embedding(input_ids))

    class RecordingSGD(torch.optim.SGD):
        def __init__(self, parameters: object, lr: float) -> None:
            super().__init__(parameters, lr=lr)
            self.learning_rates: list[float] = []

        def step(self, closure: object = None) -> object:
            self.learning_rates.append(float(self.param_groups[0]["lr"]))
            return super().step(closure)

    model = TrainableLanguageModel()
    batch = (torch.tensor([[0, 1, 2]]), torch.tensor([[1, 2, 3]]))
    loader = [batch, batch, batch, batch]
    optimizer = RecordingSGD(model.parameters(), lr=0.1)

    train_causal_lm(
        model,
        loader,
        loader,
        optimizer,
        "cpu",
        num_epochs=1,
        eval_freq=4,
        eval_iter=1,
        warmup_steps=2,
        initial_lr=0.0,
    )

    assert optimizer.learning_rates == pytest.approx([0.0, 0.05, 0.1, 0.1])


def test_train_causal_lm_applies_cosine_decay_after_warmup() -> None:
    class TrainableLanguageModel(nn.Module):
        def __init__(self) -> None:
            super().__init__()
            self.embedding = nn.Embedding(8, 4)
            self.output = nn.Linear(4, 8)

        def forward(self, input_ids: torch.Tensor) -> torch.Tensor:
            return self.output(self.embedding(input_ids))

    class RecordingSGD(torch.optim.SGD):
        def __init__(self, parameters: object, lr: float) -> None:
            super().__init__(parameters, lr=lr)
            self.learning_rates: list[float] = []

        def step(self, closure: object = None) -> object:
            self.learning_rates.append(float(self.param_groups[0]["lr"]))
            return super().step(closure)

    model = TrainableLanguageModel()
    batch = (torch.tensor([[0, 1, 2]]), torch.tensor([[1, 2, 3]]))
    loader = [batch, batch, batch]
    optimizer = RecordingSGD(model.parameters(), lr=1.0)

    train_causal_lm(
        model,
        loader,
        loader,
        optimizer,
        "cpu",
        num_epochs=1,
        eval_freq=3,
        eval_iter=1,
        warmup_steps=1,
        initial_lr=0.0,
        min_lr=0.1,
    )

    assert optimizer.learning_rates == pytest.approx([0.0, 1.0, 0.55])


def test_train_causal_lm_clips_gradients_after_warmup() -> None:
    class TrainableLanguageModel(nn.Module):
        def __init__(self) -> None:
            super().__init__()
            self.embedding = nn.Embedding(8, 4)
            self.output = nn.Linear(4, 8)

        def forward(self, input_ids: torch.Tensor) -> torch.Tensor:
            return self.output(self.embedding(input_ids))

    class GradientRecordingSGD(torch.optim.SGD):
        def __init__(self, parameters: object, lr: float) -> None:
            super().__init__(parameters, lr=lr)
            self.gradient_norms: list[float] = []

        def step(self, closure: object = None) -> object:
            gradients = [
                parameter.grad.detach().flatten()
                for group in self.param_groups
                for parameter in group["params"]
                if parameter.grad is not None
            ]
            total_norm = torch.linalg.vector_norm(torch.cat(gradients))
            self.gradient_norms.append(float(total_norm))
            return super().step(closure)

    torch.manual_seed(123)
    model = TrainableLanguageModel()
    batch = (torch.tensor([[0, 1, 2]]), torch.tensor([[1, 2, 3]]))
    loader = [batch, batch, batch]
    optimizer = GradientRecordingSGD(model.parameters(), lr=0.1)

    train_causal_lm(
        model,
        loader,
        loader,
        optimizer,
        "cpu",
        num_epochs=1,
        eval_freq=3,
        eval_iter=1,
        warmup_steps=1,
        max_grad_norm=0.1,
    )

    assert optimizer.gradient_norms[0] > 0.1
    assert optimizer.gradient_norms[1] > 0.1
    assert optimizer.gradient_norms[2] == pytest.approx(0.1, abs=1e-6)


def test_instruction_responses_are_sliced_by_token(monkeypatch: pytest.MonkeyPatch) -> None:
    import llm_from_scratch.instruction as instruction_module

    tokenizer = FakeTokenizer()
    model = nn.Identity()

    def fake_generate(**kwargs: object) -> torch.Tensor:
        prompt_ids = kwargs["idx"]
        suffix = torch.tensor([[7, 50256, 9]], dtype=torch.long)
        return torch.cat((prompt_ids, suffix), dim=1)

    monkeypatch.setattr(instruction_module, "generate_token_ids", fake_generate)
    data = [{"instruction": "1", "input": "", "output": "2"}]
    responses = generate_instruction_responses(
        data,
        model,
        tokenizer,
        "cpu",
        context_size=16,
        show_progress=False,
    )
    assert responses[0]["model_response"] == "7"
    assert "model_response" not in data[0]


def test_instruction_response_removes_only_leading_response_header(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import llm_from_scratch.instruction as instruction_module

    class HeaderTokenizer(FakeTokenizer):
        def decode(self, token_ids: list[int]) -> str:
            return "  ### Response:\nanswer with ### Response: inside  "

    def fake_generate(**kwargs: object) -> torch.Tensor:
        prompt_ids = kwargs["idx"]
        return torch.cat((prompt_ids, torch.tensor([[7]])), dim=1)

    monkeypatch.setattr(instruction_module, "generate_token_ids", fake_generate)
    responses = generate_instruction_responses(
        [{"instruction": "1", "input": "", "output": "2"}],
        nn.Identity(),
        HeaderTokenizer(),
        "cpu",
        context_size=16,
        show_progress=False,
    )
    assert responses[0]["model_response"] == "answer with ### Response: inside"
