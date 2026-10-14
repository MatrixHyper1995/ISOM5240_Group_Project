"""
Sephora Skin Concern Advisor — Review 模型（nlptown multilingual-BERT 评论 PRO/CON 分类）
nlptown BERT review classification (PRO / CON) + verified-buyer curation.
"""
import streamlit as st
from transformers import pipeline

import config
from utils import load_reviews, quantize_model


@st.cache_resource
def load_review(model_id: str):
    """加载并缓存文本分类模型（按 model_id 缓存）。"""
    if not config.ENABLE_QUANTIZATION:
        return pipeline("text-classification", model=model_id)
    from transformers import AutoModelForSequenceClassification, AutoTokenizer
    model = AutoModelForSequenceClassification.from_pretrained(model_id)
    model = quantize_model(model)
    return pipeline(
        "text-classification",
        model=model,
        tokenizer=AutoTokenizer.from_pretrained(model_id),
    )


def _normalize_label(raw_label: str) -> str:
    """归一化标签为 "PRO" / "CON"。

    兼容三个候选模型的输出格式：
      - SST-2（distilbert）→ POSITIVE / NEGATIVE
      - RoBERTa（twitter）→ positive / negative / neutral
      - multilingual-BERT（nlptown）→ 1 star ~ 5 stars
    中性/3 星保守归 CON（PRO/CON 二分类不设中性档）。
    """
    label = raw_label.strip().upper()
    if label in ("PRO", "POSITIVE", "4 STARS", "5 STARS"):
        return "PRO"
    if label in ("CON", "NEGATIVE", "NEUTRAL", "1 STAR", "2 STARS", "3 STARS"):
        return "CON"
    return "PRO"  # 兜底


def predict_review(text: str, model_id: str | None = None) -> str:
    """单条评论分类 → "PRO" / "CON"。model_id 缺省用 config.REVIEW_MODEL。"""
    model_id = model_id or config.REVIEW_MODEL
    return _normalize_label(load_review(model_id)(text)[0]["label"])


def curate_reviews(reviews: list[str], pro_top_k: int = None, con_top_k: int = None, model_id: str | None = None) -> dict:
    """批处理评论 → 按置信度取 top PRO/CON 摘要。Batch classify → top PRO/CON digests."""
    pro_top_k = pro_top_k or config.PRO_TOP_K
    con_top_k = con_top_k or config.CON_TOP_K
    model_id = model_id or config.REVIEW_MODEL
    if not reviews:
        return {"pro": [], "con": []}
    results = load_review(model_id)(reviews, batch_size=16)
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


def load_and_curate(product_names: list[str], model_id: str | None = None) -> dict:
    """加载评论 CSV → 过滤验证买家 + 目标产品 → 批处理分类 → PRO/CON 摘要。

    汇总版（所有目标产品合并成一份摘要），保留向后兼容。
    产品卡内嵌摘要请用 curate_per_product（按产品分发）。
    """
    reviews = load_reviews()
    if reviews is None or reviews.empty:
        return {"pro": [], "con": []}
    df = reviews
    if "verified_purchase" in df.columns:
        df = df[df["verified_purchase"] == True]
    if "product_name" in df.columns and product_names:
        df = df[df["product_name"].isin(product_names)]
    texts = df["review_text"].astype(str).tolist()[:50]  # 限制条数，避免 CPU 打爆
    return curate_reviews(texts, model_id=model_id)


@st.cache_data(show_spinner=False)
def _curate_per_product_cached(product_names: tuple, model_id: str) -> dict[str, dict]:
    """按产品分发的 PRO/CON 摘要（结果按 (product_names, model_id) 缓存）。

    同一档位 → 同一批产品 → 同一份摘要，第二次 Analyze 直接命中缓存，
    省掉最重的 review 批量推理。
    """
    result = {name: {"pro": [], "con": []} for name in product_names}
    reviews = load_reviews()
    if reviews is None or reviews.empty:
        return result
    df = reviews
    if "verified_purchase" in df.columns:
        df = df[df["verified_purchase"] == True]
    if "product_name" not in df.columns or not product_names:
        return result
    df = df[df["product_name"].isin(product_names)]

    # 每个产品最多 50 条，合并后一次批量推理（避免逐产品反复加载模型）
    texts_by_name = {}
    for name in product_names:
        texts = df[df["product_name"] == name]["review_text"].astype(str).tolist()[:50]
        if texts:
            texts_by_name[name] = texts
    if not texts_by_name:
        return result

    flat_texts, flat_names = [], []
    for name, texts in texts_by_name.items():
        for t in texts:
            flat_texts.append(t)
            flat_names.append(name)

    results = load_review(model_id)(flat_texts, batch_size=16)

    pro_by_name = {name: [] for name in product_names}
    con_by_name = {name: [] for name in product_names}
    for name, text, r in zip(flat_names, flat_texts, results):
        label = _normalize_label(r["label"])
        (pro_by_name[name] if label == "PRO" else con_by_name[name]).append((text, float(r["score"])))

    for name in product_names:
        pro_by_name[name].sort(key=lambda x: -x[1])
        con_by_name[name].sort(key=lambda x: -x[1])
        result[name] = {
            "pro": [t for t, _ in pro_by_name[name][:config.PRO_TOP_K]],
            "con": [t for t, _ in con_by_name[name][:config.CON_TOP_K]],
        }
    return result


def curate_per_product(product_names: list[str], model_id: str | None = None) -> dict[str, dict]:
    """薄壳：解析 model_id，转 tuple 作为缓存 key，调用缓存版。"""
    model_id = model_id or config.REVIEW_MODEL
    return _curate_per_product_cached(tuple(product_names), model_id)
