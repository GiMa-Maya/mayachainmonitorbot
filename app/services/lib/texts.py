import itertools
from dataclasses import dataclass
from enum import Enum
from urllib.parse import urlparse

from aiogram.types import KeyboardButton, ReplyKeyboardMarkup

from services.lib.money import pretty_money, format_percent


class MessageType(Enum):
    TEXT = 'text'
    STICKER = 'sticker'
    PHOTO = 'photo'


@dataclass
class BoardMessage:
    text: str
    message_type: MessageType = MessageType.TEXT
    photo: str = None

    @classmethod
    def make_photo(cls, photo, caption=''):
        return cls(caption, MessageType.PHOTO, photo)


def bold(text):
    return f"<b>{text}</b>"


def link(url, text):
    return f'<a href="{url}">{text}</a>'


def link_with_domain_text(url):
    parsed_uri = urlparse(url)
    text = parsed_uri.netloc
    return f'<a href="{url}">{text}</a>'


def code(text):
    return f"<code>{text}</code>"


def ital(text):
    return f"<i>{text}</i>"


def pre(text):
    return f"<pre>{text}</pre>"


def x_ses(one, two):
    if one == 0 or two == 0:
        return 'N/A'
    else:
        sign = 'x' if two > one else '-x'
        times = two / one if two > one else one / two
        return f'{sign}{pretty_money(times)}'


def progressbar(x, total, symbol_width=10):
    if total <= 0:
        s = 0
    else:
        s = int(round(symbol_width * x / total))
    s = max(0, s)
    s = min(symbol_width, s)
    return '▰' * s + '▱' * (symbol_width - s)


def grouper(n, iterable):
    args = [iter(iterable)] * n
    return ([e for e in t if e is not None] for t in itertools.zip_longest(*args))


def kbd(buttons, resize=True, vert=False, one_time=False, row_width=3):
    if isinstance(buttons, str):
        buttons = [[buttons]]
    elif isinstance(buttons, (list, tuple, set)):
        if all(isinstance(b, str) for b in buttons):
            if vert:
                buttons = [[b] for b in buttons]
            else:
                buttons = [buttons]

    buttons = [
        [KeyboardButton(b) for b in row] for row in buttons
    ]
    return ReplyKeyboardMarkup(buttons,
                               resize_keyboard=resize,
                               one_time_keyboard=one_time,
                               row_width=row_width)


def cut_long_text(text: str, max_symbols=15, end='...'):
    end_len, text_len = len(end), len(text)
    if text_len > max_symbols - end_len:
        cut = max_symbols - end_len
        return text[:cut] + end
    else:
        return text


def bracketify(item):
    return f"({item})" if item else ''


def up_down_arrow(old_value, new_value, smiley=False, more_is_better=True, same_result='',
                  int_delta=False, money_delta=False, percent_delta=False, signed=True,
                  money_prefix='', ignore_on_no_old=True, postfix=''):
    if ignore_on_no_old and not old_value:
        return same_result

    delta = new_value - old_value

    if delta == 0:
        return same_result

    better = delta > 0 if more_is_better else delta < 0

    smiley = ('😃' if better else '🙁') if smiley else ''
    arrow = '↑' if better else '↓'

    delta_text = ''
    if int_delta:
        sign = ('+' if delta >= 0 else '') if signed else ''
        delta_text = f"{sign}{int(delta)}"
    elif money_delta:
        delta_text = pretty_money(delta, money_prefix, signed)
    elif percent_delta:
        delta_text = format_percent(delta, old_value, signed)

    return f"{smiley} {arrow} {delta_text}{postfix}".strip()


def plural(n: int, one_thing, many_things):
    return one_thing if n == 1 else many_things


def join_as_numbered_list(items, sep='\n', start=1):
    en_items = (f'{i}. {text!s}' for i, text in enumerate(items, start=start))
    return sep.join(en_items)
