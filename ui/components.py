"""
Sephora Skin Concern Advisor — UI 组件
Topbar, hero, section headers, severity bar, result, product card, digest, footer.

参考 / Reference: 设计原稿v2.html —— 每个 UI 区块一个函数，样式独立在 style.css，
改样式不动代码。

深度 2 改造：所有 CSS 类名 / 分段条格数 / 文案从 data/ui_spec.json 读，
类名单一事实来源，style.css 与此表对齐，改表不动代码。
"""
import base64
import html
from io import BytesIO

import streamlit as st

import config
from utils import (
    get_severity_desc,
    get_severity_label,
    get_ingredients,
    load_ui_spec,
)


def _css() -> dict:
    """UI 类名表（ui_spec.json）。"""
    return load_ui_spec()["css"]


def _copy() -> dict:
    """UI 文案表（ui_spec.json）。"""
    return load_ui_spec()["copy"]


def _cells() -> int:
    """分段条格数（ui_spec.json）。"""
    return load_ui_spec()["severity_bar"]["cells"]


def _layout() -> dict:
    """布局参数（ui_spec.json）。"""
    return load_ui_spec()["layout"]


def inject_css() -> None:
    """注入 UI 样式：静态 style.css + 动态 content 文案（从 ui_spec.json 读）。"""
    css = config.CSS_PATH.read_text(encoding="utf-8")
    spec = load_ui_spec()
    copy = spec["copy"]
    up = copy["upload"]
    btn = copy["buttons"]

    # 上传区 ::before/::after 的 content 文案从表读（style.css 已删掉这 4 条，改表不动 CSS）
    dyn_css = f"""
[data-testid="stFileUploaderDropzoneInstructions"]::before {{
    content: "{up['primary']}";
    display: block;
    width: 100%;
    text-align: center;
    font-size: 16px;
    color: var(--ink);
    line-height: 1.5;
}}
[data-testid="stFileUploaderDropzoneInstructions"]::after {{
    content: "{up['secondary']}";
    display: block;
    width: 100%;
    text-align: center;
    font-size: 13px;
    color: var(--muted);
    margin-top: 4px;
}}
[data-testid="stFileUploaderDropzone"]::after {{
    content: "{up['privacy']}";
    font-size: 12.5px;
    color: var(--muted-strong);
    letter-spacing: .02em;
    margin-top: 16px;
}}
[data-testid="stFileUploaderDropzone"] button::after {{
    content: "{btn['choose_photo']}";
    font-size: 14px;
    font-weight: 600;
    letter-spacing: .1em;
}}
"""
    st.markdown(f"<style>{css}\n{dyn_css}</style>", unsafe_allow_html=True)


