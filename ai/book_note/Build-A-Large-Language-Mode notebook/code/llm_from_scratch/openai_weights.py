"""下载并把 OpenAI GPT-2 TensorFlow 权重映射到本地 GPTModel。"""

from __future__ import annotations

import importlib.util
import urllib.request
from collections.abc import Callable, Mapping
from pathlib import Path
from typing import Any

import numpy as np
import torch
from torch import nn

from .config import GPT2_MODEL_CONFIGS, GPTConfig, create_gpt2_config
from .model import GPTModel


GPT_DOWNLOAD_URL = (
    "https://raw.githubusercontent.com/rasbt/"
    "LLMs-from-scratch/main/ch05/01_main-chapter-code/gpt_download.py"
)

__all__ = [
    "GPT_DOWNLOAD_URL",
    "download_gpt_download_script",
    "import_gpt_download",
    "assign_parameter",
    "load_weights_into_gpt",
    "load_pretrained_gpt2",
]


def download_gpt_download_script(
    script_path: str | Path = "gpt_download.py",
    *,
    url: str = GPT_DOWNLOAD_URL,
    timeout: float = 60.0,
) -> Path:
    """按需下载原书的 ``gpt_download.py`` 并返回本地路径。"""
    destination = Path(script_path)
    if destination.exists():
        return destination

    destination.parent.mkdir(parents=True, exist_ok=True)
    with urllib.request.urlopen(url, timeout=timeout) as response:
        script_bytes = response.read()

    temporary_path = destination.with_suffix(destination.suffix + ".part")
    temporary_path.write_bytes(script_bytes)
    temporary_path.replace(destination)
    return destination


def import_gpt_download(script_path: str | Path) -> Callable[..., Any]:
    """从指定脚本中加载 ``download_and_load_gpt2`` 函数。"""
    path = Path(script_path).resolve()
    if not path.exists():
        raise FileNotFoundError(f"GPT-2 下载脚本不存在：{path}")

    module_name = f"_llm_from_scratch_gpt_download_{abs(hash(path))}"
    spec = importlib.util.spec_from_file_location(module_name, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"无法从路径创建模块：{path}")

    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    download_function = getattr(module, "download_and_load_gpt2", None)
    if not callable(download_function):
        raise ImportError(f"{path} 未定义 download_and_load_gpt2")
    return download_function


def assign_parameter(left: torch.Tensor, right: Any) -> nn.Parameter:
    """检查形状，并以左参数的 dtype/device 创建新参数。"""
    right_tensor = torch.as_tensor(
        right,
        dtype=left.dtype,
        device=left.device,
    )
    if left.shape != right_tensor.shape:
        raise ValueError(
            f"Shape mismatch. Left: {left.shape}, Right: {right_tensor.shape}"
        )
    return nn.Parameter(right_tensor.detach().clone())


