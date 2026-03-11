# -*- coding: utf-8 -*-
# клвавиатуры

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def sizes_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="3x3", callback_data="sz_3x3"),
            InlineKeyboardButton(text="5x5", callback_data="sz_5x5")
        ],
        [
            InlineKeyboardButton(text="8x8", callback_data="sz_8x8"),
            InlineKeyboardButton(text="10x10", callback_data="sz_10x10")
        ],
        [InlineKeyboardButton(text="✏️ Свой размер", callback_data="custom_sz")]
    ])


def vid_mode_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Анимированный", callback_data="vid_anim")],
        [InlineKeyboardButton(text="Статичный (1 кадр)", callback_data="vid_static")]
    ])


def cancel_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Отмена", callback_data="cancel")]
    ])


def preview_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Да, добавить оригинал", callback_data="prev_yes")],
        [InlineKeyboardButton(text="Нет, только пазл", callback_data="prev_no")]
    ])
