"""
Sephora Skin Concern Advisor — 主入口（薄壳）
Main entry (thin shell): page + flow orchestration. No business logic here.

参考 / Reference: Image Storyteller 的 main() 编排经验 ——
app.py 只编排流程，具体逻辑在 config / data / models / ui / utils 各模块。

流程 / Flow: 上传 → Analyze → 结果 → 推荐 → 产品 → 评论摘要 → 保存/反馈
"""
import streamlit as st

import config
from utils import (
    load_image,
    validate_size,
    get_products,
)
from models.vision import predict_severity, release_vision
from models.generator import generate, release_generator
from models.review import load_and_curate
from ui.components import (
    inject_css,
    render_severity_bar,
    render_result,
    render_recommendation,
    render_product_card,
    render_digest,
    tone_select,
    render_disclaimer,
    render_feedback,
)
from ui.card import render_summary_card

STYLES = ["Gentle", "Professional", "Concise", "Enthusiastic"]

st.set_page_config(page_title="Sephora Skin Concern Advisor", page_icon="🪞", layout="centered")


# ---------------------------------------------------------------------------
# 会话状态 / Session state
# ---------------------------------------------------------------------------
def init_state() -> None:
    defaults = {
        "image": None,
        "severity_key": None,
        "severity_label": None,
        "confidence": None,
        "recommendation": None,
        "products": None,
        "digest": None,
        "file_id": None,
        "feedback_reco": None,
        "feedback_digest": None,
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def reset_results() -> None:
    """换图后重置旧结果。"""
    for key in ("severity_key", "severity_label", "confidence", "recommendation", "products", "digest", "feedback_reco", "feedback_digest"):
        st.session_state[key] = None


# ---------------------------------------------------------------------------
# 流程编排 / Flow orchestration
# ---------------------------------------------------------------------------
def handle_upload(uploaded) -> bool:
    """处理上传：新图则加载并重置旧结果。返回是否发生换图。"""
    file_id = (uploaded.name, uploaded.size)
    if st.session_state.file_id == file_id:
        return False
    st.session_state.file_id = file_id
    error = validate_size(uploaded)
    if error:
        st.error(error)
        return False
    st.session_state.image = load_image(uploaded)
    reset_results()
    return True


def run_analysis() -> None:
    """Step 02 Analyze：ViT 分类 → 结果；成功后释放模型（用一杀一）。"""
    with st.status("Analyzing cosmetic skin concerns...", expanded=False) as status:
        try:
            key, label, conf = predict_severity(st.session_state.image)
            st.session_state.severity_key = key
            st.session_state.severity_label = label
            st.session_state.confidence = conf
            status.update(label="✅ Analysis complete", state="complete", expanded=False)
        except Exception as e:
            status.update(label="Analysis failed", state="error", expanded=True)
            st.error(f"Analysis failed: {e}")
        else:
            release_vision()
            st.rerun()


def run_recommendation(tone: str) -> None:
    """Step 04 Generate：文案续写；成功后释放模型。"""
    st.session_state.recommendation = generate(tone, st.session_state.severity_key)
    release_generator()
    st.rerun()


# ---------------------------------------------------------------------------
# 主流程 / Main
# ---------------------------------------------------------------------------
def main() -> None:
    inject_css()
    init_state()

    # 0. Hero
    st.title("🪞 Skin Concern Advisor")
    st.caption("Snap a selfie · Match your routine · Reviews already curated")

    # 1. 上传 / Upload
    uploaded = st.file_uploader(
        "Choose Photo",
        type=config.ALLOWED_TYPES,
        help=f"JPG or PNG · Max {config.MAX_UPLOAD_MB} MB · Front-facing, good light",
    )
    if uploaded is not None and handle_upload(uploaded):
        st.rerun()

    # 2. Analyze 按钮 / Analyze button
    can_analyze = st.session_state.image is not None
    if st.button("Analyze", type="primary", disabled=not can_analyze):
        run_analysis()

    # 3~6. 结果 / Result → Recommendation → Products → Digest → Save/Feedback
    if st.session_state.severity_key is not None:
        render_result(st.session_state.severity_label, st.session_state.confidence)
        render_severity_bar(st.session_state.severity_key)
        render_disclaimer()

        products = get_products(st.session_state.severity_key)
        st.session_state.products = products

        # 4. 推荐 / Recommendation
        st.subheader("Your match")
        tone = tone_select(STYLES)
        if st.button("Generate recommendation"):
            run_recommendation(tone)
        if st.session_state.recommendation:
            render_recommendation(st.session_state.recommendation)

        # 5. 产品卡片 + 评论摘要 / Product cards + Verified Buyer Digest
        for product in products:
            render_product_card(product)

        # 评论摘要（reviews_sample.csv 生成后自动接入；懒加载 + 缓存，只跑一次）
        if st.session_state.digest is None and products:
            try:
                st.session_state.digest = load_and_curate([p["name"] for p in products])
            except Exception:
                st.session_state.digest = {"pro": [], "con": []}
        if st.session_state.digest and (st.session_state.digest["pro"] or st.session_state.digest["con"]):
            render_digest(st.session_state.digest)

        # 6. 保存 / 分享 / 反馈 / Save / Share / Feedback
        c1, c2 = st.columns(2)
        with c1:
            card = render_summary_card(
                st.session_state.severity_key,
                st.session_state.severity_label,
                st.session_state.confidence,
                st.session_state.recommendation,
                products,
            )
            st.download_button("💾 Save card", card, file_name="skin_snapshot.png", mime="image/png")
        with c2:
            st.button("📤 Share")

        # 反馈：两个问题，回答后消失变感谢语（都答后居中一条）
        render_feedback()

    # 页脚 / Footer
    render_disclaimer()


if __name__ == "__main__":
    main()
