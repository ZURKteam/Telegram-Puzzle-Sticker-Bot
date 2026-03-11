# -*- coding: utf-8 -*-
# запуск

import sys
import subprocess
import asyncio
import logging

# проверка модулей
need = ["aiogram", "PIL", "cv2"]
miss = []

for m in need:
    try:
        mod = m if m != "PIL" else "Pillow"
        __import__(m if m != "PIL" else "PIL")
    except ImportError:
        miss.append(m if m != "PIL" else "Pillow")

if miss:
    print(f"[!] нет модулей: {', '.join(miss)}")
    r = input("поставить? (y/n): ").strip().lower()
    
    if r == "y":
        for m in miss:
            pkg = "opencv-python" if m == "cv2" else m.lower()
            print(f"[*] ставлю {pkg}...")
            subprocess.check_call([sys.executable, "-m", "pip", "install", pkg])
        print("[+] готово, перезапусти скрипт")
    else:
        print("[-] отказано")
    sys.exit(1)


from pathlib import Path
from aiogram import Bot, Dispatcher
from aiogram.utils.token import TokenValidationError, validate_token
from bot_handlers import rt, worker
from config_new import cfg

log = logging.getLogger(__name__)


def setup_log():
    fmt = "%(asctime)s | %(name)s | %(levelname)s | %(message)s"
    logging.basicConfig(level=logging.INFO, format=fmt)
    
    # отключаем лишнее
    logging.getLogger("aiogram").setLevel(logging.WARNING)
    logging.getLogger("aiohttp").setLevel(logging.WARNING)


def setup_dirs():
    Path(cfg.tmp).mkdir(exist_ok=True)
    Path(cfg.parts).mkdir(exist_ok=True)
    Path(cfg.vids).mkdir(exist_ok=True)


def check_token() -> None:
    tok = cfg.token.strip()

    if not tok or tok == "YOUR_BOT_TOKEN":
        print("[!] BOT_TOKEN не задан")
        print("[i] Создай файл .env рядом с run.py и пропиши:")
        print("    BOT_TOKEN=123456:ABCDEF")
        raise SystemExit(1)

    try:
        validate_token(tok)
    except TokenValidationError:
        print("[!] BOT_TOKEN выглядит некорректным")
        print("[i] Проверь токен от BotFather в .env или .env.example")
        raise SystemExit(1)


async def main():
    setup_log()
    setup_dirs()
    check_token()
    
    log.info("запуск бота")
    
    bot = Bot(token=cfg.token)
    dp = Dispatcher()
    dp.include_router(rt)
    
    # воркер
    wt = asyncio.create_task(worker(bot))
    
    try:
        await dp.start_polling(bot)
    finally:
        wt.cancel()
        try:
            await wt
        except asyncio.CancelledError:
            pass
        
        await bot.session.close()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nстоп")
