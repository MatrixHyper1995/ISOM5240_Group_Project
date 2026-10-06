# Sephora Skin Concern Advisor

Two-pipeline deep-learning advisor for Sephora.com:
- **ViT** (fine-tuned, image classification) → acne severity (None / Mild / Moderate / Severe)
- **DistilBERT** (fine-tuned, text classification) → verified-buyer review curation into PRO/CON
- **distilgpt2** (text generation) → recommendation copy (with template fallback)

Only recommends, never diagnoses, never sells. Processed in memory, never stored.

## Run locally

```bash
pip install -r requirements.txt
streamlit run app.py
```

> **Deploy to Streamlit Cloud**: the requirements pin Python 3.12 wheels (`cp312`).
> Streamlit Cloud now defaults to **Python 3.14**, which has no wheel for torch 2.3.1 / Pillow 10.3.0
> (you'll get `torch-2.3.1+cpu-cp312... is not a supported wheel` + `Failed to build pillow==10.3.0`).
> Fix: app → Settings → **Advanced settings → Python version → 3.12**, then save.

## Project structure

```
isom5240-sephora-skin-advisor/
├── app.py                  # main entry (thin shell): page + flow orchestration
├── config.py               # model names, thresholds, limits, paths, switches
├── style.css               # UI theme (Sephora base: black / ivory / brand red)
├── data/
│   ├── bridge_mapping.json # severity → ingredients → products (business-editable)
│   ├── style_openers.json  # recommendation openers (style × severity × variant)
│   └── reviews_sample.csv  # sampled real reviews for the digest (8 products × 50)
├── models/
│   ├── __init__.py         # package marker
│   ├── vision.py           # ViT acne severity classification
│   ├── review.py           # DistilBERT PRO/CON review classification
│   └── generator.py        # recommendation text generation (with fallback)
├── ui/
│   ├── __init__.py         # package marker
│   ├── components.py       # severity bar, product card, Verified Buyer Digest, tone dropdown
│   └── card.py             # Pillow summary card (downloadable PNG)
├── utils.py                # image helpers, mapping lookup, review batching
├── requirements.txt
└── README.md
```

## Design principles

- **Config / data / code separated** — business updates `data/*.json` and `config.py` without touching code.
- **app.py is a thin shell** — orchestrates the flow, no business logic inside.
- **Models are lazy-loaded** (`@st.cache_resource`) and released on demand ("use one, kill one") to fit Streamlit Cloud's small CPU memory.
- **Text-gen fails → template fallback**, the flow never breaks.
- **Severe (level 3)** always leads with "see a dermatologist"; products are adjunct only.

## Model sources

Fine-tuned on Colab, hosted on Hugging Face, deployed on Streamlit Cloud.
Replace `<HF_USERNAME>` in `config.py` after fine-tuning.

| Pipeline | Base model | Task |
|---|---|---|
| Vision | `jiefangziyou/vit-acne-severity` | 4-class acne severity |
| Review | `distilbert-sephora-review-curator` | PRO/CON classification |
| Generator | `distilgpt2-sephora-reco` | recommendation continuation |

## Data sources

- **ACNE04** — acne severity (0–4 raw labels, consolidated to 4 classes), 70/15/15 stratified split.
- **Kaggle "Sephora Products and Skincare Reviews"** — ~1M reviews (`sephora_reviews.csv`), sampled a few thousand for fine-tuning; `data/reviews_sample.csv` holds 400 runtime samples (8 recommended products × 50) with `verified_purchase=True`.
  <https://www.kaggle.com/datasets/nadyinky/sephora-products-and-skincare-reviews>

## Known gotchas (from the Image Storyteller IA build)

- **transformers 5.x removed `image-to-text`** (now `image-text-to-text`). We use classic `image-classification` / `text-classification`, so pinning `transformers==4.42.0` is safe.
- **torchvision is NOT required at runtime** — the ViT image-classification pipeline uses the PIL-based `ViTImageProcessor` by default (`use_fast=False`); the torchvision-backed `ViTImageProcessorFast` is only used if you explicitly pass `use_fast=True`. Verified against transformers 4.42.0 source (`image_processing_utils_fast.py` imports torchvision behind `if is_torchvision_available():`). Keep it OUT of requirements.txt to shrink the deploy.
- **Streamlit `st.selectbox` gained a `filter_mode` arg in 1.64** — pass `filter_mode=None` to disable type-to-filter on the tone dropdown.
- **`st.rerun()` after a successful generation** — otherwise the result is written to `session_state` but the page doesn't refresh.
- **`torch` must be the CPU wheel** — PyPI's default `torch` is the CUDA build, which drags in ~5GB of `nvidia-*-cu12` packages and fails on Streamlit Cloud's small memory (`installer returned non-zero exit code`). Pin the CPU wheel via direct URL (`download.pytorch.org/whl/cpu`, `cp312` = Python 3.12).
