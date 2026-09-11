"""LoRA export and inference helpers for section 11.6."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Literal, Tuple


QuantizationMode = Literal["none", "8bit", "4bit"]


def merge_lora_adapter(
    adapter_path: str | Path,
    output_dir: str | Path,
) -> Path:
    """Merge a trained LoRA adapter into its base model and save both assets."""
    source = Path(adapter_path).expanduser()
    destination = Path(output_dir).expanduser()
    if not (source / "adapter_config.json").is_file():
        raise ValueError(f"LoRA adapter_config.json was not found in {source}")
    if source.resolve() == destination.resolve():
        raise ValueError("output_dir must differ from adapter_path")

    try:
        from peft import AutoPeftModelForCausalLM
        from transformers import AutoTokenizer
    except ImportError as exc:
        raise ImportError("合并 LoRA 需要安装 peft 和 transformers") from exc

    model = AutoPeftModelForCausalLM.from_pretrained(
        str(source),
        torch_dtype="auto",
        trust_remote_code=True,
    )
    tokenizer = AutoTokenizer.from_pretrained(
        str(source),
        trust_remote_code=True,
    )
    merged_model = model.merge_and_unload()
    destination.mkdir(parents=True, exist_ok=True)
    merged_model.save_pretrained(str(destination), safe_serialization=True)
    tokenizer.save_pretrained(str(destination))
    return destination


def load_inference_model(
    model_path: str | Path,
    quantization: QuantizationMode = "none",
) -> Tuple[Any, Any]:
    """Load a merged model or PEFT adapter, optionally in 8-bit or 4-bit."""
    source = Path(model_path).expanduser()
    if quantization not in {"none", "8bit", "4bit"}:
        raise ValueError("quantization must be none, 8bit or 4bit")

    try:
        from transformers import (
            AutoModelForCausalLM,
            AutoTokenizer,
            BitsAndBytesConfig,
        )
    except ImportError as exc:
        raise ImportError("模型推理需要安装 transformers") from exc

    model_kwargs = {
        "device_map": "auto",
        "torch_dtype": "auto",
        "trust_remote_code": True,
    }
    if quantization != "none":
        model_kwargs["quantization_config"] = BitsAndBytesConfig(
            load_in_8bit=quantization == "8bit",
            load_in_4bit=quantization == "4bit",
        )

    if (source / "adapter_config.json").is_file():
        try:
            from peft import AutoPeftModelForCausalLM
        except ImportError as exc:
            raise ImportError("加载 LoRA Adapter 需要安装 peft") from exc
        model = AutoPeftModelForCausalLM.from_pretrained(
            str(source), **model_kwargs
        )
    else:
        model = AutoModelForCausalLM.from_pretrained(
            str(source), **model_kwargs
        )
    tokenizer = AutoTokenizer.from_pretrained(
        str(source), trust_remote_code=True
    )
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token
    model.eval()
    return model, tokenizer


def generate_math_response(
    model: Any,
    tokenizer: Any,
    question: str,
    max_new_tokens: int = 512,
) -> str:
    """Generate one answer with the model's own chat template."""
    normalized_question = question.strip()
    if not normalized_question:
        raise ValueError("question cannot be empty")
    if max_new_tokens <= 0:
        raise ValueError("max_new_tokens must be positive")

    prompt = tokenizer.apply_chat_template(
        [
            {
                "role": "user",
                "content": (
                    f"Question: {normalized_question}\n\n"
                    "Let's solve this step by step:"
                ),
            }
        ],
        tokenize=False,
        add_generation_prompt=True,
    )
    encoded = tokenizer(prompt, return_tensors="pt").to(model.device)

    try:
        import torch
    except ImportError as exc:
        raise ImportError("模型推理需要安装 torch") from exc
    with torch.inference_mode():
        generated = model.generate(
            **encoded,
            max_new_tokens=max_new_tokens,
            do_sample=False,
            pad_token_id=tokenizer.pad_token_id,
        )
    prompt_length = encoded["input_ids"].shape[1]
    return tokenizer.decode(
        generated[0][prompt_length:],
        skip_special_tokens=True,
    ).strip()