def render_topbar() -> None:
    """顶栏：SEPHORA* 黑底 + 金色底边。"""
    C = _css()
    st.markdown(
        f"""
        <div class="{C['topbar']}">
            <span class="{C['wordmark']}">SEPHORA<span class="{C['flame']}">*</span></span>
            <span class="{C['topbar_sub']}">PERSONALIZED SKINCARE · SKIN ADVISOR</span>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_hero() -> None:
    """Hero：eyebrow + 衬线主标题 + 标语 + 红色分隔线。"""
    C = _css()
    st.markdown(
        f"""
        <div class="{C['hero']}">
            <div class="{C['eyebrow']}">SKIN CONCERN ADVISOR</div>
            <h1>Find Your First Step to<br><span class="{C['accent']}">Better Skin</span></h1>
            <p class="{C['tag']}">Snap a selfie · Match your routine · Reviews already curated</p>
            <p class="{C['tag_sub']}">Thousands of SKUs. We narrow it down to two or three — with verified buyer reviews already filtered.</p>
            <div class="{C['rule']}"></div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_section(idx: str, title: str, hint: str) -> None:
    """区块标题：序号 + 衬线标题 + 提示。"""
    C = _css()
    st.markdown(
        f"""
        <div class="{C['sec']}">
            <div class="{C['idx']}">{html.escape(idx)}</div>
            <h2>{html.escape(title)}</h2>
            <p class="{C['hint']}">{html.escape(hint)}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_photo_card(image, filename: str) -> None:
    """上传后卡片内容：缩略图 + 文件名 + 状态（横向，供容器左列使用）。

    外层卡片边框/玻璃背景由 CSS `[data-testid="stHorizontalBlock"]:has(.photo-row)` 提供，本函数只渲染内部。
    """
    C = _css()
    buf = BytesIO()
    image.save(buf, format="PNG")
    b64 = base64.b64encode(buf.getvalue()).decode()
    st.markdown(
        f"""
        <div class="{C['photo_row']}">
            <img class="{C['thumb']}" src="data:image/png;base64,{b64}" alt="" />
            <div class="{C['meta']}">
                <div class="{C['fname']}">{html.escape(filename)}</div>
                <div class="{C['fstatus']}">Ready · No face detection error</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_footer() -> None:
    """页脚：黑底免责声明。"""
    C = _css()
    st.markdown(
        f"""
        <div class="{C['footer']}">
            <span class="{C['footer_flame']}">*</span> For skincare reference only. <span class="{C['footer_gold']}">Not a medical diagnosis.</span> For skin conditions or concerns, please consult a dermatologist.<br>
            Images are processed in memory and never stored or shared. This tool recommends only — it does not sell or diagnose.<br>
            SEPHORA<span class="{C['footer_flame']}">*</span> · Skin Concern Advisor
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_result(key: str, label: str, confidence: float) -> None:
    """渲染分析结果：一张玻璃卡片包住等级、描述、置信度、分段条、低置信提示与免责声明。"""
    C = _css()
    desc = get_severity_desc(key)

    # 分段条：格数、点亮、标签均从 ui_spec / bridge_mapping 读
    level = int(key) + 1
    cells = _cells()
    seg_cols = ""
    for i in range(cells):
        cls = C["bar_cell_on"] if i < level else C["bar_cell"]
        seg_label = html.escape(get_severity_label(str(i)))
        seg_cols += (
            f'<div class="{C["seg_col"]}"><div class="{cls}"></div>'
            f'<span class="{C["seg_label"]}">{seg_label}</span></div>'
        )

    severity_row = f'<span class="{C["severity_word"]}">{html.escape(label)}</span>'
    if desc:
        severity_row += f'<span class="{C["severity_desc"]}">{html.escape(desc)}</span>'

    lowconf = ""
    if confidence < config.LOW_CONF_THRESHOLD:
        lowconf = (
            f'<div class="{C["lowconf"]}">Low confidence — try another photo with better light, '
            'or consult a dermatologist.</div>'
        )

    st.markdown(
        f"""
        <div class="{C['card_glass']}">
          <div class="{C['label']}">BREAKOUT CONCERN LEVEL</div>
          <div class="{C['severity_row']}">{severity_row}</div>
          <div class="{C['confidence']}">Confidence: <b>{confidence:.0%}</b></div>
          <div class="{C['severity_bar']}">{seg_cols}</div>
          {lowconf}
          <div class="{C['disclaimer']}">For skincare reference only · Not a medical diagnosis · See a dermatologist for persistent or severe concerns</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_why_chain(key: str, products: list[dict]) -> None:
    """「为什么这样推荐」链：等级 → 成分 → 产品。"""
    C = _css()
    label = get_severity_label(key)
    ingredients = " · ".join(get_ingredients(key))
    product_names = " · ".join(p.get("short", p.get("name", "")) for p in products[:2])
    st.markdown(
        f"""
        <div class="{C['why_chain']}">
            <div class="{C['why_k']}">WHY THIS RECOMMENDATION</div>
            <div class="{C['chain']}">
                {html.escape(label)} breakout concern
                <span class="{C['arrow']}">→</span> {html.escape(ingredients)}
                <span class="{C['arrow']}">→</span> {html.escape(product_names)}
            </div>
            <div class="{C['note']}">Ingredients commonly used in cosmetic skincare for {html.escape(label.lower())} breakout concerns.</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_recommendation(text: str) -> None:
    """推荐文案卡。"""
    C = _css()
    st.markdown(f'<div class="{C["reco_card"]}">{html.escape(text)}</div>', unsafe_allow_html=True)


def _digest_html(digest: dict | None) -> str:
    """生成 Verified Buyer Digest 的 HTML（内嵌进产品卡）。无摘要则返回空串。"""
    C = _css()
    if not digest:
        return ""
    pro = digest.get("pro", [])
    con = digest.get("con", [])
    if not pro and not con:
        return ""
    rows = ""
    for t in pro:
        rows += (
            f'<div class="{C["row"]}"><span class="{C["mark_pos"]}">PRO +</span>'
            f'<span class="{C["txt"]}">{html.escape(t)}</span></div>'
        )
    for t in con:
        rows += (
            f'<div class="{C["row"]}"><span class="{C["mark_neg"]}">CON −</span>'
            f'<span class="{C["txt"]}">{html.escape(t)}</span></div>'
        )
    return (
        f'<div class="{C["rv"]}">'
        f'<div class="{C["rv_head"]}">'
        f'<span class="{C["vb"]}">VERIFIED BUYER DIGEST</span>'
        f'<span class="{C["pill"]}">{len(pro)} PRO</span>'
        f'<span class="{C["pill"]}">{len(con)} CON</span>'
        f'</div>{rows}</div>'
    )


def render_product_card(product: dict, digest: dict | None = None) -> None:
    """产品卡：名称 + 品牌·肤质标签·功效 + 成分/功效 chips + 内嵌 Verified Buyer Digest。"""
    C = _css()
    name = html.escape(product.get("name", ""))
    brand = html.escape(product.get("brand", ""))
    why = html.escape(product.get("why", ""))
    concern = html.escape(product.get("concern", ""))
    # 品牌行：品牌 · 肤质标签 · 功效（三段，对齐设计稿 .prod-brand）
    brand_parts = [p for p in (brand, concern, why) if p]
    brand_line = " · ".join(brand_parts)
    # 成分 + 功效 tags（chips）
    ing_items = list(product.get("ingredients", [])) + list(product.get("tags", []))
    ing_chips = "".join(
        f'<span class="{C["ing_chip"]}">{html.escape(i)}</span>'
        for i in ing_items
    )
    st.markdown(
        f"""
        <div class="{C['prod_card']}">
            <div class="{C['prod_name']}">{name}</div>
            <div class="{C['prod_brand']}">{brand_line}</div>
            <div class="{C['ing']}">{ing_chips}</div>
            {_digest_html(digest)}
        </div>
        """,
        unsafe_allow_html=True,
    )


def tone_select(styles: list[str], default: str | None = None):
    """风格下拉（Tone）。"""
    if default is None:
        default = _copy().get("default_tone", "Gentle")
    idx = styles.index(default) if default in styles else 0
    return st.selectbox("RECOMMENDATION TONE", styles, index=idx)


def render_sidebar(demo_mode: bool) -> dict | None:
    """演示模式 sidebar：三个模型下拉（Vision/Review/Gen 各 3 选 1）。

    非演示模式返回 None；演示模式返回 {"vision": id, "review": id, "gen": id}。
    对应设计原稿 v5「演示模式 sidebar」：st.secrets 控制，默认关，不做界面开关。
    """
    if not demo_mode:
        return None
    with st.sidebar:
        st.markdown("#### Model Selection")
        st.caption("Pick a candidate per pipeline — 3-way comparison.")
        vision_label = st.selectbox(
            "Vision · acne severity · fine-tuned",
            list(config.VISION_CANDIDATES.keys()),
        )
        review_label = st.selectbox(
            "Review · PRO/CON · non-fine-tuned",
            list(config.REVIEW_CANDIDATES.keys()),
        )
        gen_label = st.selectbox(
            "Text-gen · recommendation · non-fine-tuned",
            list(config.GEN_CANDIDATES.keys()),
        )
    return {
        "vision": config.VISION_CANDIDATES[vision_label],
        "review": config.REVIEW_CANDIDATES[review_label],
        "gen": config.GEN_CANDIDATES[gen_label],
    }


def _set_feedback(key: str, value: str) -> None:
    """反馈回调：写 session_state（on_click，不显式 rerun，避免回顶）。"""
    st.session_state[key] = value


def render_feedback() -> None:
    """反馈区：两个问题（推荐 / 评论摘要）横排并排，回答后该组变感谢语；都答后居中一条。

    用 st.button + on_click（先写 session_state 再自动 rerun），不回顶；
    不做手搓 JS（st.markdown 注入的 <script> 不会执行）。
    """
    C = _css()
    reco_done = st.session_state.get("feedback_reco") is not None
    digest_done = st.session_state.get("feedback_digest") is not None

    if reco_done and digest_done:
        st.markdown(
            f'<div class="{C["feedback_thanks"]} {C["center"]}">We appreciate your feedback</div>',
            unsafe_allow_html=True,
        )
        return

    # 两个 group 横排（对齐设计稿 .feedback flex）
    g1, g2 = st.columns(2)
    with g1:
        if reco_done:
            st.markdown(f'<div class="{C["feedback_thanks"]}">We appreciate your feedback</div>', unsafe_allow_html=True)
        else:
            q, b1, b2 = st.columns([2.6, 0.7, 0.7])
            with q:
                st.markdown(f'<span class="fb-q">Was this recommendation useful?</span>', unsafe_allow_html=True)
            with b1:
                st.button("👍", key="reco_helpful", on_click=_set_feedback, args=("feedback_reco", "helpful"))
            with b2:
                st.button("👎", key="reco_not", on_click=_set_feedback, args=("feedback_reco", "not_helpful"))
    with g2:
        if digest_done:
            st.markdown(f'<div class="{C["feedback_thanks"]}">We appreciate your feedback</div>', unsafe_allow_html=True)
        else:
            q, b1, b2 = st.columns([2.6, 0.7, 0.7])
            with q:
                st.markdown(f'<span class="fb-q">Was the review digest useful?</span>', unsafe_allow_html=True)
            with b1:
                st.button("👍", key="digest_helpful", on_click=_set_feedback, args=("feedback_digest", "helpful"))
            with b2:
                st.button("👎", key="digest_not", on_click=_set_feedback, args=("feedback_digest", "not_helpful"))


def render_actions(summary_png: bytes) -> None:
    """06 行动区（深色容器）：下载 PNG（原生 <a download>）+ 分享/保存（原生组件）。

    Download 用原生 <a download> 而非 st.download_button：后者在 Streamlit 1.36
    的 use_container_width 失效（wrapper 固定内容宽 204px，且整条父链 flex 收缩，
    CSS/内联均无法覆盖）。<a download> 是浏览器原生下载，无需 JS，
    CSS width:100% 直接生效，与 Share/Save 等宽。
    """
    C = _css()
    copy = _copy()
    b64 = base64.b64encode(summary_png).decode()
    with st.container(border=True):
        st.markdown(
            f'<div class="{C["actions_head"]}">'
            f'<h3>{copy["save_head"]}</h3>'
            f'<div class="{C["actions_sub"]}">{copy["save_sub"]}</div>'
            '</div>',
            unsafe_allow_html=True,
        )
        c1, c2, c3 = st.columns(_layout()["save_cols"], vertical_alignment="center")
        with c1:
            st.markdown(
                f'<a class="dl-btn" download="skin_snapshot.png" '
                f'href="data:image/png;base64,{b64}">{html.escape(copy["buttons"]["download"])}</a>',
                unsafe_allow_html=True,
            )
        with c2:
            if st.button(copy["buttons"]["share"], use_container_width=True):
                st.toast(copy["toast_share"])
        with c3:
            if st.button(copy["buttons"]["save"], type="primary", use_container_width=True):
                st.session_state.saved = True
                st.toast(copy["toast_saved"])
