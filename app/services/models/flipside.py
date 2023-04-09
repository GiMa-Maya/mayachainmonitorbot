from datetime import datetime
from typing import NamedTuple, List

from services.jobs.fetch.flipside import FSList, KEY_DATETIME
from services.lib.constants import STABLE_COIN_POOLS_ALL, thor_to_float
from services.models.pool_info import PoolInfoMap


class FSSwapVolume(NamedTuple):
    date: datetime
    swap_synth_volume_usd: float = 0.0
    swap_non_synth_volume_usd: float = 0.0
    swap_volume_usd: float = 0.0
    swap_volume_usd_cumulative: float = 0.0

    @classmethod
    def from_json(cls, j):
        return cls(
            j.get(KEY_DATETIME),
            float(j.get('SWAP_SYNTH_VOLUME_USD', 0.0)),
            float(j.get('SWAP_NON_SYNTH_VOLUME_USD', 0.0)),
            float(j.get('SWAP_VOLUME_USD', 0.0)),
            float(j.get('SWAP_VOLUME_USD_CUMULATIVE', 0.0)),
        )


class FSLockedValue(NamedTuple):
    date: datetime
    total_value_pooled: float = 0.0
    total_value_pooled_usd: float = 0.0
    total_value_bonded: float = 0.0
    total_value_bonded_usd: float = 0.0
    total_value_locked: float = 0.0
    total_value_locked_usd: float = 0.0

    @classmethod
    def from_json(cls, j):
        return cls(
            j.get(KEY_DATETIME),
            float(j.get('TOTAL_VALUE_POOLED', 0.0)),
            float(j.get('TOTAL_VALUE_POOLED_USD', 0.0)),
            float(j.get('TOTAL_VALUE_BONDED', 0.0)),
            float(j.get('TOTAL_VALUE_BONDED_USD', 0.0)),
            float(j.get('TOTAL_VALUE_LOCKED', 0.0)),
            float(j.get('TOTAL_VALUE_LOCKED_USD', 0.0)),
        )


class FSSwapCount(NamedTuple):
    date: datetime
    swap_count: int = 0
    unique_swapper_count: int = 0
    swap_count_cumulative: int = 0

    @classmethod
    def from_json(cls, j):
        return cls(
            j.get(KEY_DATETIME),
            int(j.get('SWAP_COUNT', 0)),
            int(j.get('UNIQUE_SWAPPER_COUNT', 0)),
            int(j.get('SWAP_COUNT_CUMULATIVE', 0)),
        )


class FSFees(NamedTuple):
    date: datetime
    liquidity_fees: float = 0.0
    liquidity_fees_usd: float = 0.0
    block_rewards: float = 0.0
    block_rewards_usd: float = 0.0
    pct_of_earnings_from_liq_fees: float = 0.0
    pct_30d_moving_average: float = 0.0
    total_earnings: float = 0.0
    total_earnings_usd: float = 0.0
    earnings_to_nodes: float = 0.0
    earnings_to_nodes_usd: float = 0.0
    earnings_to_pools: float = 0.0
    earnings_to_pools_usd: float = 0.0
    liquidity_fees_usd_cumulative: float = 0.0
    block_rewards_usd_cumulative: float = 0.0
    total_earnings_usd_cumulative: float = 0.0
    earnings_to_nodes_usd_cumulative: float = 0.0
    earnings_to_pools_usd_cumulative: float = 0.0

    @classmethod
    def from_json(cls, j):
        return cls(
            j.get(KEY_DATETIME),
            float(j.get('LIQUIDITY_FEES', 0.0)),
            float(j.get('LIQUIDITY_FEES_USD', 0.0)),
            float(j.get('BLOCK_REWARDS', 0.0)),
            float(j.get('BLOCK_REWARDS_USD', 0.0)),
            float(j.get('PCT_OF_EARNINGS_FROM_LIQ_FEES', 0.0)),
            float(j.get('PCT_30D_MOVING_AVERAGE', 0.0)),
            float(j.get('TOTAL_EARNINGS', 0.0)),
            float(j.get('TOTAL_EARNINGS_USD', 0.0)),
            float(j.get('EARNINGS_TO_NODES', 0.0)),
            float(j.get('EARNINGS_TO_NODES_USD', 0.0)),
            float(j.get('EARNINGS_TO_POOLS', 0.0)),
            float(j.get('EARNINGS_TO_POOLS_USD', 0.0)),
            float(j.get('LIQUIDITY_FEES_USD_CUMULATIVE', 0.0)),
            float(j.get('BLOCK_REWARDS_USD_CUMULATIVE', 0.0)),
            float(j.get('TOTAL_EARNINGS_USD_CUMULATIVE', 0.0)),
            float(j.get('EARNINGS_TO_NODES_USD_CUMULATIVE', 0.0)),
            float(j.get('EARNINGS_TO_POOLS_USD_CUMULATIVE', 0.0)),
        )


