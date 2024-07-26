from PIL import Image

from services.lib.draw_utils import image_square_crop
from services.lib.utils import async_wrap

MAYA_AVA_FRAME_PATH = './data/maya_ava_frame.png'
MAYA_LASER_PATH = './data/laser_green_2.png'
MAYA_LASER_SIZE = 24


def combine_frame_and_photo(photo: Image.Image):
    frame = Image.open(MAYA_AVA_FRAME_PATH)

    photo = photo.resize(frame.size).convert('RGBA')
    result = Image.alpha_composite(photo, frame)

    return result


@async_wrap
def make_avatar(photo: Image.Image):
    photo = image_square_crop(photo)

    return combine_frame_and_photo(photo)


