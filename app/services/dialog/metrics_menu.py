from aiogram.dispatcher.filters.state import StatesGroup, State
from aiogram.types import *
from aiogram.utils.helper import HelperMode

from localization.manager import BaseLocalization
from services.dialog.base import BaseDialog, message_handler
from services.dialog.picture.block_height_picture import block_speed_chart
from services.dialog.picture.nodes_pictures import NodePictureGenerator
from services.dialog.picture.price_picture import price_graph_from_db
from services.dialog.picture.queue_picture import queue_graph
from services.dialog.picture.savers_picture import SaversPictureGenerator
from services.dialog.picture.supply_picture import SupplyPictureGenerator
from services.jobs.fetch.fair_price import RuneMarketInfoFetcher
from services.jobs.fetch.node_info import NodeInfoFetcher
from services.lib.constants import THOR_BLOCKS_PER_MINUTE
from services.lib.date_utils import DAY, HOUR, parse_timespan_to_seconds, now_ts
from services.lib.draw_utils import img_to_bio
from services.lib.texts import kbd
from services.models.node_info import NodeInfo
from services.models.price import PriceReport, RuneMarketInfo
from services.notify.types.best_pool_notify import BestPoolsNotifier
from services.notify.types.block_notify import BlockHeightNotifier
from services.notify.types.cap_notify import LiquidityCapNotifier
from services.notify.types.node_churn_notify import NodeChurnNotifier
from services.notify.types.price_notify import PriceNotifier
from services.notify.types.savers_stats_notify import EventSaverStats, SaversStatsNotifier
from services.notify.types.stats_notify import NetworkStatsNotifier
from services.notify.types.transfer_notify import RuneMoveNotifier


class MetricsStates(StatesGroup):
    mode = HelperMode.snake_case

    SECTION_FINANCE = State()
    SECTION_NET_OP = State()

    MAIN_METRICS_MENU = State()
    PRICE_SELECT_DURATION = State()
    QUEUE_SELECT_DURATION = State()
    DEX_AGGR_SELECT_DURATION = State()


