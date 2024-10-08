import asyncio
import logging
import os

from localization.languages import Language
from services.dialog.picture.price_picture import price_graph_from_db
from services.dialog.twitter.twitter_bot import TwitterBot, TwitterBotMock
from services.lib.config import Config
from services.lib.date_utils import DAY
from services.lib.utils import setup_logs
from services.notify.channel import BoardMessage, ChannelDescriptor
from tools.debug.dbg_supply_graph import get_supply_pic
from tools.lib.lp_common import LpAppFramework, save_and_show_pic

MOCK = False


async def twitter_post_supply(app: LpAppFramework):
    pic, pic_name = await get_supply_pic(app)
    save_and_show_pic(pic, name='supply')

    loc = app.deps.loc_man[Language.ENGLISH_TWITTER]
    b_message = BoardMessage.make_photo(pic, loc.SUPPLY_PIC_CAPTION)

    await app.deps.broadcaster.notify_preconfigured_channels(b_message)


async def twitter_post_price(app: LpAppFramework):
    loc = app.deps.loc_man.default
    graph, graph_name = await price_graph_from_db(app.deps, loc, period=14 * DAY)

    await app.deps.broadcaster.notify_preconfigured_channels(
        BoardMessage.make_photo(graph, caption='Cacao price', photo_file_name=graph_name)
    )

    # await app.deps.broadcaster.notify_preconfigured_channels(
    #     BoardMessage('Test Twitter API v2')
    # )


async def main():
    setup_logs(logging.INFO)
    print(os.getcwd())
    # cfg = Config('../../../temp/twitter.yaml')
    cfg = Config('../../../config.yaml')
    twitter_bot = TwitterBotMock(cfg) if MOCK else TwitterBot(cfg)

    app = LpAppFramework()
    async with app(brief=True):
        # configure
        app.deps.twitter_bot = twitter_bot
        app.deps.twitter_bot.emergency = app.deps.emergency
        app.deps.broadcaster.channels = [
            ChannelDescriptor('twitter', '', Language.ENGLISH_TWITTER)
        ]
        r = await twitter_bot.verify_credentials()
        print(f'Verify: {r}')

        await asyncio.sleep(5.5)

        # await twitter_post_supply(app)

        # await twitter_bot.post('I want to make sure everything works.')
        await twitter_post_price(app)


if __name__ == '__main__':
    asyncio.run(main())
