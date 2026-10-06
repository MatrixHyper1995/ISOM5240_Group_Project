"""
Sephora Skin Concern Advisor — Review 模型（DistilBERT 评论 PRO/CON 分类）
DistilBERT review classification (PRO / CON) + verified-buyer curation.
"""
import streamlit as st
from transformers import pipeline

import config
from utils import load_reviews


@st.cache_resource
def load_review():
    """加载并缓存 DistilBERT 文本分类模型。"""
    return pipeline("text-classification", model=config.REVIEW_MODEL)


def _normalize_label(raw_label: str) -> str:
    """归一化标签为 "PRO" / "CON"（兼容 LABEL_0/1、POSITIVE/NEGATIVE、PRO/CON）。"""
    label = raw_label.upper()
    if label in ("PRO", "POSITIVE", "LABEL_0"):
        return "PRO"
    if label in ("CON", "NEGATIVE", "LABEL_1"):
        return "CON"
    return "PRO"  # 兜底


def predict_review(text: str) -> str:
    """单条评论分类 → "PRO" / "CON"。"""
    return _normalize_label(load_review()(text)[0]["label"])


def curate_reviews(reviews: list[str], pro_top_k: int = None, con_top_k: int = None) -> dict:
    """批处理评论 → 按置信度取 top PRO/CON 摘要。Batch classify → top PRO/CON digests."""
    pro_top_k = pro_top_k or config.PRO_TOP_K
    con_top_k = con_top_k or config.CON_TOP_K
    if not reviews:
        return {"pro": [], "con": []}
    results = load_review()(reviews, batch_size=16)
    pro, con = [], []
    for text, r in zip(reviews, results):
        label = _normalize_label(r["label"])
        (pro if label == "PRO" else con).append((text, float(r["score"])))
    pro.sort(key=lambda x: -x[1])
    con.sort(key=lambda x: -x[1])
    return {
        "pro": [t for t, _ in pro[:pro_top_k]],
        "con": [t for t, _ in con[:con_top_k]],
    }


def load_and_curate(product_names: list[str]) -> dict:
    """加载评论 CSV → 过滤验证买家 + 目标产品 → 批处理分类 → PRO/CON 摘要。"""
    reviews = load_reviews()
    if reviews is None or reviews.empty:
        return {"pro": [], "con": []}
    df = reviews
    if "verified_purchase" in df.columns:
        df = df[df["verified_purchase"] == True]
    if "product_name" in df.columns and product_names:
        df = df[df["product_name"].isin(product_names)]
    texts = df["review_text"].astype(str).tolist()[:50]  # 限制条数，避免 CPU 打爆
    return curate_reviews(texts)
