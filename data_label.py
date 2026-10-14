import argparse
import csv
import os
import threading
from pathlib import Path
 
import gradio as gr

LABELS = {'lighting':['day','night'],
                'vehicle': ['cars','bus'],
                'traffic': ['vehicle in same direction', 'vehicle in opposite direction']}

p = argparse.ArgumentParser()
p.add_argument("--folder", required=True)
p.add_argument("--n", type=int, default=4)
args = p.parse_args()

folder = Path(args.folder)
images = sorted(f for f in folder.iterdir() if f.suffix.lower() in {".png", ".jpg", ".jpeg"})
frames = [str(f) for f in images[:: max(1, len(images) // args.n)][: args.n]]

with open("labels.csv", "w", newline="", encoding="utf-8") as f:   # fresh file each run
    csv.writer(f).writerow(["file", *LABELS])

def save(i, *tags):
    if i >= len(frames):                      # already finished: ignore extra clicks
        return i, None, "Done - labels.csv saved", *[None] * len(LABELS)
    if None in tags:
        gr.Warning("Pick every label.")
        return i, frames[i], f"{i + 1} / {len(frames)}", *tags
    with open("labels.csv", "a", newline="", encoding="utf-8") as f:
        csv.writer(f).writerow([frames[i], *tags])
    i += 1
    if i == len(frames):
        print(f"Done: {i} frames saved to labels.csv. Exiting.")
        threading.Timer(1.0, lambda: os._exit(0)).start()   # stop the server after --n frames
        return i, None, "Done - labels.csv saved. App closed, you can close this tab.", *[None] * len(LABELS)
    return i, frames[i], f"{i + 1} / {len(frames)}", *[None] * len(LABELS)

with gr.Blocks() as app:
    idx = gr.State(0)
    status = gr.Markdown(f"1 / {len(frames)}")
    img = gr.Image(value=frames[0], height=480, interactive=False)
    radios = [gr.Radio(v, label=k) for k, v in LABELS.items()]
    gr.Button("Save & next").click(save, [idx, *radios], [idx, img, status, *radios])
 
app.launch(allowed_paths=[str(folder.resolve())])