# -*- coding: utf-8 -*-
# хендлеры бота

import asyncio
import logging
import time
from pathlib import Path

from aiogram import Bot, Router, F
from aiogram.types import Message, CallbackQuery, FSInputFile, InputSticker
from aiogram.filters import Command
from aiogram.exceptions import TelegramRetryAfter, TelegramBadRequest

from config_new import cfg
from keyboard import sizes_kb, vid_mode_kb, cancel_kb, preview_kb
from proc import cut_img, cut_vid, get_frame
from helpers import users, clear_user, check_size, parse_sz, fmt_size

log = logging.getLogger(__name__)

rt = Router()

queue = asyncio.Queue()


# команды

@rt.message(Command("start"))
async def cmd_start(msg: Message):
    await msg.answer(
        "<b>Puzzle Emoji Bot</b>\n\n"
        "Кидай <b>фото</b> или <b>видео</b>, сделаю эмодзи-пазл\n\n"
        "Фото - статичные эмодзи\n"
        "Видео - анимированные или статичные\n\n"
        "Эмодзи можно вставлять в текст (нужен Premium)\n\n"
        f"Лимит: видео до {cfg.max_vid_mb}мб и {cfg.max_vid_sec}сек\n"
        f"Макс {cfg.max_emoji} эмодзи в паке",
        parse_mode="HTML"
    )


@rt.message(Command("help"))
async def cmd_help(msg: Message):
    await msg.answer(
        "<b>Как юзать:</b>\n\n"
        "1. Кидаешь фото/видео\n"
        "2. Для видео выбираешь режим\n"
        "3. Выбираешь размер\n"
        "4. Ждешь\n"
        "5. Добавляешь пак\n\n"
        "Размеры: 3x3, 5x5, 8x8 или свой\n"
        "Свой формат: <code>4x6</code>\n\n"
        "Для эмодзи в тексте нужен Premium",
        parse_mode="HTML"
    )


@rt.message(Command("cancel"))
async def cmd_cancel(msg: Message):
    uid = msg.from_user.id
    if users.has(uid):
        users.rm(uid)
        clear_user(uid)
        await msg.answer("отменено")
    else:
        await msg.answer("нечего отменять")


# фото

@rt.message(F.photo)
async def on_photo(msg: Message, bot: Bot):
    uid = msg.from_user.id
    
    photo = msg.photo[-1]
    fi = await bot.get_file(photo.file_id)
    
    fp = Path(cfg.tmp) / f"{uid}.jpg"
    await bot.download_file(fi.file_path, fp)
    
    users.set(uid, {
        "type": "img",
        "file": str(fp)
    })
    
    await msg.answer("выбери размер:", reply_markup=sizes_kb())


# видео

@rt.message(F.video)
async def on_video(msg: Message, bot: Bot):
    uid = msg.from_user.id
    vid = msg.video
    
    # проверки
    max_sz = cfg.max_vid_mb * 1024 * 1024
    if vid.file_size > max_sz:
        return await msg.answer(
            f"видео слишком большое\n"
            f"макс: {cfg.max_vid_mb}мб\n"
            f"твое: {fmt_size(vid.file_size)}"
        )
    
    if vid.duration > cfg.max_vid_sec:
        return await msg.answer(
            f"видео слишком длинное\n"
            f"макс: {cfg.max_vid_sec}сек\n"
            f"твое: {vid.duration}сек"
        )
    
    fi = await bot.get_file(vid.file_id)
    fp = Path(cfg.vids) / f"{uid}.mp4"
    await bot.download_file(fi.file_path, fp)
    
    users.set(uid, {
        "type": "vid",
        "file": str(fp)
    })
    
    await msg.answer("что делаем?", reply_markup=vid_mode_kb())


# выбор режима видео

@rt.callback_query(F.data.in_(["vid_anim", "vid_static"]))
async def cb_vid_mode(cb: CallbackQuery):
    uid = cb.from_user.id
    
    if not users.has(uid):
        return await cb.answer("сначала кинь видео", show_alert=True)
    
    mode = "anim" if cb.data == "vid_anim" else "static"
    users.upd(uid, vid_mode=mode)
    
    txt = "анимированный" if mode == "anim" else "статичный"
    
    await cb.message.edit_text(f"режим: {txt}\n\nвыбери размер:", reply_markup=sizes_kb())
    await cb.answer()


