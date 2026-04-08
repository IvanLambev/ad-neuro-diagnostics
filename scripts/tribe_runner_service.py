from __future__ import annotations

import json
import os
import sys
import threading
from pathlib import Path

import numpy as np
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from tribev2 import TribeModel

VENV_BIN = str(Path(sys.executable).parent)
os.environ["PATH"] = VENV_BIN + os.pathsep + os.environ.get("PATH", "")

app = FastAPI(title="TRIBE Bare Metal Runner")
gpu_lock = threading.Lock()


class RunnerRequest(BaseModel):
    clip_path: str
    output_dir: str
    device: str = "cuda"


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/v1/run")
def run_job(request: RunnerRequest) -> dict[str, object]:
    clip_path = Path(request.clip_path)
    output_dir = Path(request.output_dir)
    if not clip_path.exists():
        raise HTTPException(status_code=404, detail=f"Clip not found: {clip_path}")

    output_dir.mkdir(parents=True, exist_ok=True)
    with gpu_lock:
        model = TribeModel.from_pretrained(
            "facebook/tribev2",
            cache_folder=str(output_dir / "cache"),
            device=request.device,
        )
        events = model.get_events_dataframe(video_path=str(clip_path))
        preds, _segments = model.predict(events, verbose=True)
        np.save(output_dir / "preds.npy", preds)
        events.to_csv(output_dir / "events.csv", index=False)
        (output_dir / "manifest.json").write_text(
            json.dumps(
                {
                    "stage": "tribe_raw",
                    "status": "ready",
                    "clip_path": str(clip_path),
                    "device": request.device,
                },
                indent=2,
            ),
            encoding="utf-8",
        )
    return {
        "status": "ready",
        "preds_shape": list(preds.shape),
        "events_rows": int(len(events)),
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8765, workers=1)
