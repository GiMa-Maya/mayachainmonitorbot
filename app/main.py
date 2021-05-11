import asyncio
import logging
import os

import aiohttp
import ujson
from aiogram import Bot, Dispatcher, executor
from aiogram.types import *
from aiothornode.connector import ThorConnector

from localization import LocalizationManager
from services.dialog import init_dialogs
from services.jobs.fetch.cap import CapInfoFetcher
from services.jobs.fetch.const_mimir import ConstMimirFetcher
from services.jobs.fetch.gecko_price import fill_rune_price_from_gecko
from services.jobs.fetch.net_stats import NetworkStatisticsFetcher
from services.jobs.fetch.node_info import NodeInfoFetcher
from services.jobs.fetch.pool_price import PoolPriceFetcher, PoolInfoFetcherMidgard
from services.jobs.fetch.queue import QueueFetcher
from services.jobs.fetch.tx import TxFetcher
from services.jobs.pool_stats import PoolStatsUpdater
from services.lib.config import Config
from services.lib.constants import get_thor_env_by_network_id
from services.lib.db import DB
from services.lib.depcont import DepContainer
from services.lib.utils import setup_logs
from services.models.price import LastPriceHolder
from services.notify.broadcast import Broadcaster
from services.notify.types.cap_notify import LiquidityCapNotifier
from services.notify.types.node_churn_notify import NodeChurnNotifier
from services.notify.types.pool_churn import PoolChurnNotifier
from services.notify.types.price_notify import PriceNotifier
from services.notify.types.queue_notify import QueueNotifier
from services.notify.types.stats_notify import NetworkStatsNotifier
from services.notify.types.tx_notify import StakeTxNotifier


class App:
    def __init__(self):
        d = self.deps = DepContainer()
        d.cfg = Config()

        log_level = d.cfg.get_pure('log_level', logging.INFO)
        setup_logs(log_level)

        logging.info(f'Starting THORChainMonitoringBot for "{d.cfg.network_id}".')

        d.loop = asyncio.get_event_loop()
        d.db = DB(d.loop)

        d.price_holder = LastPriceHolder()

    def create_bot_stuff(self):
        d = self.deps

        d.bot = Bot(token=d.cfg.telegram.bot.token, parse_mode=ParseMode.HTML)
        d.dp = Dispatcher(d.bot, loop=d.loop)
        d.loc_man = LocalizationManager(d.cfg)
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

        ppf = d.price_pool_fetcher = PoolPriceFetcher(d)
        current_pools = await d.price_pool_fetcher.get_current_pool_data_full()
        if not current_pools:
            logging.error("no pool data at startup! halt it!")
            exit(-1)

        self.deps.price_holder.update(current_pools)

        fetcher_mimir = ConstMimirFetcher(d)
        self.deps.mimir_const_holder = fetcher_mimir
        await fetcher_mimir.fetch()  # get constants beforehand

        fetcher_cap = CapInfoFetcher(d)
        fetcher_tx = TxFetcher(d)
        fetcher_queue = QueueFetcher(d)
        fetcher_stats = NetworkStatisticsFetcher(d)
        fetcher_nodes = NodeInfoFetcher(d)
        fetcher_pool_info = PoolInfoFetcherMidgard(d)

        notifier_cap = LiquidityCapNotifier(d)
        notifier_tx = StakeTxNotifier(d)
        notifier_queue = QueueNotifier(d)
        notifier_price = PriceNotifier(d)
        notifier_pool_churn = PoolChurnNotifier(d)
        notifier_stats = NetworkStatsNotifier(d)
        notifier_nodes = NodeChurnNotifier(d)

        stats_updater = PoolStatsUpdater(d)
        stats_updater.subscribe(notifier_tx)
        fetcher_tx.subscribe(stats_updater)

        fetcher_cap.subscribe(notifier_cap)
        fetcher_queue.subscribe(notifier_queue)
        fetcher_stats.subscribe(notifier_stats)
        fetcher_nodes.subscribe(notifier_nodes)

        ppf.subscribe(notifier_price)
        fetcher_pool_info.subscribe(notifier_pool_churn)

        # await notifier_cap.test()
        # await notifier_stats.clear_cd()

        await asyncio.gather(*(task.run() for task in [
            ppf,
            fetcher_pool_info,
            fetcher_tx,
            fetcher_cap,
            fetcher_queue,
            fetcher_stats,
            fetcher_nodes,
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