class FSAffiliateCollectors(NamedTuple):
    date: datetime
    label: str
    fee_usd: float = 0.0
    cumulative_fee_usd: float = 0.0
    fee_rune: float = 0.0
    cumulative_fee_rune: float = 0.0

    @classmethod
    def from_json(cls, j):
        return cls(
            j.get(KEY_DATETIME),
            j.get('LABEL', ''),
            float(j.get('FEE_USD', 0.0)),
            float(j.get('CUMULATIVE_FEE_USD', 0.0)),
            float(j.get('FEE_RUNE', 0.0)),
            float(j.get('CUMULATIVE_FEE_RUNE', 0.0)),
        )

    @classmethod
    def from_json_v2(cls, j):
        """[{"AFFILIATE":"TrustWallet","TOTAL_VOLUME_USD":7629531.47796143,"DAY":"2023-04-06"},...]"""
        return cls(
            j.get(KEY_DATETIME),
            j.get('AFFILIATE', ''),
            float(j.get('TOTAL_LIQUIDITY_FEES_USD', 0.0)),
            0, 0, 0
        )


class FSSwapRoutes(NamedTuple):
    date: datetime
    assets: str
    asset_from: str
    asset_to: str
    swap_count: int
    swap_volume: float
    usd_per_swap: float
    fee_per_swap: float

    @classmethod
    def from_json(cls, j):
        assets = j.get('ASSETS')
        asset_from, asset_to = assets.split(' to ', 2) if assets else ('', '')

        return cls(
            j.get(KEY_DATETIME),
            assets, asset_from, asset_to,
            int(j.get('SWAP_COUNT', 0)),
            float(j.get('SWAP_VOLUME', 0.0)),
            float(j.get('USD_PER_SWAP', 0.0)),
            float(j.get('FEE_PER_SWAP', 0.0)),
        )

    @classmethod
    def from_json_v2(cls, j):
        """[{"SWAP_PATH":"BTC.BTC <-> THOR.RUNE","TOTAL_VOLUME_USD":20045361.3515259,"DAY":"2023-04-06"},...]"""
        assets = j.get('SWAP_PATH')
        asset_from, asset_to = assets.split(' <-> ', 2) if assets else ('', '')

        return cls(
            j.get(KEY_DATETIME),
            assets, asset_from, asset_to,
            0,
            float(j.get('TOTAL_VOLUME_USD', 0.0)),
            0,
            0,
        )


class KeyStats(NamedTuple):
    date: datetime
    affiliates: List[FSAffiliateCollectors]
    fees: FSFees
    swappers: FSSwapCount
    volume: FSSwapVolume
    locked: FSLockedValue
    pools: PoolInfoMap


class EventKeyStats(NamedTuple):
    series: FSList
    previous_pools: PoolInfoMap
    current_pools: PoolInfoMap

    routes: List[FSSwapRoutes]
    affiliates: List[FSAffiliateCollectors]
    prev_affiliates: List[FSAffiliateCollectors]

    days: int = 7

    @property
    def end_date(self):
        return self.series.latest_date

    def get_stables_sum(self, previous=False):
        return self.get_sum(STABLE_COIN_POOLS_ALL, previous)

    def get_sum(self, coin_list, previous=False):
        source = self.previous_pools if previous else self.current_pools
        running_sum = 0.0

        for symbol in coin_list:
            pool = source.get(symbol)
            if pool:
                running_sum += pool.balance_asset
        return thor_to_float(running_sum)
