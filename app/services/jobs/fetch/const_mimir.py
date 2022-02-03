import asyncio
from typing import Tuple, List

from aiothornode.nodeclient import ThorNodePublicClient
from aiothornode.types import ThorConstants, ThorMimir

from services.jobs.fetch.base import BaseFetcher
from services.lib.date_utils import parse_timespan_to_seconds
from services.lib.depcont import DepContainer
from services.models.mimir import MimirVote

ATTEMPTS = 5


class ConstMimirFetcher(BaseFetcher):
    def __init__(self, deps: DepContainer):
        sleep_period = parse_timespan_to_seconds(deps.cfg.constants.fetch_period)
        super().__init__(deps, sleep_period)

    async def fetch_constants_midgard(self) -> ThorConstants:
        data = await self.deps.midgard_connector.request_random_midgard('/thorchain/constants')
        return ThorConstants.from_json(data)

    async def _request_public_node_client(self, path):
        client = ThorNodePublicClient(self.deps.session)
        for attempt in range(1, ATTEMPTS):
            response = await client.request(path)
            if response is not None:
                return response
            else:
                self.logger.warning(f'fail attempt "{path}": #{attempt}')
        raise Exception('failed to get THORNode data')

    async def fetch_constants_fallback(self) -> ThorConstants:
        response = await self._request_public_node_client('/thorchain/constants')
        return ThorConstants.from_json(response) if response else ThorConstants()

    async def fetch_mimir_fallback(self) -> ThorMimir:
        response = await self._request_public_node_client('/thorchain/mimir')
        return ThorMimir.from_json(response) if response else ThorMimir()

    async def fetch_node_mimir_votes(self) -> List[MimirVote]:
        response = await self._request_public_node_client('/thorchain/mimir/nodes_all')
        return MimirVote.from_json_array(response)

    async def fetch_node_mimir_results(self) -> dict:
        response = await self._request_public_node_client('/thorchain/mimir/nodes')
        return response or {}

    async def fetch(self) -> Tuple[ThorConstants, ThorMimir]:
        constants, mimir, node_mimir, votes = await asyncio.gather(
            self.fetch_constants_fallback(),
            self.fetch_mimir_fallback(),
            self.fetch_node_mimir_results(),
            self.fetch_node_mimir_votes(),
        )

        # last_mimir = self._dbg_randomize_mimir(last_mimir)  # fixme

        self.deps.mimir_const_holder.update(constants, mimir, node_mimir, votes)

        self.logger.info(f'Got {len(constants.constants)} CONST entries'
                         f' and {len(mimir.constants)} MIMIR entries.')
        return constants, mimir

    def _dbg_randomize_votes(self, votes: List[MimirVote]):
        return votes

    def _dbg_randomize_node_mimir_results(self, results):
        return results

    def _dbg_randomize_mimir(self, fresh_mimir: ThorMimir):
        # if random.uniform(0, 1) > 0.5:
        #     fresh_mimir.constants['LOKI_CONST'] = "555"
        # if random.uniform(0, 1) > 0.3:
        #     fresh_mimir.constants['LOKI_CONST'] = "777"
        # if random.uniform(0, 1) > 0.6:
        #     fresh_mimir.constants['NativeTransactionFee'] = 300000
        # if random.uniform(0, 1) > 0.3:
        #     try:
        #         del fresh_mimir.constants['NativeTransactionFee']
        #     except KeyError:
        #         pass
        # del fresh_mimir.constants["HALTBNBTRADING"]
        # fresh_mimir.constants["HALTETHTRADING"] = 0
        # fresh_mimir.constants["HALTBNBCHAIN"] = 1233243  # 1234568
        # del fresh_mimir.constants["EMISSIONCURVE"]
        # fresh_mimir.constants['NATIVETRANSACTIONFEE'] = 4000000
        # fresh_mimir.constants['MAXLIQUIDITYRUNE'] = 10000000000000 * random.randint(1, 99)
        # fresh_mimir.constants["FULLIMPLOSSPROTECTIONBLOCKS"] = 10000 * random.randint(1, 999)
        return fresh_mimir
