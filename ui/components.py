"""
Sephora Skin Concern Advisor — UI 组件
Topbar, hero, section headers, severity bar, result, product card, digest, footer.

参考 / Reference: 设计原稿v2.html —— 每个 UI 区块一个函数，样式独立在 style.css，
改样式不动代码。
"""
import base64
import html
from io import BytesIO

import streamlit as st

import config
from utils import get_severity_desc, get_severity_label, get_ingredients, get_products


def inject_css() -> None:
    """注入 UI 样式（独立在 style.css，改样式不动代码）。"""
    css = config.CSS_PATH.read_text(encoding="utf-8")
    st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)


def render_topbar() -> None:
    """顶栏：SEPHORA* 黑底 + 金色底边。"""
    st.markdown(
        """
        <div class="topbar">
            <span class="wordmark">SEPHORA<span class="flame">*</span></span>
            <span class="sub">PERSONALIZED SKINCARE · SKIN ADVISOR</span>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_hero() -> None:
    """Hero：eyebrow + 衬线主标题 + 标语 + 红色分隔线。"""
    st.markdown(
        """
        <div class="hero">
            <div class="eyebrow">SKIN CONCERN ADVISOR</div>
            <h1>Find Your First Step to<br><span class="accent">Better Skin</span></h1>
            <p class="tag">Snap a selfie · Match your routine · Reviews already curated</p>
            <p class="tag-sub">Thousands of SKUs. We narrow it down to two or three — with verified buyer reviews already filtered.</p>
            <div class="rule"></div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_section(idx: str, title: str, hint: str) -> None:
    """区块标题：序号 + 衬线标题 + 提示。"""
    st.markdown(
        f"""
        <div class="sec">
            <div class="idx">{html.escape(idx)}</div>
            <h2>{html.escape(title)}</h2>
            <p class="hint">{html.escape(hint)}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_photo_card(image, filename: str) -> None:
    """上传后卡片内容：缩略图 + 文件名 + 状态（横向，供容器左列使用）。

    外层卡片边框/玻璃背景由 CSS `[data-testid="stHorizontalBlock"]:has(.photo-row)` 提供，本函数只渲染内部。
    """
    buf = BytesIO()
    image.save(buf, format="PNG")
    b64 = base64.b64encode(buf.getvalue()).decode()
    st.markdown(
        f"""
        <div class="photo-row">
            <img class="thumb" src="data:image/png;base64,{b64}" alt="" />
            <div class="meta">
                <div class="fname">{html.escape(filename)}</div>
                <div class="fstatus">Ready · No face detection error</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_footer() -> None:
    """页脚：黑底免责声明。"""
    st.markdown(
        """
        <div class="footer">
            <span class="flame">*</span> For skincare reference only. <span class="gold">Not a medical diagnosis.</span> For skin conditions or concerns, please consult a dermatologist.<br>
            Images are processed in memory and never stored or shared. This tool recommends only — it does not sell or diagnose.<br>
            SEPHORA<span class="flame">*</span> · Skin Concern Advisor
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_result(key: str, label: str, confidence: float) -> None:
    """渲染分析结果：一张玻璃卡片包住等级、描述、置信度、分段条、低置信提示与免责声明。"""
    desc = get_severity_desc(key)

    # 分段条（原样保留：range(4)、4 个 .seg-col 格子、点亮 level+1 格、标签 get_severity_label(str(i))）
    level = int(key) + 1
    seg_cols = ""
    for i in range(4):
        cls = "bar-cell on" if i < level else "bar-cell"
        seg_label = html.escape(get_severity_label(str(i)))
        seg_cols += (
            f'<div class="seg-col"><div class="{cls}"></div>'
            f'<span class="seg-label">{seg_label}</span></div>'
        )

    severity_row = f'<span class="severity-word">{html.escape(label)}</span>'
    if desc:
        severity_row += f'<span class="severity-desc">{html.escape(desc)}</span>'

    lowconf = ""
    if confidence < config.LOW_CONF_THRESHOLD:
        lowconf = (
            '<div class="lowconf">Low confidence — try another photo with better light, '
            'or consult a dermatologist.</div>'
        )

    st.markdown(
        f"""
        <div class="card glass">
          <div class="label">BREAKOUT CONCERN LEVEL</div>
          <div class="severity-row">{severity_row}</div>
          <div class="confidence">Confidence: <b>{confidence:.0%}</b></div>
          <div class="severity-bar">{seg_cols}</div>
          {lowconf}
          <div class="disclaimer">For skincare reference only · Not a medical diagnosis · See a dermatologist for persistent or severe concerns</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_why_chain(key: str, products: list[dict]) -> None:
    """「为什么这样推荐」链：等级 → 成分 → 产品。"""
    label = get_severity_label(key)
    ingredients = " · ".join(get_ingredients(key))
    product_names = " · ".join(p.get("name", "") for p in products[:2])
    st.markdown(
        f"""
        <div class="why-chain">
            <div class="k">WHY THIS RECOMMENDATION</div>
            <div class="chain">
                {html.escape(label)} breakout concern
                <span class="arrow">→</span> {html.escape(ingredients)}
                <span class="arrow">→</span> {html.escape(product_names)}
            </div>
            <div class="note">Ingredients commonly used in cosmetic skincare for {html.escape(label.lower())} breakout concerns.</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_recommendation(text: str) -> None:
    """推荐文案卡。"""
    st.markdown(f'<div class="reco-card">{html.escape(text)}</div>', unsafe_allow_html=True)


def render_product_card(product: dict) -> None:
    """产品卡：名称在上、品牌·功效在下、成分为标签 chips（对齐设计稿 .prod-card）。"""
    name = html.escape(product.get("name", ""))
    brand = html.escape(product.get("brand", ""))
    why = html.escape(product.get("why", ""))
    brand_line = brand + (f" · {why}" if why else "")
    ing_chips = "".join(
        f'<span class="ing-chip">{html.escape(i)}</span>'
        for i in product.get("ingredients", [])
    )
    st.markdown(
        f"""
        <div class="prod-card">
            <div class="prod-name">{name}</div>
            <div class="prod-brand">{brand_line}</div>
            <div class="ing">{ing_chips}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_digest(digest: dict) -> None:
    """Verified Buyer Digest：标题 + PRO/CON 药丸 + 行式 PRO+/CON−（对齐设计稿 .rv）。"""
    pro = digest.get("pro", [])
    con = digest.get("con", [])
    rows = ""
    for t in pro:
        rows += (
            f'<div class="row"><span class="mark pos">PRO +</span>'
            f'<span class="txt">{html.escape(t)}</span></div>'
        )
    for t in con:
        rows += (
            f'<div class="row"><span class="mark neg">CON −</span>'
            f'<span class="txt">{html.escape(t)}</span></div>'
        )
    st.markdown(
        f"""
        <div class="rv">
            <div class="rv-head">
                <span class="vb">VERIFIED BUYER DIGEST</span>
                <span class="pill">{len(pro)} PRO</span>
                <span class="pill">{len(con)} CON</span>
            </div>
            {rows}
        </div>
        """,
        unsafe_allow_html=True,
    )


def tone_select(styles: list[str], default: str = "Gentle"):
    """风格下拉（Tone）。"""
    idx = styles.index(default) if default in styles else 0
    return st.selectbox("RECOMMENDATION TONE", styles, index=idx)


def render_feedback() -> None:
    """反馈区：两个问题（推荐 / 评论摘要），回答后消失变感谢语；都答后居中一条。"""
    reco_done = st.session_state.get("feedback_reco") is not None
    digest_done = st.session_state.get("feedback_digest") is not None

    if reco_done and digest_done:
        st.markdown('<div class="feedback-thanks center">We appreciate your feedback</div>', unsafe_allow_html=True)
        return

    if reco_done:
        st.markdown('<div class="feedback-thanks">We appreciate your feedback</div>', unsafe_allow_html=True)
    else:
        st.markdown("**Was this recommendation useful?**")
        c1, c2 = st.columns(2)
        with c1:
            if st.button("Yes", key="reco_helpful"):
                st.session_state.feedback_reco = "helpful"
                st.rerun()
        with c2:
            if st.button("No", key="reco_not"):
                st.session_state.feedback_reco = "not_helpful"
                st.rerun()

    if digest_done:
        st.markdown('<div class="feedback-thanks">We appreciate your feedback</div>', unsafe_allow_html=True)
    else:
        st.markdown("**Was the review digest useful?**")
        c1, c2 = st.columns(2)
        with c1:
            if st.button("Yes", key="digest_helpful"):
                st.session_state.feedback_digest = "helpful"
                st.rerun()
        with c2:
            if st.button("No", key="digest_not"):
                st.session_state.feedback_digest = "not_helpful"
                st.rerun()
