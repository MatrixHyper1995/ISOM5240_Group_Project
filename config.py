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
# 模型：三条 pipeline，每条 3 选 1 候选（label → Hugging Face model id）
# 选型论证见「评估设计」；评估选优后更新默认项（demo 关闭时用默认项）
# ---------------------------------------------------------------------------
VISION_CANDIDATES = {
    # fine-tuned pipeline：base 三选一 → ACNE04 fine-tune
    # 「current」是现成顶替（尚未训练，保证 demo 跑通）；fine-tune 完成后移除，默认改训练产物
    "current (jiefangziyou)": "jiefangziyou/vit-acne-severity",
    "vit-base-patch16-224": "google/vit-base-patch16-224",
    "vit-small-patch16-224": "google/vit-small-patch16-224",
    "resnet-50": "microsoft/resnet-50",
}
REVIEW_CANDIDATES = {
    # non-fine-tuned：三个现成情感模型（SST-2 / RoBERTa / multilingual-BERT）
    "distilbert-sst-2": "distilbert-base-uncased-finetuned-sst-2-english",
    "twitter-roberta-sentiment": "cardiffnlp/twitter-roberta-base-sentiment-latest",
    "bert-sentiment": "nlptown/bert-base-multilingual-uncased-sentiment",
}
GEN_CANDIDATES = {
    # non-fine-tuned：三个现成生成模型（GPT-2 家族）
    "distilgpt2": "distilgpt2",
    "gpt2": "gpt2",
    "gpt2-medium": "gpt2-medium",
}

# 默认模型 id（demo_mode 关闭 / 未选择时用）
VISION_MODEL = VISION_CANDIDATES["current (jiefangziyou)"]   # ViT 痘痘严重度分类（现成顶替）
REVIEW_MODEL = REVIEW_CANDIDATES["distilbert-sst-2"]          # DistilBERT 评论 PRO/CON（SST-2 情感二分类）
GEN_MODEL    = GEN_CANDIDATES["gpt2-medium"]                  # 推荐文案续写（GPT-2 medium 355M，质量更稳）

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
UI_SPEC_PATH = DATA_DIR / "ui_spec.json"          # UI 组件参数表（类名/格数/列宽/文案）
CSS_PATH     = BASE_DIR / "style.css"             # UI 样式
