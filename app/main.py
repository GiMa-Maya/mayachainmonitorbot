import asyncio
import logging
import os

import aiohttp
import ujson
from aiogram import Bot, Dispatcher, executor
from aiogram.types import *
from aiothornode.connector import ThorConnector
from aiothornode.types import TEST_NET_ENVIRONMENT_MULTI_1, CHAOS_NET_BNB_ENVIRONMENT, ThorEnvironment

from localization import LocalizationManager
from services.dialog import init_dialogs
from services.jobs.fetch.cap import CapInfoFetcher
from services.jobs.fetch.gecko_price import fill_rune_price_from_gecko
from services.jobs.fetch.pool_price import PoolPriceFetcher
from services.jobs.fetch.queue import QueueFetcher
from services.jobs.fetch.tx import TxFetcher
from services.lib.config import Config
from services.lib.constants import NetworkIdents
from services.lib.db import DB
from services.lib.depcont import DepContainer
from services.models.price import LastPriceHolder
from services.notify.broadcast import Broadcaster
from services.notify.types.cap_notify import CapFetcherNotifier
from services.notify.types.pool_churn import PoolChurnNotifier
from services.notify.types.price_notify import PriceNotifier
from services.notify.types.queue_notify import QueueNotifier
from services.notify.types.tx_notify import StakeTxNotifier


def get_thor_env_by_network_id(network_id) -> ThorEnvironment:
    if network_id == NetworkIdents.TESTNET_MULTICHAIN:
        return TEST_NET_ENVIRONMENT_MULTI_1.copy()
    elif network_id == NetworkIdents.CHAOSNET_BEP2CHAIN:
        return CHAOS_NET_BNB_ENVIRONMENT.copy()
    else:
        # todo: add multi-chain chaosnet
        raise KeyError('unsupported network ID!')


class App:
    def __init__(self):
        d = self.deps = DepContainer()
        d.cfg = Config()

        log_level = d.cfg.get('log_level', logging.INFO)
        logging.basicConfig(
            level=logging.getLevelName(log_level),
            format='%(asctime)s.%(msecs)03d %(levelname)s %(module)s - %(funcName)s: %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S',
        )

        logging.info('-' * 100)
        logging.info(f'Starting THORChainMonitoringBot for "{d.cfg.network_id}".')
        logging.info(f"Log level: {log_level}")

        d.loop = asyncio.get_event_loop()
        d.db = DB(d.loop)

        d.price_holder = LastPriceHolder()

    def create_bot_stuff(self):
        d = self.deps

        d.bot = Bot(token=d.cfg.telegram.bot.token, parse_mode=ParseMode.HTML)
        d.dp = Dispatcher(d.bot, loop=d.loop)
        d.loc_man = LocalizationManager()
        d.broadcaster = Broadcaster(d)

        init_dialogs(d)

    async def connect_chat_storage(self):
        if self.deps.dp:
            self.deps.dp.storage = await self.deps.db.get_storage()

    async def create_thor_node_connector(self):
        d = self.deps
        d.thor_connector = ThorConnector(get_thor_env_by_network_id(d.cfg.network_id), d.session)
        await d.thor_connector.update_nodes()

    async def _run_background_jobs(self):
        d = self.deps

        if 'REPLACE_RUNE_TIMESERIES_WITH_GECKOS' in os.environ:
            await fill_rune_price_from_gecko(d.db)

        self.ppf = PoolPriceFetcher(d)
        await self.ppf.get_current_pool_data_full()

        fetcher_cap = CapInfoFetcher(d, ppf=self.ppf)
        fetcher_tx = TxFetcher(d)
        fetcher_queue = QueueFetcher(d)

        notifier_cap = CapFetcherNotifier(d)
        notifier_tx = StakeTxNotifier(d)
        notifier_queue = QueueNotifier(d)
        notifier_price = PriceNotifier(d)
        notifier_pool_churn = PoolChurnNotifier(d)

        fetcher_cap.subscribe(notifier_cap)
        fetcher_tx.subscribe(notifier_tx)
        fetcher_queue.subscribe(notifier_queue)
        self.ppf.subscribe(notifier_price)
        self.ppf.subscribe(notifier_pool_churn)

        await asyncio.gather(*(task.run() for task in [
            self.ppf,
            fetcher_tx,
            fetcher_cap,
            fetcher_queue,
        ]))

    async def on_startup(self, _):
        await self.connect_chat_storage()

        self.deps.session = aiohttp.ClientSession(json_serialize=ujson.dumps)
        await self.create_thor_node_connector()

        asyncio.create_task(self._run_background_jobs())

    async def on_shutdown(self, _):
        await self.deps.session.close()

    def run_bot(self):
        self.create_bot_stuff()
        executor.start_polling(self.deps.dp, skip_updates=True, on_startup=self.on_startup,
                               on_shutdown=self.on_shutdown)


if __name__ == '__main__':
    App().run_bot()
