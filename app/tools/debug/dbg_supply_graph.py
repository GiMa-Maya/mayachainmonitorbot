import asyncio
import dataclasses
import os

from localization.languages import Language
from localization.manager import LocalizationManager
from services.dialog.picture.supply_picture import SupplyPictureGenerator
from services.jobs.fetch.killed_rune import KilledRuneFetcher
from services.jobs.fetch.net_stats import NetworkStatisticsFetcher
from services.lib.draw_utils import img_to_bio
from services.lib.utils import json_cached_to_file_async
from services.models.killed_rune import KilledRuneEntry
from services.models.net_stats import NetworkStats
from services.models.price import RuneMarketInfo
from tools.lib.lp_common import LpAppFramework


@json_cached_to_file_async("../temp/killed_rune.json")
async def get_killed_rune(app: LpAppFramework):
    krf = KilledRuneFetcher(app.deps)
    data = await krf.fetch()
    return data[0].__dict__


@json_cached_to_file_async("../temp/supply_info.json")
async def get_rune_supply(app: LpAppFramework):
    rune_market_info: RuneMarketInfo = await app.deps.rune_market_fetcher.get_rune_market_info()
    return dataclasses.asdict(rune_market_info.supply_info)


@json_cached_to_file_async("../temp/net_stats.json")
async def get_network_stats(app: LpAppFramework):
    ns_fetcher = NetworkStatisticsFetcher(app.deps)
    data = await ns_fetcher.fetch()
    return dataclasses.asdict(data)


async def get_supply_pic(app):
    loc_man: LocalizationManager = app.deps.loc_man
    loc = loc_man.get_from_lang(Language.ENGLISH)

    data = await get_killed_rune(app)
    killed_rune = KilledRuneEntry(**data)

    await app.deps.price_pool_fetcher.fetch()

    rune_market_info: RuneMarketInfo = await app.deps.rune_market_fetcher.get_rune_market_info()

    ns_raw = await get_network_stats(app)
    ns = NetworkStats(**ns_raw)

    pic_gen = SupplyPictureGenerator(loc, rune_market_info.supply_info, killed_rune, ns)

    return await pic_gen.get_picture()


def save_and_show_supply_pic(pic):
    filepath = '../temp/supply.png'
    with open(filepath, 'wb') as f:
        pic_bio = img_to_bio(pic, os.path.basename(filepath))
        f.write(pic_bio.getbuffer())

    os.system(f'open "{filepath}"')


async def run():
    app = LpAppFramework()
    async with app(brief=True):
        pic, _ = await get_supply_pic(app)
        save_and_show_supply_pic(pic)


if __name__ == '__main__':
    asyncio.run(run())