def load_weights_into_gpt(
    model: GPTModel,
    params: Mapping[str, Any],
) -> GPTModel:
    """把原始 GPT-2 参数字典映射到书中实现的 GPTModel。"""
    blocks = params["blocks"]
    if len(blocks) != len(model.trf_blocks):
        raise ValueError(
            "Transformer 层数不匹配："
            f"model={len(model.trf_blocks)}, weights={len(blocks)}"
        )

    model.pos_emb.weight = assign_parameter(model.pos_emb.weight, params["wpe"])
    model.tok_emb.weight = assign_parameter(model.tok_emb.weight, params["wte"])

    for block_index, openai_block in enumerate(blocks):
        model_block = model.trf_blocks[block_index]
        attention = openai_block["attn"]

        query_weight, key_weight, value_weight = np.split(
            attention["c_attn"]["w"],
            3,
            axis=-1,
        )
        model_block.att.W_query.weight = assign_parameter(
            model_block.att.W_query.weight,
            query_weight.T,
        )
        model_block.att.W_key.weight = assign_parameter(
            model_block.att.W_key.weight,
            key_weight.T,
        )
        model_block.att.W_value.weight = assign_parameter(
            model_block.att.W_value.weight,
            value_weight.T,
        )

        query_bias, key_bias, value_bias = np.split(
            attention["c_attn"]["b"],
            3,
            axis=-1,
        )
        if (
            model_block.att.W_query.bias is None
            or model_block.att.W_key.bias is None
            or model_block.att.W_value.bias is None
        ):
            raise ValueError("加载 OpenAI GPT-2 权重时必须使用 qkv_bias=True")
        model_block.att.W_query.bias = assign_parameter(
            model_block.att.W_query.bias,
            query_bias,
        )
        model_block.att.W_key.bias = assign_parameter(
            model_block.att.W_key.bias,
            key_bias,
        )
        model_block.att.W_value.bias = assign_parameter(
            model_block.att.W_value.bias,
            value_bias,
        )

        model_block.att.out_proj.weight = assign_parameter(
            model_block.att.out_proj.weight,
            attention["c_proj"]["w"].T,
        )
        model_block.att.out_proj.bias = assign_parameter(
            model_block.att.out_proj.bias,
            attention["c_proj"]["b"],
        )

        mlp = openai_block["mlp"]
        model_block.ff.layers[0].weight = assign_parameter(
            model_block.ff.layers[0].weight,
            mlp["c_fc"]["w"].T,
        )
        model_block.ff.layers[0].bias = assign_parameter(
            model_block.ff.layers[0].bias,
            mlp["c_fc"]["b"],
        )
        model_block.ff.layers[2].weight = assign_parameter(
            model_block.ff.layers[2].weight,
            mlp["c_proj"]["w"].T,
        )
        model_block.ff.layers[2].bias = assign_parameter(
            model_block.ff.layers[2].bias,
            mlp["c_proj"]["b"],
        )

        model_block.norm1.scale = assign_parameter(
            model_block.norm1.scale,
            openai_block["ln_1"]["g"],
        )
        model_block.norm1.shift = assign_parameter(
            model_block.norm1.shift,
            openai_block["ln_1"]["b"],
        )
        model_block.norm2.scale = assign_parameter(
            model_block.norm2.scale,
            openai_block["ln_2"]["g"],
        )
        model_block.norm2.shift = assign_parameter(
            model_block.norm2.shift,
            openai_block["ln_2"]["b"],
        )

    model.final_norm.scale = assign_parameter(model.final_norm.scale, params["g"])
    model.final_norm.shift = assign_parameter(model.final_norm.shift, params["b"])
    model.out_head.weight = assign_parameter(model.out_head.weight, params["wte"])
    return model


def _model_size_from_name(model_name: str) -> str:
    if model_name not in GPT2_MODEL_CONFIGS:
        supported = ", ".join(GPT2_MODEL_CONFIGS)
        raise ValueError(f"未知 GPT-2 规格 {model_name!r}；可选值：{supported}")
    try:
        return model_name.rsplit("(", 1)[1].rstrip(")")
    except IndexError as error:
        raise ValueError(f"模型名称中缺少规格标记：{model_name}") from error


def _validate_settings(settings: Mapping[str, Any], config: GPTConfig) -> None:
    expected = {
        "n_vocab": config.vocab_size,
        "n_ctx": config.context_length,
        "n_embd": config.emb_dim,
        "n_head": config.n_heads,
        "n_layer": config.n_layers,
    }
    mismatches = {
        key: (settings.get(key), value)
        for key, value in expected.items()
        if key in settings and settings[key] != value
    }
    if mismatches:
        raise ValueError(f"下载权重与模型配置不一致：{mismatches}")


def load_pretrained_gpt2(
    model_name: str = "gpt2-small (124M)",
    *,
    models_dir: str | Path = "gpt2",
    script_path: str | Path = "gpt_download.py",
    device: str | torch.device = "cpu",
) -> tuple[GPTModel, GPTConfig]:
    """下载指定 GPT-2 权重，构建模型并完成参数映射。"""
    config = create_gpt2_config(model_name, drop_rate=0.0, qkv_bias=True)
    local_script = download_gpt_download_script(script_path)
    download_and_load_gpt2 = import_gpt_download(local_script)
    settings, params = download_and_load_gpt2(
        model_size=_model_size_from_name(model_name),
        models_dir=str(models_dir),
    )
    _validate_settings(settings, config)

    model = GPTModel(config)
    load_weights_into_gpt(model, params)
    model.to(device)
    model.eval()
    return model, config
