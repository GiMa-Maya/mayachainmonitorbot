import logging
import time
from typing import List, Dict

from localization import LocalizationManager
from services.config import Config, DB
from services.fetch.tx import StakeTxFetcher
from services.models.tx import StakeTx, StakePoolStats
from services.notify.broadcast import Broadcaster, telegram_chats_from_config


class StakeTxNotifier(StakeTxFetcher):
    MAX_TX_PER_ONE_TIME = 10

    def __init__(self, cfg: Config, db: DB, broadcaster: Broadcaster, loc_man: LocalizationManager):
        super().__init__(cfg, db)
        self.broadcaster = broadcaster
        self.loc_man = loc_man

        scfg = cfg.tx.stake_unstake
        self.threshold_mult = float(scfg.threshold_mult)
        self.avg_n = int(scfg.avg_n)
        self.max_age_sec = int(scfg.max_age_sec)
        self.min_usd_total = int(scfg.min_usd_total)

    def _filter_by_age(self, txs: List[StakeTx]):
        now = int(time.time())
        for tx in txs:
            if tx.date > now - self.max_age_sec:
                yield tx

    def _filter_large_txs(self, txs, threshold_factor=5.0, min_rune_volume=10000):
        for tx in txs:
            tx: StakeTx
            stats: StakePoolStats = self.pool_stat_map.get(tx.pool)
            if stats is not None:
                if tx.full_rune >= min_rune_volume and tx.full_rune >= stats.rune_avg_amt * threshold_factor:
                    yield tx

    async def on_new_txs(self, txs: List[StakeTx]):
        new_txs = self._filter_by_age(txs)

        runes_per_dollar = self.runes_per_dollar
        min_rune_volume = self.min_usd_total * runes_per_dollar

        large_txs = self._filter_large_txs(new_txs, self.threshold_mult, min_rune_volume)

        large_txs = list(large_txs)
        large_txs = large_txs[:self.MAX_TX_PER_ONE_TIME]

        self.logger.info(f"large_txs: {len(large_txs)}")

        if large_txs:
            user_lang_map = telegram_chats_from_config(self.cfg, self.loc_man)

            async def message_gen(chat_id):
                loc = user_lang_map[chat_id]
                texts = []
                for tx in large_txs:
                    pool = self.pool_stat_map.get(tx.pool)
                    pool_info = self.pool_info_map.get(tx.pool)
                    texts.append(loc.tx_text(tx, runes_per_dollar, pool, pool_info))
                return '\n\n'.join(texts)

            await self.broadcaster.broadcast(user_lang_map.keys(), message_gen)