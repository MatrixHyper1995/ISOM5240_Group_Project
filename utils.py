"""
Sephora Skin Concern Advisor — 工具函数
Image helpers, mapping lookup, review loading.

参考 / Reference: Image Storyteller 的拆分经验 ——
纯图片工具（PIL）与数据加载（@st.cache_data）分开，映射查询集中在这里，业务改数据不动代码。
"""
import json
from pathlib import Path

import pandas as pd
import streamlit as st
from PIL import Image, ImageOps

import config


# ---------------------------------------------------------------------------
# 图片工具 / Image helpers (pure PIL)
# ---------------------------------------------------------------------------
def validate_size(uploaded) -> str | None:
    """校验文件大小（格式由上传白名单限制）。返回错误信息，合法则返回 None。"""
    if uploaded.size > config.MAX_UPLOAD_BYTES:
        return f"File is too large. Please upload an image under {config.MAX_UPLOAD_MB} MB."
    return None


def load_image(uploaded) -> Image.Image:
    """读取图片并统一为 RGB，应用 EXIF 旋转（避免手机照片横躺）。"""
    img = Image.open(uploaded)
    img = ImageOps.exif_transpose(img)
    return img.convert("RGB")


def resize_image(img: Image.Image, max_size: int = 1024) -> Image.Image:
    """按长边等比缩放，避免超大图占用内存（ViT pipeline 内部会自动 resize 到 224）。"""
    w, h = img.size
    if max(w, h) > max_size:
        scale = max_size / max(w, h)
        img = img.resize((int(w * scale), int(h * scale)), Image.LANCZOS)
    return img


# ---------------------------------------------------------------------------
# 数据文件加载（@st.cache_data，避免每次 rerun 重读）/ Data loading
# ---------------------------------------------------------------------------
@st.cache_data
def load_json(path: Path) -> dict:
    """加载 JSON 文件（缓存）。"""
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def load_bridge() -> dict:
    """加载桥映射表（等级 → 成分 → 产品）。"""
    return load_json(config.BRIDGE_PATH)


def load_openers() -> dict:
    """加载推荐文案开头句（风格 × 档位 × 变体）。"""
    return load_json(config.OPENERS_PATH)


def load_reviews():
    """加载评论样本 CSV（若存在）。列需含 product_name / review_text / verified_purchase。"""
    path = config.DATA_DIR / "reviews_sample.csv"
    if not path.exists():
        return None
    return pd.read_csv(path)


# ---------------------------------------------------------------------------
# 映射查询 / Mapping lookup
# ---------------------------------------------------------------------------
def get_severity_label(key: str) -> str:
    """档位 key → 消费者语言标签（"1" → "Mild"）。"""
    return load_bridge()["severity_labels"].get(key, "Mild")


def get_ingredients(key: str) -> list[str]:
    """档位 key → 成分列表。"""
    return load_bridge()["ingredient_map"].get(key, ["Niacinamide"])


def get_products(key: str) -> list[dict]:
    """档位 key → 产品列表。"""
    return load_bridge()["product_map"].get(key, [])


def get_opener(style: str, key: str, variant: int = 0) -> str:
    """风格 × 档位 → 开头句；缺省兜底 Mild 档。变体 [主, 变体] 轮换。"""
    openers = load_openers().get(style, {})
    variants = openers.get(key) or openers.get("1") or ["For your skin,"]
    return variants[variant % len(variants)]


def format_opener(opener: str, ingredient: str) -> str:
    """把开头句里的 {ingredient} 占位替换成实际成分（用 replace，避免 str.format 意外）。"""
    return opener.replace("{ingredient}", ingredient)
