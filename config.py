"""
Sephora Skin Concern Advisor — 配置文件
Configuration: model names, thresholds, limits, paths, switches.
改配置不动代码 / Edit config without touching code.

参考 / Reference: Image Storyteller (IA) 的「配置抽离」经验 —— 选项与默认值独立成文件，
app.py 只读配置，改参数不动业务逻辑。

技术栈 / Tech stack: Streamlit + Hugging Face Transformers
  - ViT (image-classification)     痘痘严重度分类
  - DistilBERT (text-classification) 评论 PRO/CON
  - distilgpt2 (text-generation)   推荐文案续写（失败回退模板）
"""
from pathlib import Path

# ---------------------------------------------------------------------------
# 模型名（微调后替换 <HF_USERNAME>）/ Model IDs (replace <HF_USERNAME> after fine-tune)
# ---------------------------------------------------------------------------
VISION_MODEL = "jiefangziyou/vit-acne-severity"                    # ViT 痘痘严重度分类
REVIEW_MODEL = "<HF_USERNAME>/distilbert-sephora-review-curator"    # DistilBERT 评论 PRO/CON
GEN_MODEL    = "<HF_USERNAME>/distilgpt2-sephora-reco"              # 推荐文案续写

# ---------------------------------------------------------------------------
# 阈值与限制 / Thresholds & limits
# ---------------------------------------------------------------------------
LOW_CONF_THRESHOLD = 0.60    # 置信度低于此值 → 低置信提示 / low-confidence hint below this
MAX_UPLOAD_MB      = 10      # 上传大小上限 / upload size limit
MAX_UPLOAD_BYTES   = MAX_UPLOAD_MB * 1024 * 1024
IMG_SIZE           = 224     # 图片 resize 尺寸 / image resize size
ALLOWED_TYPES      = ["png", "jpg", "jpeg", "bmp"]

# ---------------------------------------------------------------------------
# 开关 / Switches
# ---------------------------------------------------------------------------
ENABLE_TEXT_GEN = True       # text-gen 开关；False 或加载失败 → 模板回退 / text-gen switch

# 评论摘要条数 / review digest counts
PRO_TOP_K = 3                # 每产品 PRO 摘要条数 / PRO digests per product
CON_TOP_K = 1                # 每产品 CON 摘要条数 / CON digests per product

# ---------------------------------------------------------------------------
# 路径（用 __file__ 定位，Cloud 任意工作目录都能找到）/ Paths
# ---------------------------------------------------------------------------
BASE_DIR     = Path(__file__).parent
DATA_DIR     = BASE_DIR / "data"
BRIDGE_PATH  = DATA_DIR / "bridge_mapping.json"   # 桥映射表：等级 → 成分 → 产品
OPENERS_PATH = DATA_DIR / "style_openers.json"    # 推荐文案开头句
CSS_PATH     = BASE_DIR / "style.css"             # UI 样式
