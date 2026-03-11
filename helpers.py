# -*- coding: utf-8 -*-
# вспомогательные функции

import shutil
import logging
from pathlib import Path
from typing import Any

from config_new import cfg

log = logging.getLogger(__name__)


def clear_user(uid: int) -> None:
    # чистим временные файлы юзера
    log.info(f"чистка файлов юзера {uid}")
    
    uid_s = str(uid)
    
    # temp
    tmp = Path(cfg.tmp)
    if tmp.exists():
        for f in tmp.iterdir():
            if uid_s in f.name:
                try:
                    if f.is_dir():
                        shutil.rmtree(f, ignore_errors=True)
                    else:
                        f.unlink()
                except OSError:
                    pass
    
    # parts
    pts = Path(cfg.parts)
    if pts.exists():
        for f in pts.iterdir():
            if uid_s in f.name:
                try:
                    f.unlink()
                except OSError:
                    pass
    
    # videos
    vds = Path(cfg.vids)
    if vds.exists():
        for f in vds.iterdir():
            if uid_s in f.name:
                try:
                    f.unlink()
                except OSError:
                    pass


def clear_all() -> None:
    # чистка при выключении
    log.info("полная чистка")
    
    for d in [cfg.tmp, cfg.parts]:
        p = Path(d)
        if p.exists():
            for f in p.iterdir():
                try:
                    if f.is_dir():
                        shutil.rmtree(f, ignore_errors=True)
                    else:
                        f.unlink()
                except OSError:
                    pass


def fmt_size(b: int | float) -> str:
    # форматирование размера файла
    for u in ['Б', 'КБ', 'МБ', 'ГБ']:
        if b < 1024:
            return f"{b:.1f} {u}"
        b /= 1024
    return f"{b:.1f} ТБ"


def check_size(c: int, r: int) -> tuple[bool, str]:
    # проверка размера пазла
    total = c * r + 1  # +1 на превью
    
    if c < 1 or r < 1:
        return False, "мин 1x1"
    
    if c > 20 or r > 20:
        return False, "макс сторона 20"
    
    if total > cfg.max_emoji:
        return False, f"макс {cfg.max_emoji - 1} эмодзи"
    
    return True, ""


def parse_sz(txt: str) -> tuple[int, int] | None:
    # парсим строку типа 3x5
    txt = txt.strip().lower()
    
    if 'x' not in txt:
        return None
    
    try:
        p = txt.split('x')
        if len(p) != 2:
            return None
        
        c = int(p[0].strip())
        r = int(p[1].strip())
        
        if c > 0 and r > 0:
            return c, r
    except ValueError:
        pass
    
    return None


class UserData:
    # хранилка данных юзеров
    
    def __init__(self) -> None:
        self._d: dict[int, dict[str, Any]] = {}
    
    def get(self, uid: int) -> dict[str, Any] | None:
        return self._d.get(uid)
    
    def set(self, uid: int, data: dict[str, Any]) -> None:
        self._d[uid] = data
    
    def upd(self, uid: int, **kw: Any) -> None:
        if uid in self._d:
            self._d[uid].update(kw)
    
    def rm(self, uid: int) -> None:
        self._d.pop(uid, None)
    
    def has(self, uid: int) -> bool:
        return uid in self._d


users = UserData()
