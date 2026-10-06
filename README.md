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

## Project structure

```
isom5240-sephora-skin-advisor/
├── app.py                  # main entry (thin shell): page + flow orchestration
├── config.py               # model names, thresholds, limits, paths, switches
├── style.css               # UI theme (Sephora base: black / ivory / brand red)
├── data/
│   ├── bridge_mapping.json # severity → ingredients → products (business-editable)
│   └── style_openers.json  # recommendation openers (style × severity × variant)
├── models/
│   ├── vision.py           # ViT acne severity classification
│   ├── review.py           # DistilBERT PRO/CON review classification
│   └── generator.py        # recommendation text generation (with fallback)
├── ui/
│   └── components.py       # severity bar, product card, Verified Buyer Digest, tone dropdown
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
| Vision | `vit-acne-severity` | 4-class acne severity |
| Review | `distilbert-sephora-review-curator` | PRO/CON classification |
| Generator | `distilgpt2-sephora-reco` | recommendation continuation |

## Data sources

- **ACNE04** — acne severity (0–4 raw labels, consolidated to 4 classes), 70/15/15 stratified split.
- **Kaggle "Sephora Products and Skincare Reviews"** — ~1M reviews, sampled a few thousand for fine-tuning.
  <https://www.kaggle.com/datasets/nadyinky/sephora-products-and-skincare-reviews>

## Known gotchas (from the Image Storyteller IA build)

- **transformers 5.x removed `image-to-text`** (now `image-text-to-text`). We use classic `image-classification` / `text-classification`, so pinning `transformers==4.42.0` is safe.
- **torchvision is transitively imported** by the transformers image-processor registry (ZoeDepth chain) — keep `torchvision` in requirements, matching the `torch` version.
- **Streamlit `st.selectbox` gained a `filter_mode` arg in 1.64** — pass `filter_mode=None` to disable type-to-filter on the tone dropdown.
- **`st.rerun()` after a successful generation** — otherwise the result is written to `session_state` but the page doesn't refresh.
