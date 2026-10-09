"""
Sephora Skin Concern Advisor — Vision 模型（ViT 痘痘严重度分类）
ViT acne severity classification (0–3).

参考 / Reference: Image Storyteller 的「用一杀一」经验 ——
分析完就释放模型，避免与下游 text-gen / review 叠加占用内存（Streamlit Cloud 小内存）。
"""
import gc

import streamlit as st
from PIL import Image
from transformers import pipeline

import config
from utils import load_bridge


@st.cache_resource
def load_vision(model_id: str):
    """加载并缓存 ViT 图像分类模型（按 model_id 缓存，切模型不重复加载）。"""
    return pipeline("image-classification", model=model_id)


def release_vision() -> None:
    """释放 Vision 模型缓存，腾出内存（给下游 text-gen / review 让位）。"""
    load_vision.clear()
    gc.collect()


def _normalize_key(raw_label: str) -> str:
    """把模型输出标签归一化成 "0"~"3"。Normalize model label to key "0"–"3"."""
    severity_labels = load_bridge()["severity_labels"]
    label = raw_label
    if label.startswith("LABEL_"):
        label = label[len("LABEL_"):]       # "LABEL_3" → "3"
    if label in severity_labels:
        return label                        # "3" / "0" 直接命中
    for k, v in severity_labels.items():    # "Moderate" → "2"
        if v.lower() == label.lower():
            return k
    raise ValueError(
        f"Unrecognized severity label: {raw_label!r}. "
        "This vision candidate may not be fine-tuned for acne severity yet."
    )


def predict_severity(image: Image.Image, model_id: str | None = None) -> tuple[str, str, float]:
    """分类痘痘严重度，返回 (severity_key, label, confidence)。model_id 缺省用 config.VISION_MODEL。"""
    model_id = model_id or config.VISION_MODEL
    result = load_vision(model_id)(image, top_k=1)[0]
    key = _normalize_key(result["label"])
    label = load_bridge()["severity_labels"].get(key, "Mild")
    return key, label, float(result["score"])
