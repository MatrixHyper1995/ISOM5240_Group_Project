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
    load_ui_spec,
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
    render_result,
    render_why_chain,
    render_recommendation,
    render_product_card,
    render_digest,
    tone_select,
    render_feedback,
    render_actions,
    render_sidebar,
)
from ui.card import render_summary_card

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


def run_recommendation(tone: str, model_id: str | None = None) -> None:
    """Step 04 Generate：文案续写；成功后释放模型（同轮渲染，无 rerun）。"""
    st.session_state.recommendation = generate(tone, st.session_state.severity_key, model_id=model_id)
    release_generator()


# ---------------------------------------------------------------------------
# 主流程 / Main
# ---------------------------------------------------------------------------
def main() -> None:
    inject_css()
    init_state()

    # UI 参数表（单一事实来源）
    spec = load_ui_spec()
    COPY = spec["copy"]
    LAYOUT = spec["layout"]
    CELLS = spec["severity_bar"]["cells"]
    SEC = COPY["sections"]
    BTN = COPY["buttons"]
    TONES = COPY["tones"]

    # 演示模式：st.secrets 脚本控制（默认关），开启时侧栏出三个模型下拉（答辩展示用）
    demo_mode = st.secrets.get("demo_mode", False)
    model_sel = render_sidebar(demo_mode)  # None 或 {"vision","review","gen"} 模型 id
    vision_model = model_sel["vision"] if model_sel else config.VISION_MODEL
    review_model = model_sel["review"] if model_sel else config.REVIEW_MODEL
    gen_model = model_sel["gen"] if model_sel else config.GEN_MODEL

    # 顶栏 + Hero
    render_topbar()
    render_hero()

    # 01 UPLOAD
    render_section(SEC["01"]["idx"], SEC["01"]["title"], SEC["01"]["hint"])
    uploaded = st.file_uploader(
        BTN["choose_photo"],
        type=config.ALLOWED_TYPES,
        label_visibility="collapsed",
    )
    if uploaded is not None and handle_upload(uploaded):
        st.rerun()

    # 02 ANALYZE
    render_section(SEC["02"]["idx"], SEC["02"]["title"], SEC["02"]["hint"])
    can_analyze = st.session_state.image is not None
    analyze_clicked = False
    if can_analyze:
        filename = uploaded.name if uploaded is not None else "selfie.jpg"
        c_left, c_right = st.columns(LAYOUT["photo_cols"], vertical_alignment="center")
        with c_left:
            render_photo_card(st.session_state.image, filename)
        with c_right:
            analyze_clicked = st.button(BTN["analyze"], type="primary", disabled=False)
    else:
        analyze_clicked = st.button(BTN["analyze"], type="primary", disabled=True)

    # 分析进度：整张卡片下方、占满整行（同轮完成，无 st.rerun，避免页面回顶）
    if analyze_clicked and can_analyze:
        with st.spinner(COPY["spinner_analyze"]):
            try:
                key, label, conf = predict_severity(st.session_state.image, model_id=vision_model)
                st.session_state.severity_key = key
                st.session_state.severity_label = label
                st.session_state.confidence = conf
            except Exception as e:
                st.error(COPY["error_analysis"].format(error=e))
            else:
                release_vision()

    # 03~06 结果 / Result → Recommendation → Products → Save/Feedback
    if st.session_state.severity_key is not None:
        key = st.session_state.severity_key

        # 03 RESULT
        render_section(SEC["03"]["idx"], SEC["03"]["title"], SEC["03"]["hint"])
        render_result(key, st.session_state.severity_label, st.session_state.confidence)

        products = get_products(key)
        st.session_state.products = products

        # 04 RECOMMENDATION
        render_section(SEC["04"]["idx"], SEC["04"]["title"], SEC["04"]["hint"])
        with st.container(border=True):
            render_why_chain(key, products)
            tone = tone_select(TONES)
            if st.button(BTN["generate"], type="primary"):
                run_recommendation(tone, model_id=gen_model)
            if st.session_state.recommendation:
                render_recommendation(st.session_state.recommendation)

        # 05 MATCHED PRODUCTS
        render_section(SEC["05"]["idx"], SEC["05"]["title"], SEC["05"]["hint"])
        for product in products:
            render_product_card(product)

        # 评论摘要（reviews_sample.csv 生成后自动接入；懒加载 + 缓存，只跑一次）
        if st.session_state.digest is None and products:
            try:
                st.session_state.digest = load_and_curate([p["name"] for p in products], model_id=review_model)
            except Exception:
                st.session_state.digest = {"pro": [], "con": []}
        if st.session_state.digest and (st.session_state.digest["pro"] or st.session_state.digest["con"]):
            render_digest(st.session_state.digest)

        # 06 SAVE · SHARE · FEEDBACK
        render_section(SEC["06"]["idx"], SEC["06"]["title"], SEC["06"]["hint"])
        card = render_summary_card(
            key,
            st.session_state.severity_label,
            st.session_state.confidence,
            st.session_state.recommendation,
            products,
            cells=CELLS,
        )
        render_actions(card)  # 手搓：<a download> + 分享/保存按钮 + 内联提示

        # 反馈：两个问题，手搓 HTML 按钮 + JS 锁定（不依赖 st.button / session_state）
        render_feedback()

    # 页脚
    render_footer()


if __name__ == "__main__":
    main()
