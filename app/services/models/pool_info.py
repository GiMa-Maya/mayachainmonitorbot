from dataclasses import dataclass
from typing import List, Dict, NamedTuple

from aiothornode.types import ThorPool

from services.lib.constants import THOR_DIVIDER_INV


def pool_share(rune_depth, asset_depth, my_units, pool_total_units):
    rune_share = (rune_depth * my_units) / pool_total_units
    asset_share = (asset_depth * my_units) / pool_total_units
    return rune_share, asset_share


@dataclass
class PoolInfo:
    asset: str

    balance_asset: int
    balance_rune: int
    pool_units: int

    status: str

    DEPRECATED_BOOTSTRAP = 'bootstrap'
    DEPREATED_ENABLED = 'enabled'
    AVAILABLE = 'available'  # enabled
    STAGED = 'staged'  # bootstrap

    def percent_share(self, runes):
        return runes / (2 * self.balance_rune * THOR_DIVIDER_INV) * 100.0

    def rune_share_of_pool(self, units) -> float:
        r, a = pool_share(self.balance_rune, self.balance_asset, my_units=units, pool_total_units=self.pool_units)
        return r * THOR_DIVIDER_INV

    def total_my_capital_of_pool_in_rune(self, units) -> float:
        return self.rune_share_of_pool(units) * 2.0

    @classmethod
    def dummy(cls):
        return cls('', 1, 1, 1, cls.DEPRECATED_BOOTSTRAP)

    @property
    def asset_per_rune(self):
        return self.balance_asset / self.balance_rune

    @property
    def runes_per_asset(self):
        return self.balance_rune / self.balance_asset

    @staticmethod
    def is_status_enabled(status):
        return status.lower() in (PoolInfo.DEPREATED_ENABLED, PoolInfo.AVAILABLE)  # v2 compatibility

    @property
    def is_enabled(self):
        return self.is_status_enabled(self.status)

    def usd_depth(self, dollar_per_rune):
        pool_depth_usd = 2 * self.balance_rune * THOR_DIVIDER_INV * dollar_per_rune  # note: * 2 as in off. frontend
        return pool_depth_usd

    @classmethod
    def from_dict(cls, j):
        balance_asset = int(j['balance_asset'])
        balance_rune = int(j['balance_rune'])
        return cls(asset=j['asset'],
                   balance_asset=balance_asset,
                   balance_rune=balance_rune,
                   pool_units=int(j['pool_units']),
                   status=str(j['status']).lower())

    def as_dict(self):
        return {
            'balance_asset': str(self.balance_asset),
            'balance_rune': str(self.balance_rune),
            'pool_units': str(self.pool_units),
            'asset': self.asset,
            'status': self.status
        }


@dataclass
class LPPosition:
    pool: str
    liquidity_units: int
    liquidity_total: int
    rune_balance: float
    asset_balance: float
    usd_per_rune: float
    usd_per_asset: float
    total_usd_balance: float

    @classmethod
    def create(cls, pool: PoolInfo, my_units: int, usd_per_rune: float):
        usd_per_asset = usd_per_rune / pool.asset_per_rune
        return cls(
            pool=pool.asset,
            liquidity_units=my_units,
            liquidity_total=pool.pool_units,
            rune_balance=pool.balance_rune * THOR_DIVIDER_INV,
            asset_balance=pool.balance_asset * THOR_DIVIDER_INV,
            usd_per_rune=usd_per_rune,
            usd_per_asset=usd_per_asset,
            total_usd_balance=pool.balance_rune * THOR_DIVIDER_INV * usd_per_rune * 2.0
        )


@dataclass
class PoolInfoHistoricEntry:
    asset_depth: int = 0
    rune_depth: int = 0
    asset_price: float = 0.0
    asset_price_usd: float = 0.0
    liquidity_units: int = 0
    timestamp: int = 0

    def to_pool_info(self, asset) -> PoolInfo:
        return PoolInfo(
            asset,
            self.asset_depth,
            self.rune_depth,
            self.liquidity_units,
            PoolInfo.DEPREATED_ENABLED
        )


PoolInfoMap = Dict[str, PoolInfo]


def parse_thor_pools(thor_pools: List[ThorPool]) -> PoolInfoMap:
    return {
        p.asset: PoolInfo(p.asset,
                          p.balance_asset_int, p.balance_rune_int,
                          p.pool_units_int, p.status)
        for p in thor_pools
    }


class PoolChange(NamedTuple):
    pool_name: str
    old_status: str
    new_status: str


class PoolChanges(NamedTuple):
    pools_added: List[PoolChange]
    pools_removed: List[PoolChange]
    pools_changed: List[PoolChange]

    @property
    def any_changed(self):
        return self.pools_changed or self.pools_added or self.pools_removed
