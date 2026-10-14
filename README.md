# ADAS Scene Search: CLIP-based retrieval and evaluation on EuroCity

Search ADAS drive data with natural language ("wet road at night with oncoming traffic") and measure how far each answer can be trusted.

> **Status:** early work in progress. Zero-shot CLIP tagging, a labelling tool, and the evaluation design are in place. Retrieval, the LLM layer and fine-tuning are next (see [Roadmap](#roadmap)).

## Problem

ADAS test and validation teams spend hours scrolling through drive recordings to find specific situations: night scenes, wet roads, oncoming traffic, a particular vehicle type. Recording metadata rarely covers these conditions.

This project builds a scene search tool over camera frames and treats **evaluation as a first-class feature**. A search result is only useful if you know how often the tags behind it are wrong.

## Data

- **EuroCity Persons / Tracking** (TU Delft and Daimler): urban drives across European cities, day and night.
- Used so far: one Rome night sequence (`IT_Roma00`, ~1,200 frames), with a Milan sequence planned as the held-out test set.
- **Images are not included in this repo.** The dataset is licensed for non-commercial research use; download it from the official source.

## What's built so far

| Component | File | What it does |
|---|---|---|
| Zero-shot tagging | `data_parse.ipynb` | Runs `openai/clip-vit-base-patch32` on frames and scores them against text prompts per attribute |
| Labelling app | `data_label.py` | Gradio app: shows N evenly spaced frames from a folder, and you pick labels → `labels.csv` |

### Label schema (v1)

| Attribute | Classes |
|---|---|
| `lighting` | day, dusk, night |
| `main_vehicle` (most prominent vehicle ahead) | car, van, truck, bus, none |
| `traffic` | both directions, one direction |

### Run the labelling app

```bash
python -m pip install gradio
py data_label.py --folder "path/to/sequence_folder" --n 10
# open http://127.0.0.1:7860 ; app exits after N frames, output: labels.csv
```

## Findings so far

1. **One softmax per attribute, not one across all labels.** Putting `['car', 'truck', 'cat', 'day', 'night']` into a single softmax made "night" look uncertain (0.26) on obvious night frames, because object and lighting labels competed for the same probability mass. Renormalised within the lighting group, night is ~0.99. Each attribute now gets its own softmax.
2. **Prompt templates help.** "a photo of a city street at night" scores more reliably than bare words like "night", which matches how CLIP was trained on image captions.
3. **CLIP confuses boxy vans with trucks.** On consecutive Rome frames, a white MPV flipped between car and truck (0.34 vs 0.39) as it got closer. This is a known failure case to track.
4. **CLIP can't count or reason about direction.** It encodes the whole image as one 512-d vector, so "fewer than 3 oncoming cars" or "oncoming vs same direction" barely register. Consecutive frames with 2 vs 3 oncoming cars scored almost identically. **Design decision:** use CLIP for scene-level attributes, and add a detector for counts and positions.

## Evaluation design

- **Ground truth:** hand labels per a written labelling guide (`labeling_guide.md`, with definitions and edge cases). Labels are blind, made before looking at CLIP's output, to avoid anchoring bias.
- **Split by sequence, not by frame.** Consecutive frames are near-duplicates, so a random frame split leaks and inflates accuracy.
- **Dev / test:** Rome = dev (prompt tuning), Milan = held-out test, measured once. Later: leave-one-city-out across all cities.
- **Metrics:** accuracy per attribute with 95% CIs (Wilson), frames by number of wrong attributes, and later retrieval precision@10 per query.
- **Sample size note:** with 24 frames, 22/24 correct is 92% but the 95% CI is roughly 74–98%. Early results are reported as indicative only.

### Results

| Attribute | Rome (dev) | Milan (test) |
|---|---|---|
| lighting | _TBD_ | _TBD_ |
| main_vehicle | _TBD_ | _TBD_ |
| traffic | _TBD_ | _TBD_ |

## Roadmap

- [x] Zero-shot CLIP tagging with per-attribute softmax
- [x] Labelling app → `labels.csv`
- [ ] Compare script: labels vs CLIP → accuracy table + failure list
- [ ] Embed frames once (subsampled: every 20th frame) → LanceDB index
- [ ] Text-to-frame search + Gradio UI
- [ ] LLM query parser (local, via Ollama) → structured filters + grounded answers citing frame ids
- [ ] Fine-tune only where evals show a gap: linear probe for scene tags, detector for vehicle type and counts
- [ ] FastAPI + Docker, demo on Hugging Face Spaces

## Standards alignment (planned)

- Scene tag vocabulary aligned to **BSI PAS 1883** (ODD taxonomy)
- Label export compatible with **ASAM OpenLABEL**
- Data quality practices (labelling guide, consistency checks, leakage-free splits) in the spirit of **ISO/PAS 8800**

## Environment

Windows, Python 3.13, CPU only (8 GB RAM).

```bash
python -m pip install torch transformers pillow gradio pandas
```

## Licence

Code: MIT (or your choice). Dataset: see EuroCity terms. No images or derived labels from the dataset are redistributed here.