class MetricsDialog(BaseDialog):
    # ----------- HANDLERS ------------

    @message_handler(state=MetricsStates.MAIN_METRICS_MENU)
    async def handle_main_state(self, message: Message):
        if message.text == self.loc.BUTTON_BACK:
            await self.go_back(message)
            return
        elif message.text == self.loc.BUTTON_METR_S_NET_OP:
            await self.on_menu_net_op(message)
        elif message.text == self.loc.BUTTON_METR_S_FINANCIAL:
            await self.on_menu_financial(message)
        else:
            await self.show_main_menu(message)

    async def show_main_menu(self, message: Message):
        await MetricsStates.MAIN_METRICS_MENU.set()
        reply_markup = kbd([
            [self.loc.BUTTON_METR_S_FINANCIAL, self.loc.BUTTON_METR_S_NET_OP],
            [self.loc.BUTTON_BACK],
        ])
        await message.answer(self.loc.TEXT_METRICS_INTRO,
                             reply_markup=reply_markup,
                             disable_notification=True)

    async def show_menu_financial(self, message: Message):
        await MetricsStates.SECTION_FINANCE.set()
        reply_markup = kbd([
            [self.loc.BUTTON_METR_PRICE, self.loc.BUTTON_METR_CAP, self.loc.BUTTON_METR_STATS],
            [self.loc.BUTTON_METR_SAVERS, self.loc.BUTTON_METR_TOP_POOLS, self.loc.BUTTON_METR_CEX_FLOW],
            [self.loc.BUTTON_METR_SUPPLY, self.loc.BUTTON_METR_DEX_STATS, self.loc.BUTTON_BACK],
        ])
        await message.answer(self.loc.TEXT_METRICS_INTRO,
                             reply_markup=reply_markup,
                             disable_notification=True)

    async def show_menu_net_op(self, message: Message):
        await MetricsStates.SECTION_NET_OP.set()
        reply_markup = kbd([
            [self.loc.BUTTON_METR_NODES, self.loc.BUTTON_METR_VOTING, self.loc.BUTTON_METR_MIMIR],
            [self.loc.BUTTON_METR_BLOCK_TIME, self.loc.BUTTON_METR_QUEUE, self.loc.BUTTON_METR_CHAINS],
            [self.loc.BUTTON_BACK],
        ])
        await message.answer(self.loc.TEXT_METRICS_INTRO,
                             reply_markup=reply_markup,
                             disable_notification=True)

    @message_handler(state=MetricsStates.SECTION_FINANCE)
    async def on_menu_financial(self, message: Message):
        if message.text == self.loc.BUTTON_BACK:
            await self.show_main_menu(message)
            return
        elif message.text == self.loc.BUTTON_METR_PRICE:
            await self.ask_price_info_duration(message)
            return
        elif message.text == self.loc.BUTTON_METR_CAP:
            await self.show_cap(message)
        elif message.text == self.loc.BUTTON_METR_STATS:
            await self.show_last_stats(message)
        elif message.text == self.loc.BUTTON_METR_SAVERS:
            await self.show_savers(message)
        elif message.text == self.loc.BUTTON_METR_TOP_POOLS:
            await self.show_top_pools(message)
        elif message.text == self.loc.BUTTON_METR_CEX_FLOW:
            await self.show_cex_flow(message)
        elif message.text == self.loc.BUTTON_METR_SUPPLY:
            await self.show_rune_supply(message)
        elif message.text == self.loc.BUTTON_METR_DEX_STATS:
            await self.ask_dex_aggr_duration(message)
            return
        await self.show_menu_financial(message)

    @message_handler(state=MetricsStates.SECTION_NET_OP)
    async def on_menu_net_op(self, message: Message):
        if message.text == self.loc.BUTTON_BACK:
            await self.show_main_menu(message)
            return
        elif message.text == self.loc.BUTTON_METR_QUEUE:
            await self.ask_queue_duration(message)
            return
        elif message.text == self.loc.BUTTON_METR_NODES:
            await self.show_node_list(message)
        elif message.text == self.loc.BUTTON_METR_CHAINS:
            await self.show_chain_info(message)
        elif message.text == self.loc.BUTTON_METR_MIMIR:
            await self.show_mimir_info(message)
        elif message.text == self.loc.BUTTON_METR_VOTING:
            await self.show_voting_info(message)
        elif message.text == self.loc.BUTTON_METR_BLOCK_TIME:
            await self.show_block_time(message)
        await self.show_menu_net_op(message)

    async def show_cap(self, message: Message):
        info = await LiquidityCapNotifier.get_last_cap_from_db(self.deps.db)
        await message.answer(self.loc.cap_message(info),
                             disable_web_page_preview=True,
                             disable_notification=True)

    async def show_savers(self, message: Message):
        loading_message = await self.show_loading(message)

        ssn = SaversStatsNotifier(self.deps)
        c_data = await ssn.get_previous_saver_stats(0)

        if not c_data:
            await message.answer(self.loc.TEXT_SAVERS_NO_DATA,
                                 disable_notification=True)
            return

        prev_data = await ssn.get_previous_saver_stats(DAY)
        event = EventSaverStats(
            prev_data, c_data, self.deps.price_holder
        )

        pic_gen = SaversPictureGenerator(self.loc, event)
        pic, name = await pic_gen.get_picture()

        await message.answer_photo(img_to_bio(pic, name),
                                   caption=self.loc.notification_text_saver_stats(event),
                                   disable_notification=True)

        await self.safe_delete(loading_message)

    async def show_last_stats(self, message: Message):
        nsn = NetworkStatsNotifier(self.deps)
        old_info = await nsn.get_previous_stats()
        new_info = self.deps.net_stats

        loc: BaseLocalization = self.loc
        if not new_info.is_ok:
            await message.answer(f"{loc.ERROR} {loc.NOT_READY}", disable_notification=True)
            return

        rune_market_info: RuneMarketInfo = await self.deps.rune_market_fetcher.get_rune_market_info()
        await message.answer(loc.notification_text_network_summary(
            old_info, new_info, rune_market_info, self.deps.killed_rune),
            disable_web_page_preview=True,
            disable_notification=True)

    async def show_node_list(self, message: Message):
        loading_message = await self.show_loading(message)

        node_fetcher = NodeInfoFetcher(self.deps)
        result_network_info = await node_fetcher.get_node_list_and_geo_info()  # todo: switch to NodeChurnDetector (DB)
        node_list = result_network_info.node_info_list

        active_node_messages = self.loc.node_list_text(node_list, NodeInfo.ACTIVE)
        standby_node_messages = self.loc.node_list_text(node_list, NodeInfo.STANDBY)
        other_node_messages = self.loc.node_list_text(node_list, 'others')

        await self.safe_delete(loading_message)

        for message_text in (active_node_messages + standby_node_messages + other_node_messages):
            if message_text:
                await message.answer(message_text, disable_web_page_preview=True, disable_notification=True)

        # generate a beautiful masterpiece :)
        chart_pts = await NodeChurnNotifier(self.deps).load_last_statistics(NodePictureGenerator.CHART_PERIOD)
        gen = NodePictureGenerator(result_network_info, chart_pts, self.loc)
        pic = await gen.generate()

        await message.answer_photo(img_to_bio(pic, gen.proper_name()), disable_notification=True)

    async def ask_queue_duration(self, message: Message):
        await message.answer(self.loc.TEXT_PRICE_INFO_ASK_DURATION, reply_markup=kbd([
            [
                self.loc.BUTTON_1_HOUR,
                self.loc.BUTTON_24_HOURS,
                self.loc.BUTTON_1_WEEK,
                self.loc.BUTTON_30_DAYS,
            ],
            [
                self.loc.BUTTON_BACK
            ]
        ]))
        await MetricsStates.QUEUE_SELECT_DURATION.set()

    def parse_duration_response(self, message: Message):
        if message.text == self.loc.BUTTON_1_HOUR:
            return HOUR
        elif message.text == self.loc.BUTTON_24_HOURS:
            return DAY
        elif message.text == self.loc.BUTTON_1_WEEK:
            return 7 * DAY
        elif message.text == self.loc.BUTTON_30_DAYS:
            return 30 * DAY
        elif message.text == self.loc.BUTTON_BACK:
            return  # back
        else:
            period = parse_timespan_to_seconds(message.text.strip())
            return period

    @message_handler(state=MetricsStates.QUEUE_SELECT_DURATION)
    async def on_queue_duration_answered(self, message: Message):
        period = self.parse_duration_response(message)
        if isinstance(period, str):
            await message.reply(period)
            return
        if not period:
            await self.show_menu_net_op(message)
            return
        await self.show_queue(message, period)

    async def show_queue(self, message, period):
        queue_info = self.deps.queue_holder
        plot, plot_name = await queue_graph(self.deps, self.loc, duration=period)
        if plot is not None:
            plot_bio = img_to_bio(plot, plot_name)
            await message.answer_photo(plot_bio, caption=self.loc.queue_message(queue_info), disable_notification=True)
        else:
            await message.answer(self.loc.queue_message(queue_info), disable_notification=True)

    @message_handler(state=MetricsStates.PRICE_SELECT_DURATION)
    async def on_price_duration_answered(self, message: Message, explicit_period=0):
        period = explicit_period or self.parse_duration_response(message)

        if not period:
            await self.show_menu_financial(message)
            return

        if isinstance(period, str):
            await message.reply(period)
            return

        market_info = await self.deps.rune_market_fetcher.get_rune_market_info()
        pn = PriceNotifier(self.deps)
        price_1h, price_24h, price_7d = await pn.historical_get_triplet()
        market_info.pool_rune_price = self.deps.price_holder.usd_per_rune
        btc_price = self.deps.price_holder.btc_per_rune

        price_text = self.loc.notification_text_price_update(PriceReport(
            price_1h, price_24h, price_7d,
            market_info=market_info,
            btc_pool_rune_price=btc_price),
            halted_chains=self.deps.halted_chains
        )

        graph, graph_name = await price_graph_from_db(self.deps, self.loc, period=period)
        await message.answer_photo(img_to_bio(graph, graph_name),
                                   disable_notification=True)
        await message.answer(price_text,
                             disable_web_page_preview=True,
                             disable_notification=True)

    async def ask_price_info_duration(self, message: Message):
        await message.answer(self.loc.TEXT_PRICE_INFO_ASK_DURATION, reply_markup=kbd([
            [
                self.loc.BUTTON_1_HOUR,
                self.loc.BUTTON_24_HOURS,
                self.loc.BUTTON_1_WEEK,
                self.loc.BUTTON_30_DAYS,
            ],
            [
                self.loc.BUTTON_BACK
            ]
        ]))
        await MetricsStates.PRICE_SELECT_DURATION.set()

    async def show_chain_info(self, message: Message):
        text = self.loc.text_chain_info(list(self.deps.chain_info.values()))
        await message.answer(text,
                             disable_web_page_preview=True,
                             disable_notification=True)

    async def show_mimir_info(self, message: Message):
        texts = self.loc.text_mimir_info(self.deps.mimir_const_holder)
        for text in texts:
            await message.answer(text,
                                 disable_web_page_preview=True,
                                 disable_notification=True)

    async def show_voting_info(self, message: Message):
        texts = self.loc.text_node_mimir_voting(self.deps.mimir_const_holder)
        for text in texts:
            await message.answer(text,
                                 disable_web_page_preview=True,
                                 disable_notification=True)

    async def show_block_time(self, message: Message):
        duration = 2 * DAY

        loading_message = await self.show_loading(message)

        block_notifier: BlockHeightNotifier = self.deps.block_notifier
        points = await block_notifier.get_block_time_chart(duration, convert_to_blocks_per_minute=True)

        # SLOW?
        chart, chart_name = await block_speed_chart(points, self.loc, normal_bpm=THOR_BLOCKS_PER_MINUTE,
                                                    time_scale_mode='time')
        last_block = block_notifier.last_thor_block
        last_block_ts = block_notifier.last_thor_block_update_ts

        recent_bps = await block_notifier.get_recent_blocks_per_second()
        state = await block_notifier.get_block_alert_state()

        d = now_ts() - last_block_ts if last_block_ts else 0

        # SLOW?
        await message.answer_photo(img_to_bio(chart, chart_name),
                                   caption=self.loc.text_block_time_report(last_block, d, recent_bps, state),
                                   disable_notification=True)
        await self.safe_delete(loading_message)

    async def show_top_pools(self, message: Message):
        notifier: BestPoolsNotifier = self.deps.best_pools_notifier
        text = self.loc.notification_text_best_pools(notifier.last_pool_detail, notifier.n_pools)
        await message.answer(text, disable_notification=True, disable_web_page_preview=True)

    async def show_cex_flow(self, message: Message):
        notifier: RuneMoveNotifier = self.deps.rune_move_notifier
        flow = await notifier.tracker.read_last24h()
        flow.usd_per_rune = self.deps.price_holder.usd_per_rune
        text = self.loc.notification_text_cex_flow(flow)
        await message.answer(text, disable_notification=True)

    async def show_rune_supply(self, message: Message):
        loading_message = await self.show_loading(message)

        market_fetcher: RuneMarketInfoFetcher = self.deps.rune_market_fetcher
        market_info = await market_fetcher.get_rune_market_info()

        text = self.loc.text_metrics_supply(market_info, self.deps.killed_rune)

        await message.answer(text, disable_notification=True)

        pic_gen = SupplyPictureGenerator(self.loc, market_info.supply_info, self.deps.killed_rune, self.deps.net_stats)
        pic, pic_name = await pic_gen.get_picture()

        await message.answer_photo(img_to_bio(pic, pic_name), disable_notification=True)

        await self.safe_delete(loading_message)

    async def ask_dex_aggr_duration(self, message: Message):
        await message.answer(self.loc.TEXT_DEX_AGGR_ASK_DURATION, reply_markup=kbd([
            [
                self.loc.BUTTON_1_HOUR,
                self.loc.BUTTON_24_HOURS,
                self.loc.BUTTON_1_WEEK,
                self.loc.BUTTON_30_DAYS,
            ],
            [
                self.loc.BUTTON_BACK
            ]
        ]))
        await MetricsStates.DEX_AGGR_SELECT_DURATION.set()

    @message_handler(state=MetricsStates.DEX_AGGR_SELECT_DURATION)
    async def on_dex_aggr_duration_answered(self, message: Message, explicit_period=0):
        period = explicit_period or self.parse_duration_response(message)

        if not period:
            await self.show_menu_financial(message)
            return

        if isinstance(period, str):
            await message.reply(period)
            return

        report = await self.deps.dex_analytics.get_analytics(period)
        text = self.loc.notification_text_dex_report(report)
        await message.answer(text,
                             disable_web_page_preview=True,
                             disable_notification=True)
