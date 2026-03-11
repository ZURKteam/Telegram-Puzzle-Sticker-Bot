# -*- coding: utf-8 -*-
# обработка картинок и видео

import os
import subprocess
import logging
from pathlib import Path

import cv2
from PIL import Image

from config_new import cfg

log = logging.getLogger(__name__)


def resize_emoji(img):
    # ресайз под телегу (100x100)
    sz = cfg.emoji_px
    return img.resize((sz, sz), Image.LANCZOS)


def cut_img(path, cols, rows, uid, with_prev=True):
    # режем картинку на куски
    log.info(f"режу {path} на {cols}x{rows}")
    
    img = Image.open(path).convert("RGBA")
    w, h = img.size
    
    pw = w // cols
    ph = h // rows
    
    result = []
    cnt = 0
    
    # сначала превью если надо
    if with_prev:
        full = resize_emoji(img.copy())
        fp = f"{cfg.parts}/{uid}_full.webp"
        full.save(fp, "WEBP", quality=90)
        result.append(fp)
    
    # потом кусочки
    for r in range(rows):
        for c in range(cols):
            x1 = c * pw
            y1 = r * ph
            x2 = (c + 1) * pw
            y2 = (r + 1) * ph
            
            piece = img.crop((x1, y1, x2, y2))
            piece = resize_emoji(piece)
            
            fp = f"{cfg.parts}/{uid}_{cnt}.webp"
            piece.save(fp, "WEBP", quality=90)
            result.append(fp)
            cnt += 1
    
    log.info(f"нарезал {cnt} кусков")
    return result


def get_frame(vid_path, out_path):
    # достаем первый кадр из видео
    try:
        cap = cv2.VideoCapture(vid_path)
        ok, frame = cap.read()
        cap.release()
        
        if ok:
            cv2.imwrite(out_path, frame)
            return True
        return False
    except Exception as e:
        log.error(f"ошибка кадра: {e}")
        return False


def cut_vid(path, cols, rows, uid, with_prev=True):
    # режем видео на анимированные кусочки
    log.info(f"режу видео {path} на {cols}x{rows}")
    
    cap = cv2.VideoCapture(path)
    
    w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    
    pw = w // cols
    ph = h // rows
    
    # папка под кадры
    frames_dir = Path(cfg.tmp) / f"fr_{uid}"
    frames_dir.mkdir(parents=True, exist_ok=True)
    
    # сохраняем все кадры
    fc = 0
    while True:
        ok, frame = cap.read()
        if not ok:
            break
        cv2.imwrite(str(frames_dir / f"{fc}.png"), frame)
        fc += 1
    
    cap.release()
    
    # ограничиваем кол-во кадров (телега не любит длинные)
    max_fr = min(fc, 90)
    step = max(1, fc // max_fr)
    
    result = []
    
    # превью - первый кадр статикой
    if with_prev:
        f0 = frames_dir / "0.png"
        if f0.exists():
            fr = Image.open(str(f0)).convert("RGBA")
            full = resize_emoji(fr)
            fp = f"{cfg.parts}/{uid}_full.webp"
            full.save(fp, "WEBP", quality=90)
            result.append(fp)
    
    # нарезаем каждую клетку
    for row in range(rows):
        for col in range(cols):
            # папка под кадры этого куска
            part_dir = Path(cfg.tmp) / f"p_{uid}_{col}_{row}"
            part_dir.mkdir(parents=True, exist_ok=True)
            
            # вырезаем из каждого кадра
            out_f = 0
            for f in range(0, fc, step):
                fr_path = frames_dir / f"{f}.png"
                if not fr_path.exists():
                    continue
                    
                img = cv2.imread(str(fr_path))
                
                x1 = col * pw
                y1 = row * ph
                x2 = (col + 1) * pw
                y2 = (row + 1) * ph
                
                crop = img[y1:y2, x1:x2]
                cv2.imwrite(str(part_dir / f"{out_f}.png"), crop)
                out_f += 1
            
            # конвертим в webm через ffmpeg
            out_file = f"{cfg.parts}/{uid}_{col}_{row}.webm"
            
            sz = cfg.emoji_px
            scale = f"scale={sz}:{sz}:force_original_aspect_ratio=disable"
            
            cmd = [
                "ffmpeg", "-y",
                "-framerate", str(cfg.vid_fps),
                "-i", str(part_dir / "%d.png"),
                "-vf", scale,
                "-c:v", "libvpx-vp9",
                "-b:v", cfg.vid_bitrate,
                "-pix_fmt", "yuva420p",
                "-an",
                "-t", "3",
                out_file
            ]
            
            try:
                subprocess.run(cmd, capture_output=True, check=True)
                result.append(out_file)
            except subprocess.CalledProcessError as e:
                log.error(f"ffmpeg error: {e.stderr.decode() if e.stderr else '?'}")
    
    log.info(f"нарезал {len(result)} анимаций")
    return result
