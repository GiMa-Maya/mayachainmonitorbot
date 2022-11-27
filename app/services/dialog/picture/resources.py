import os.path

from PIL import Image, ImageFont

from services.dialog.picture.crypto_logo import CryptoLogoDownloader
from services.lib.utils import Singleton


class FontCache(metaclass=Singleton):
    FONT_REGULAR = f'Exo2-Regular-Rune.ttf'
    FONT_BOLD = f'Exo2-Bold-Rune.ttf'

    def __init__(self, base_dir):
        self._cache = {}
        self._base_dir = base_dir

    def get_font(self, size: int, font=None):
        font = font or self.FONT_REGULAR
        key = f'{font}/{size}'
        f = self._cache.get(key)
        if not f:
            font_path = os.path.join(self._base_dir, font)
            f = self._cache[key] = ImageFont.truetype(font_path, size)
        return f


class Resources(metaclass=Singleton):
    BASE = './data'
    LOGO_BASE = './data/asset_logo'
    LOGO_WIDTH, LOGO_HEIGHT = 128, 128
    HIDDEN_IMG = f'{BASE}/hidden.png'
    BG_IMG = f'{BASE}/lp_bg.png'

    LOGO_FILE = f'{BASE}/tc_logo.png'

    def __init__(self) -> None:
        self.fonts = FontCache(self.BASE)
        self.hidden_img = Image.open(self.HIDDEN_IMG)
        self.hidden_img.thumbnail((200, 36))

        self._fonts_by_size = {}

        self.font_sum_ticks = self.fonts.get_font(24)
        self.font_small = self.fonts.get_font(28)
        self.font_semi = self.fonts.get_font(36)
        self.font = self.fonts.get_font(40)
        self.font_head = self.fonts.get_font(48)
        self.font_big = self.fonts.get_font(64)

        self.bg_image = Image.open(self.BG_IMG)

        self.tc_logo = Image.open(self.LOGO_FILE)

        self.logo_downloader = CryptoLogoDownloader(self.LOGO_BASE)

    def put_hidden_plate(self, image, position, anchor='left', ey=-3):
        x, y = position
        if anchor == 'right':
            x -= self.hidden_img.width
        elif anchor == 'center':
            x -= self.hidden_img.width // 2
        y -= self.hidden_img.height + ey
        image.paste(self.hidden_img, (x, y), self.hidden_img)
