"""
Sephora Skin Concern Advisor — 图片卡片生成
Summary card generator (Pillow): 生成「我的肤质快照」分享卡，可下载。

参考 / Reference: Image Storyteller 的「暖纸相框」视觉经验 ——
米白底 + 衬线标题 + 直角 + 色弱友好（明暗不靠红绿）。
"""
import io
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

# 配色（Sephora 基底 + 色弱友好）
BG = "#FBF7F2"            # 米白底
INK = "#1A1A1A"           # 近黑（主文字）
MUTED = "#6E6A63"         # 次级文字
LINE = "#E5DED2"          # 细线
GOLD = "#C9A96E"          # 香槟金（装饰线）
BRAND_RED = "#D61F26"     # 品牌红（仅装饰，非语义）
BAR_OFF = "#E8E2D8"       # 分段条未点亮（浅）
BAR_ON = "#1A1A1A"        # 分段条点亮（深，明暗区分）

W, PAD = 1080, 72

# 字体候选（仓库内 fonts/ 优先 → Windows → DejaVu → 默认）
# 仓库内打包字体：Cloud（纯 Linux）没有 /mnt/c/Windows/Fonts，也没有系统 DejaVu，
# 若不打包会回退到 load_default 位图小字体（忽略 size），导致标题变小 + 大片空白。
_FONTS = Path(__file__).resolve().parent.parent / "fonts"
_SERIF = [str(_FONTS / "DejaVuSerif.ttf"), "/mnt/c/Windows/Fonts/Georgia.ttf", "/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf"]
_SERIF_BOLD = [str(_FONTS / "DejaVuSerif-Bold.ttf"), "/mnt/c/Windows/Fonts/georgiab.ttf", "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf"]
_SANS = [str(_FONTS / "DejaVuSans.ttf"), "/mnt/c/Windows/Fonts/arial.ttf", "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"]
_SANS_BOLD = [str(_FONTS / "DejaVuSans-Bold.ttf"), "/mnt/c/Windows/Fonts/arialbd.ttf", "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"]


def _load_font(size: int, style: str = "sans"):
    """按 style 加载字体，找不到则回退 Pillow 默认。"""
    paths = {
        "serif": _SERIF,
        "serif_bold": _SERIF_BOLD,
        "sans": _SANS,
        "sans_bold": _SANS_BOLD,
    }.get(style, _SANS)
    for p in paths:
        try:
            return ImageFont.truetype(p, size)
        except Exception:
            continue
    return ImageFont.load_default()


def _wrap(draw, text: str, font, max_width: int) -> list[str]:
    """按像素宽度换行。"""
    words = text.split()
    lines = []
    cur = ""
    for w in words:
        t = (cur + " " + w).strip()
        if draw.textlength(t, font=font) <= max_width:
            cur = t
        else:
            if cur:
                lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines


def render_summary_card(
    severity_key: str,
    severity_label: str,
    confidence: float,
    recommendation: str | None,
    products: list[dict],
    cells: int = 4,
) -> bytes:
    """生成「我的肤质快照」PNG 卡片，返回 PNG 字节。"""
    body_w = W - PAD * 2
    measure = ImageDraw.Draw(Image.new("RGB", (10, 10)))

    f_brand = _load_font(26, "sans_bold")
    f_title = _load_font(120, "serif_bold")
    f_conf = _load_font(34, "serif")
    f_body = _load_font(38, "serif")
    f_pbrand = _load_font(24, "sans_bold")
    f_pname = _load_font(40, "sans_bold")
    f_pmeta = _load_font(30, "sans")
    f_note = _load_font(24, "sans")

    title = severity_label or "Mild"
    conf_text = f"Confidence: {confidence:.0%}"
    reco_lines = _wrap(measure, recommendation, f_body, body_w) if recommendation else []

    products_data = []
    for p in products:
        products_data.append({
            "brand": p.get("brand", "").upper(),
            "name_lines": _wrap(measure, p.get("name", ""), f_pname, body_w),
            "ing": " · ".join(p.get("ingredients", [])),
            "why_lines": _wrap(measure, p.get("why", ""), f_pmeta, body_w),
        })

    # 高度估算（与绘制严格对齐）
    y = PAD
    y += 44 + 30 + 150 + 50 + 44                      # 品牌行 + 金线 + 标题 + 置信度 + 分段条
    if reco_lines:
        y += len(reco_lines) * 52 + 8
    for d in products_data:
        y += 28 + 40 + len(d["name_lines"]) * 50 + 40 + len(d["why_lines"]) * 42 + 16
    y += 24 + 36                                      # 免责分隔线 + 免责文字
    H = y + PAD

    img = Image.new("RGB", (W, H), BG)
    draw = ImageDraw.Draw(img)

    # 顶部品牌行 + 金线
    y = PAD
    draw.text((PAD, y), "SEPHORA · SKIN SNAPSHOT", fill=BRAND_RED, font=f_brand)
    y += 44
    draw.line([(PAD, y), (W - PAD, y)], fill=GOLD, width=2)
    y += 30

    # 等级 + 置信度
    draw.text((PAD, y), title, fill=INK, font=f_title)
    y += 150
    draw.text((PAD, y), conf_text, fill=MUTED, font=f_conf)
    y += 50

    # 单色分段条（明暗不靠色）
    level = int(severity_key) + 1
    cell_w, cell_h, gap = 120, 16, 14
    for i in range(cells):
        x = PAD + i * (cell_w + gap)
        color = BAR_ON if i < level else BAR_OFF
        draw.rectangle([x, y, x + cell_w, y + cell_h], fill=color)
    y += cell_h + 28

    # 推荐文案
    for line in reco_lines:
        draw.text((PAD, y), line, fill=INK, font=f_body)
        y += 52
    if reco_lines:
        y += 8

    # 产品列表
    for d in products_data:
        draw.line([(PAD, y), (W - PAD, y)], fill=LINE, width=1)
        y += 28
        draw.text((PAD, y), d["brand"], fill=MUTED, font=f_pbrand)
        y += 40
        for line in d["name_lines"]:
            draw.text((PAD, y), line, fill=INK, font=f_pname)
            y += 50
        draw.text((PAD, y), d["ing"], fill=MUTED, font=f_pmeta)
        y += 40
        for line in d["why_lines"]:
            draw.text((PAD, y), line, fill=INK, font=f_pmeta)
            y += 42
        y += 16

    # 免责声明
    draw.line([(PAD, y), (W - PAD, y)], fill=LINE, width=1)
    y += 24
    draw.text((PAD, y), "For skincare reference only · Not a medical diagnosis", fill=MUTED, font=f_note)

    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()