# выбор размера

@rt.callback_query(F.data.startswith("sz_"))
async def cb_size(cb: CallbackQuery):
    uid = cb.from_user.id
    
    if not users.has(uid):
        return await cb.answer("сначала кинь фото/видео", show_alert=True)
    
    sz_s = cb.data.replace("sz_", "")
    res = parse_sz(sz_s)
    
    if not res:
        return await cb.answer("ошибка", show_alert=True)
    
    c, r = res
    
    ok, err = check_size(c, r)
    if not ok:
        return await cb.answer(err, show_alert=True)
    
    users.upd(uid, cols=c, rows=r)
    
    await cb.message.edit_text(
        f"размер: <b>{c}x{r}</b>\n\n"
        "добавить оригинал первым эмодзи?\n"
        "(чтоб видно было как выглядит)",
        reply_markup=preview_kb(),
        parse_mode="HTML"
    )
    await cb.answer()


@rt.callback_query(F.data == "custom_sz")
async def cb_custom(cb: CallbackQuery):
    uid = cb.from_user.id
    
    if not users.has(uid):
        return await cb.answer("сначала кинь фото/видео", show_alert=True)
    
    users.upd(uid, wait_sz=True)
    
    await cb.message.edit_text(
        "введи размер типа <b>3x5</b>\n\n"
        f"макс {cfg.max_emoji} эмодзи",
        parse_mode="HTML"
    )
    await cb.answer()


@rt.callback_query(F.data == "cancel")
async def cb_cancel(cb: CallbackQuery):
    uid = cb.from_user.id
    
    if users.has(uid):
        clear_user(uid)
        users.rm(uid)
    
    await cb.message.edit_text("отменено")
    await cb.answer()


# превью

@rt.callback_query(F.data.in_(["prev_yes", "prev_no"]))
async def cb_preview(cb: CallbackQuery):
    uid = cb.from_user.id
    
    if not users.has(uid):
        return await cb.answer("сначала кинь фото/видео", show_alert=True)
    
    add_prev = cb.data == "prev_yes"
    users.upd(uid, add_prev=add_prev, wait_title=True)
    
    await cb.message.edit_text(
        "<b>название пака:</b>\n\n"
        "примеры: <code>My Cat</code>, <code>Котик</code>\n\n"
        "или <code>-</code> для автоназвания",
        parse_mode="HTML"
    )
    await cb.answer()


# текст (размер или название)

@rt.message(F.text)
async def on_text(msg: Message):
    uid = msg.from_user.id
    st = users.get(uid)
    
    if not st:
        return
    
    # ввод названия
    if st.get("wait_title"):
        title = msg.text.strip()
        
        if title == "-":
            c = st.get("cols", 3)
            r = st.get("rows", 3)
            title = f"Puzzle {c}x{r}"
        
        if len(title) > 64:
            return await msg.answer("слишком длинное (макс 64)")
        
        if len(title) < 1:
            return await msg.answer("введи название или <code>-</code>", parse_mode="HTML")
        
        users.upd(uid, wait_title=False, title=title)
        
        c = st.get("cols", 3)
        r = st.get("rows", 3)
        
        await msg.answer(f"создаю <b>{title}</b> ({c}x{r})...", parse_mode="HTML")
        
        await queue.put((uid, (c, r)))
        return
    
    # ввод размера
    if not st.get("wait_sz"):
        return
    
    res = parse_sz(msg.text)
    
    if not res:
        return await msg.answer("формат: <code>3x5</code>", parse_mode="HTML")
    
    c, r = res
    
    ok, err = check_size(c, r)
    if not ok:
        return await msg.answer(err)
    
    users.upd(uid, wait_sz=False, cols=c, rows=r)
    
    await msg.answer(
        f"размер: <b>{c}x{r}</b>\n\n"
        "добавить оригинал первым эмодзи?",
        reply_markup=preview_kb(),
        parse_mode="HTML"
    )


# обработка задачи

