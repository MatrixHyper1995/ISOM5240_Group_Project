"""
Sephora Skin Concern Advisor — Generator 模型（推荐文案续写 + 模板回退）
Recommendation copy generation (text-generation) with template fallback.

参考 / Reference: Image Storyteller 的「风格开头句 + 续写」机制 ——
映射表只给「事实」，把推荐「说出口」交给轻量 text-gen；失败回退模板，不断流程。
"""
import gc

import streamlit as st
from transformers import pipeline

import config
from utils import get_ingredients, get_opener, get_severity_label, format_opener


@st.cache_resource
def load_generator(model_id: str):
    """加载并缓存 text-generation 模型（按 model_id 缓存）。"""
    return pipeline("text-generation", model=model_id)


def release_generator() -> None:
    """释放 Generator 模型缓存，腾出内存（给 review 让位）。"""
    load_generator.clear()
    gc.collect()


def _fallback_reason(ingredients: list[str], label: str) -> str:
    """无模型回退理由：成分 + 合规表述（不诊断）。"""
    primary = ingredients[0]
    others = ", ".join(ingredients[1:]) if len(ingredients) > 1 else ""
    reason = f"{primary} is commonly used in cosmetic skincare for {label} breakout concerns"
    if others:
        reason += f", alongside {others}"
    return reason + "."


def generate(style: str, key: str, model_id: str | None = None) -> str:
    """生成推荐文案：opener（风格×档位）+ 成分续写；text-gen 失败回退模板。model_id 缺省用 config.GEN_MODEL。"""
    model_id = model_id or config.GEN_MODEL
    ingredients = get_ingredients(key)
    primary = ingredients[0]
    label = get_severity_label(key).lower()
    opener = format_opener(get_opener(style, key), primary)
    reason = _fallback_reason(ingredients, label)

    if not config.ENABLE_TEXT_GEN:
        return f"{opener} {reason}"

    try:
        generator = load_generator(model_id)
        out = generator(
            opener,
            max_new_tokens=40,
            do_sample=True,
            temperature=0.7,
            top_p=0.9,
            pad_token_id=generator.tokenizer.eos_token_id,
        )
        tail = out[0]["generated_text"][len(opener):].strip()
        if not tail:
            tail = reason
        return f"{opener} {tail}".strip()
    except Exception:
        return f"{opener} {reason}"
