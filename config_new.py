# -*- coding: utf-8 -*-
# конфиг бота

import os
from dataclasses import dataclass
from pathlib import Path


def load_env() -> None:
    base = Path(__file__).resolve().parent

    for name in (".env", ".env.example"):
        fp = base / name
        if not fp.exists():
            continue

        for raw in fp.read_text(encoding="utf-8").splitlines():
            line = raw.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue

            k, v = line.split("=", 1)
            os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))


load_env()


@dataclass
class Config:
    token: str
    max_vid_mb: int = 20
    max_vid_sec: int = 10
    max_emoji: int = 120
    emoji_px: int = 100  # телега требует 100x100
    vid_fps: int = 15
    vid_bitrate: str = "256K"
    
    # папки
    tmp: str = "temp"
    parts: str = "parts"
    vids: str = "videos"


def get_cfg():
    tok = os.getenv("BOT_TOKEN", "YOUR_BOT_TOKEN").strip()
    
    return Config(
        token=tok,
        max_vid_mb=int(os.getenv("MAX_VIDEO_MB", 20)),
        max_vid_sec=int(os.getenv("MAX_VIDEO_SEC", 10)),
        max_emoji=int(os.getenv("MAX_STICKERS", 120)),
    )


cfg = get_cfg()


def make_dirs():
    for d in [cfg.tmp, cfg.parts, cfg.vids]:
        os.makedirs(d, exist_ok=True)
