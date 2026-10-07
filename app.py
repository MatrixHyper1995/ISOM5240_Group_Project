"""
Sephora Skin Concern Advisor — 主入口（薄壳）
Main entry (thin shell): page + flow orchestration. No business logic here.

流程 / Flow: 上传 → Analyze → 结果 → 推荐 → 产品 → 评论摘要 → 保存/反馈
UI 结构严格参照设计原稿v2.html（顶栏 / Hero / 01–06 分节 / 深色页脚）。
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
    render_topbar,
    render_hero,
    render_section,
    render_footer,
    render_photo_card,
    render_severity_bar,
    render_result,
    render_why_chain,
    render_recommendation,
    render_product_card,
    render_digest,
    tone_select,
    render_disclaimer,
    render_feedback,
)
from ui.card import render_summary_card

STYLES = ["Gentle", "Professional", "Concise", "Enthusiastic"]

st.set_page_config(page_title="SEPHORA · Skin Concern Advisor", page_icon="🪞", layout="centered")


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
        "saved": False,
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

    # 顶栏 + Hero
    render_topbar()
    render_hero()

    # 01 UPLOAD
    render_section("01 / UPLOAD", "Upload Your Selfie", "One clear photo. Front-facing, good light, no filters.")
    uploaded = st.file_uploader(
        "Choose Photo",
        type=config.ALLOWED_TYPES,
        label_visibility="collapsed",
    )
    if uploaded is not None and handle_upload(uploaded):
        st.rerun()

    # 02 ANALYZE
    render_section("02 / ANALYZE", "Analyze Your Photo", "You stay in control — analysis only runs when you click.")
    can_analyze = st.session_state.image is not None
    if can_analyze:
        filename = uploaded.name if uploaded is not None else "selfie.jpg"
        c_left, c_right = st.columns([3.2, 1.2], vertical_alignment="center")
        with c_left:
            render_photo_card(st.session_state.image, filename)
        with c_right:
            if st.button("Analyze", type="primary", disabled=not can_analyze):
                run_analysis()
    else:
        if st.button("Analyze", type="primary", disabled=True):
            run_analysis()

    # 03~06 结果 / Result → Recommendation → Products → Save/Feedback
    if st.session_state.severity_key is not None:
        key = st.session_state.severity_key

        # 03 RESULT
        render_section("03 / RESULT", "Your Skin Snapshot", "Cosmetic skin concern only. Not a medical diagnosis.")
        render_result(key, st.session_state.severity_label, st.session_state.confidence)
        render_severity_bar(key)
        render_disclaimer()

        products = get_products(key)
        st.session_state.products = products

        # 04 RECOMMENDATION
        render_section("04 / RECOMMENDATION", "Your Personalized Recommendation", "Pick a tone. We'll write the recommendation around your result.")
        render_why_chain(key, products)
        tone = tone_select(STYLES)
        if st.button("Generate recommendation"):
            run_recommendation(tone)
        if st.session_state.recommendation:
            render_recommendation(st.session_state.recommendation)

        # 05 MATCHED PRODUCTS
        render_section("05 / MATCHED PRODUCTS", "Your Skincare Picks", "Only verified-buyer reviews are shown. PRO / CON — no endless scrolling.")
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

        # 06 SAVE · SHARE · FEEDBACK
        render_section("06 / SAVE · SHARE · FEEDBACK", "Keep Your Routine", "No account needed. Your summary stays in this session.")
        st.markdown(
            '<div class="actions">'
            '<h3>Save your skincare summary</h3>'
            '<div class="sub">Download it, share it, or tell us if this was useful.</div>'
            '</div>',
            unsafe_allow_html=True,
        )
        # 三个按钮紧凑并排（原稿 .btn-row：flex gap 10px）
        c1, c2, c3 = st.columns(3)
        with c1:
            card = render_summary_card(
                key,
                st.session_state.severity_label,
                st.session_state.confidence,
                st.session_state.recommendation,
                products,
            )
            st.download_button(
                "Download Summary", card, file_name="skin_snapshot.png",
                mime="image/png", use_container_width=True,
            )
        with c2:
            if st.button("Share Routine", use_container_width=True):
                st.toast("Share this page's URL to share your routine.")
        with c3:
            if st.button("Save to This Session", use_container_width=True):
                st.session_state.saved = True
                st.toast("Saved to this session.")

        # 反馈：两个问题，回答后消失变感谢语（都答后居中一条）
        render_feedback()

    # 页脚
    render_footer()


if __name__ == "__main__":
    main()
