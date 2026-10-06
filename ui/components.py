"""
Sephora Skin Concern Advisor — UI 组件
Severity bar, result, product card, Verified Buyer Digest, tone dropdown.

参考 / Reference: Image Storyteller 的 render_* 组件化 + style.css 抽离经验 ——
每个 UI 区块一个函数，样式独立在 style.css，改样式不动代码。
"""
import html

import streamlit as st

import config


def inject_css() -> None:
    """注入 UI 样式（独立在 style.css，改样式不动代码）。"""
    css = config.CSS_PATH.read_text(encoding="utf-8")
    st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)


def render_severity_bar(key: str) -> None:
    """单色分段条（色弱友好：明暗不靠色，点亮 level 格）。"""
    level = int(key) + 1
    cells = "".join(
        '<div class="bar-cell on"></div>' if i < level else '<div class="bar-cell"></div>'
        for i in range(4)
    )
    st.markdown(f'<div class="severity-bar">{cells}</div>', unsafe_allow_html=True)


def render_result(label: str, confidence: float) -> None:
    """渲染分析结果：等级（大字号 Georgia）+ 置信度 + 低置信提示。"""
    st.markdown(f'<div class="result-label">{html.escape(label)}</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="confidence">Confidence: {confidence:.0%}</div>', unsafe_allow_html=True)
    if confidence < config.LOW_CONF_THRESHOLD:
        st.warning("Low confidence — try another photo with better light, or consult a dermatologist.")


def render_recommendation(text: str) -> None:
    """推荐文案卡。"""
    st.markdown(f'<div class="reco-card">{html.escape(text)}</div>', unsafe_allow_html=True)


def render_product_card(product: dict) -> None:
    """产品卡：品牌 + 名称 + 成分标签 + why。"""
    brand = html.escape(product.get("brand", ""))
    name = html.escape(product.get("name", ""))
    ingredients = " · ".join(html.escape(i) for i in product.get("ingredients", []))
    why = html.escape(product.get("why", ""))
    st.markdown(
        f"""
        <div class="product-card">
            <div class="p-brand">{brand}</div>
            <div class="p-name">{name}</div>
            <div class="p-ing">{ingredients}</div>
            <div class="p-why">{why}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_digest(digest: dict) -> None:
    """Verified Buyer Digest：PRO+ / CON− 符号（色弱友好，不碰红绿）。"""
    pro = digest.get("pro", [])
    con = digest.get("con", [])
    st.markdown(
        f'<div class="digest-head">Verified Buyer Digest · {len(pro)} PRO+ · {len(con)} CON−</div>',
        unsafe_allow_html=True,
    )
    for t in pro:
        st.markdown(f'<div class="digest pro">{html.escape(t)}</div>', unsafe_allow_html=True)
    for t in con:
        st.markdown(f'<div class="digest con">{html.escape(t)}</div>', unsafe_allow_html=True)


def tone_select(styles: list[str], default: str = "Gentle"):
    """风格下拉（Tone）；filter_mode=None 禁用打字过滤。"""
    idx = styles.index(default) if default in styles else 0
    return st.selectbox("Tone", styles, index=idx, filter_mode=None)


def render_disclaimer() -> None:
    """免责声明（固定挂）。For skincare reference only · Not a medical diagnosis."""
    st.markdown(
        '<div class="disclaimer">For skincare reference only · Not a medical diagnosis · '
        'See a dermatologist for persistent or severe concerns</div>',
        unsafe_allow_html=True,
    )


def render_feedback() -> None:
    """反馈区：两个问题（推荐 / 评论摘要），回答后消失变感谢语；都答后居中一条。"""
    reco_done = st.session_state.get("feedback_reco") is not None
    digest_done = st.session_state.get("feedback_digest") is not None

    # 两个都答完 → 居中一条感谢语
    if reco_done and digest_done:
        st.markdown('<div class="feedback-thanks center">We appreciate your feedback</div>', unsafe_allow_html=True)
        return

    # 推荐问题
    if reco_done:
        st.markdown('<div class="feedback-thanks">We appreciate your feedback</div>', unsafe_allow_html=True)
    else:
        st.markdown("**Was this recommendation useful?**")
        c1, c2 = st.columns(2)
        with c1:
            if st.button("👍 Helpful", key="reco_helpful"):
                st.session_state.feedback_reco = "helpful"
                st.rerun()
        with c2:
            if st.button("👎 Not helpful", key="reco_not"):
                st.session_state.feedback_reco = "not_helpful"
                st.rerun()

    # 评论摘要问题
    if digest_done:
        st.markdown('<div class="feedback-thanks">We appreciate your feedback</div>', unsafe_allow_html=True)
    else:
        st.markdown("**Was the review digest useful?**")
        c1, c2 = st.columns(2)
        with c1:
            if st.button("👍 Helpful", key="digest_helpful"):
                st.session_state.feedback_digest = "helpful"
                st.rerun()
        with c2:
            if st.button("👎 Not helpful", key="digest_not"):
                st.session_state.feedback_digest = "not_helpful"
                st.rerun()
