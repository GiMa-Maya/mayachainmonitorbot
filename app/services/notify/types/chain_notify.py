import json
import random
from typing import Dict, NamedTuple, List

from aionode.types import ThorChainInfo
from services.lib.delegates import INotified, WithDelegates
from services.lib.depcont import DepContainer
from services.lib.utils import WithLogger

EXCLUDE_CHAINS_FROM_HALTED = ('TERRA',)


class AlertChainHalt(NamedTuple):
    changed_chains: List[ThorChainInfo]


class TradingHaltedNotifier(INotified, WithDelegates, WithLogger):
    def __init__(self, deps: DepContainer):
        super().__init__()
        self.deps = deps
        # self.spam_cd = Cooldown(self.deps.db, 'TradingHalted', 30 * MINUTE)

    def _dbg_randomize_chain_dic_halted(self, data: Dict[str, ThorChainInfo]):
        for item in data.values():
            item.halted = random.uniform(0, 1) > 0.5
        return data

    async def on_data(self, sender, data: Dict[str, ThorChainInfo]):
        # data = self._dbg_randomize_chain_dic_halted(data)

        changed_chains = []

        # do not show Excluded chains
        data = {chain: v for chain, v in data.items() if chain not in EXCLUDE_CHAINS_FROM_HALTED}

        self.deps.chain_info = data

        for chain, new_info in data.items():
            new_info: ThorChainInfo
            if new_info.is_ok:
                old_info = await self._get_saved_chain_state(chain)
                if old_info and old_info.is_ok:
                    if old_info.halted != new_info.halted:
                        changed_chains.append(new_info)

                await self._save_chain_state(new_info)
                self._update_global_state(chain, new_info.halted)

        if changed_chains:
            await self.pass_data_to_listeners(AlertChainHalt(changed_chains))

    KEY_CHAIN_HALTED = 'Chain:LastInfo'

    def _update_global_state(self, chain, is_halted):
        if chain:
            halted_set = self.deps.halted_chains

            if chain in EXCLUDE_CHAINS_FROM_HALTED:
                is_halted = False  # do not show it

            if is_halted:
                halted_set.add(chain)
            elif chain in halted_set:
                halted_set.remove(chain)

    async def _get_saved_chain_state(self, chain):
        if not chain:
            self.logger.error('no "chain"!')
            return

        db = await self.deps.db.get_redis()
        raw_data = await db.hget(self.KEY_CHAIN_HALTED, chain)
        try:
            j = json.loads(raw_data)
            return ThorChainInfo.from_json(j)
        except (TypeError, ValueError):
            return None

    async def _save_chain_state(self, c: ThorChainInfo):
        if not c or not c.chain:
            self.logger.error('empty Chain Info')
            return

        data = json.dumps({
            'chain': c.chain,
            'pub_key': c.pub_key,
            'address': c.address,
            'router': c.router,
            'halted': c.halted,
            'gas_rate': c.gas_rate
        })

        db = await self.deps.db.get_redis()
        await db.hset(self.KEY_CHAIN_HALTED, c.chain, data)