async def do_task(bot: Bot, uid: int, c: int, r: int):
    st = users.get(uid)
    
    if not st:
        log.warning(f"нет данных юзера {uid}")
        return
    
    try:
        add_prev = st.get("add_prev", True)
        
        # нарезаем
        if st["type"] == "img":
            parts = cut_img(st["file"], c, r, uid, add_prev)
        else:
            if st.get("vid_mode") == "static":
                frame_p = f"{cfg.tmp}/{uid}_fr.png"
                if get_frame(st["file"], frame_p):
                    parts = cut_img(frame_p, c, r, uid, add_prev)
                else:
                    await bot.send_message(uid, "ошибка кадра")
                    return
            else:
                parts = cut_vid(st["file"], c, r, uid, add_prev)
        
        if not parts:
            await bot.send_message(uid, "не получилось нарезать")
            return
        
        # создаем пак
        me = await bot.get_me()
        ts = int(time.time())
        pack_name = f"e_{uid}_{ts}_by_{me.username}"
        
        title = st.get("title", f"Puzzle {c}x{r}")
        
        # первый эмодзи
        fmt = "static" if parts[0].endswith(".webp") else "video"
        first = InputSticker(
            sticker=FSInputFile(parts[0]),
            emoji_list=["🧩"],
            format=fmt
        )
        
        try:
            await bot.create_new_sticker_set(
                user_id=uid,
                name=pack_name,
                title=title,
                stickers=[first],
                sticker_type="custom_emoji"
            )
        except TelegramRetryAfter as e:
            await asyncio.sleep(e.retry_after)
            await bot.create_new_sticker_set(
                user_id=uid,
                name=pack_name,
                title=title,
                stickers=[first],
                sticker_type="custom_emoji"
            )
        
        # остальные
        for i, p in enumerate(parts[1:], start=2):
            try:
                s = InputSticker(
                    sticker=FSInputFile(p),
                    emoji_list=["🧩"],
                    format=fmt
                )
                await bot.add_sticker_to_set(
                    user_id=uid,
                    name=pack_name,
                    sticker=s
                )
                
                if i % 5 == 0:
                    await asyncio.sleep(0.5)
                    
            except TelegramRetryAfter as e:
                log.warning(f"флуд, жду {e.retry_after}")
                await asyncio.sleep(e.retry_after)
                await bot.add_sticker_to_set(user_id=uid, name=pack_name, sticker=s)
            except Exception as e:
                log.error(f"ошибка добавления {i}: {e}")
        
        # получаем id эмодзи для копирования
        pack = await bot.get_sticker_set(pack_name)
        
        lines = []
        full_txt = ""
        
        if add_prev:
            if pack.stickers:
                full_txt = f'<tg-emoji emoji-id="{pack.stickers[0].custom_emoji_id}">🖼</tg-emoji>'
            idx = 1
        else:
            idx = 0
        
        for row in range(r):
            row_e = []
            for col in range(c):
                if idx < len(pack.stickers):
                    e = pack.stickers[idx]
                    row_e.append(f'<tg-emoji emoji-id="{e.custom_emoji_id}">🧩</tg-emoji>')
                idx += 1
            lines.append("".join(row_e))
        
        grid = "\n".join(lines)
        
        # результат
        cnt = f"{len(parts)} (1 превью + {c*r})" if add_prev else str(len(parts))
        
        await bot.send_message(
            uid,
            f"<b>готово!</b>\n\n"
            f"название: <b>{title}</b>\n"
            f"эмодзи: {cnt}\n"
            f"размер: {c}x{r}\n\n"
            f"<a href='https://t.me/addemoji/{pack_name}'>добавить пак</a>",
            parse_mode="HTML"
        )
        
        # сетка для копирования
        if add_prev and full_txt:
            grid_msg = f"<b>скопируй:</b>\n\nпревью: {full_txt}\n\n{grid}"
        else:
            grid_msg = f"<b>скопируй:</b>\n\n{grid}"
        
        await bot.send_message(uid, grid_msg, parse_mode="HTML")
        
    except Exception as e:
        log.error(f"ошибка для {uid}: {e}")
        await bot.send_message(uid, "произошла ошибка, попробуй еще раз")
    finally:
        clear_user(uid)
        users.rm(uid)


async def worker(bot: Bot):
    log.info("воркер запущен")
    
    while True:
        try:
            uid, (c, r) = await queue.get()
            log.info(f"задача {uid}: {c}x{r}")
            
            await do_task(bot, uid, c, r)
            
            queue.task_done()
            
        except asyncio.CancelledError:
            log.info("воркер остановлен")
            break
        except Exception as e:
            log.error(f"ошибка воркера: {e}")
            await asyncio.sleep(1)
