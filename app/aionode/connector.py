import asyncio
import logging
from typing import Dict

from aiohttp import ClientSession, ClientError, ServerDisconnectedError

from .env import MayaEnvironment
from .nodeclient import MayaNodeClient
from .types import *


class MayaConnector:
    # --- METHODS ----

    async def query_custom_path(self, path):
        data = await self._request(path)
        return data

    async def query_raw(self, path, is_rpc=False):
        return await self._request(path, is_rpc=is_rpc)

    async def query_node_accounts(self, height=0) -> List[MayaNodeAccount]:
        data = await self._request(self.env.path_nodes_height.format(height=int(height)))
        return [MayaNodeAccount.from_json(j) for j in data] if data else []

    async def query_queue(self) -> MayaQueue:
        data = await self._request(self.env.path_queue)
        return MayaQueue.from_json(data)

    async def query_pools(self, height=None) -> List[MayaPool]:
        if height:
            path = self.env.path_pools_height.format(height=height)
        else:
            path = self.env.path_pools
        data = await self._request(path, treat_empty_as_ok=False)
        return [MayaPool.from_json(j) for j in data]

    async def query_pool(self, pool: str, height=None) -> MayaPool:
        if height:
            path = self.env.path_pool_height.format(pool=pool, height=height)
        else:
            path = self.env.path_pool.format(pool=pool)
        data = await self._request(path)
        return MayaPool.from_json(data)

    async def query_last_blocks(self) -> List[MayaLastBlock]:
        data = await self._request(self.env.path_last_blocks)
        return [MayaLastBlock.from_json(j) for j in data] if isinstance(data, list) else [MayaLastBlock.from_json(data)]

    async def query_constants(self) -> MayaConstants:
        data = await self._request(self.env.path_constants)
        return MayaConstants.from_json(data) if data else MayaConstants()

    async def query_mimir(self) -> MayaMimir:
        data = await self._request(self.env.path_mimir)
        return MayaMimir.from_json(data) if data else MayaMimir()

    async def query_mimir_votes(self) -> List[MayaMimirVote]:
        response = await self._request(self.env.path_mimir_votes)
        mimirs = response.get('mimirs', [])
        return MayaMimirVote.from_json_array(mimirs)

    async def query_mimir_node_accepted(self) -> dict:
        response = await self._request(self.env.path_mimir_nodes)
        return response or {}

    async def query_chain_info(self) -> Dict[str, MayaChainInfo]:
        data = await self._request(self.env.path_inbound_addresses)
        if isinstance(data, list):
            info_list = [MayaChainInfo.from_json(j) for j in data]
        else:
            # noinspection PyUnresolvedReferences
            current = data.get('current', {})  # single-chain
            info_list = [MayaChainInfo.from_json(j) for j in current]
        return {info.chain: info for info in info_list}

    async def query_vault(self, vault_type=MayaVault.TYPE_ASGARD) -> List[MayaVault]:
        path = self.env.path_vault_asgard if vault_type == MayaVault.TYPE_ASGARD else self.env.path_vault_yggdrasil
        data = await self._request(path)
        return [MayaVault.from_json(v) for v in data]

    async def query_balance(self, address: str) -> MayaBalances:
        path = self.env.path_balance.format(address=address)
        data = await self._request(path)
        return MayaBalances.from_json(data, address)

    async def query_supply_raw(self):
        r = await self._request(self.env.path_supply)
        return r.get('supply') if r else None

    async def query_tendermint_block_raw(self, height):
        path = self.env.path_block_by_height.format(height=height)
        data = await self._request(path, is_rpc=True)
        return data

    async def query_block(self, height) -> MayaBalances:
        data = await self.query_tendermint_block_raw(height)
        return MayaBlock.from_json(data)

    async def query_native_tx(self, tx_hash: str, before_hard_fork=False):
        tx_hash = str(tx_hash)
        if not tx_hash.startswith('0x') and not tx_hash.startswith('0X'):
            tx_hash = f'0x{tx_hash}'

        path_pattern = self.env.path_tx_by_hash_old if before_hard_fork else self.env.path_tx_by_hash
        path = path_pattern.format(hash=tx_hash)
        data = await self._request(path, is_rpc=True)
        return MayaNativeTX.from_json(data)

    async def query_genesis(self):
        data = await self._request(self.env.path_genesis, is_rpc=True)
        return data['result']['genesis'] if data else None

    async def query_native_status_raw(self):
        return await self._request(self.env.path_status, is_rpc=True)

    async def query_native_block_results_raw(self, height):
        url = self.env.path_block_results.format(height=height)
        return await self._request(url, is_rpc=True)

    async def query_liquidity_providers(self, asset, height=0):
        url = self.env.path_liq_providers.format(asset=asset, height=height)
        data = await self._request(url)
        if data:
            return [MayaLiquidityProvider.from_json(p) for p in data]

    async def query_liquidity_provider(self, asset, address, height=0):
        url = self.env.path_liq_provider_details.format(asset=asset, height=height, address=address)
        data = await self._request(url)
        if data:
            return MayaLiquidityProvider.from_json(data)

    async def query_savers(self, asset, height=0):
        url = self.env.path_savers.format(asset=asset, height=height)
        data = await self._request(url)
        if data:
            return [MayaLiquidityProvider.from_json(p) for p in data]

    async def query_saver_details(self, asset, address, height=0):
        url = self.env.path_saver_details.format(asset=asset, height=height, address=address)
        data = await self._request(url)
        if data:
            return MayaLiquidityProvider.from_json(data)

    async def query_pol(self, height=0):
        url = self.env.path_pol.format(height=height)
        data = await self._request(url)
        if data:
            return MayaPOL.from_json(data)

    async def query_network(self, height=0):
        url = self.env.path_network.format(height=height)
        data = await self._request(url)
        if data:
            return MayaNetwork.from_json(data)

    # ---- Internal ----

    def __init__(self, env: MayaEnvironment, session: ClientSession, logger=None, extra_headers=None,
                 additional_envs=None, silent=True):
        self.session = session
        self.env = env
        self.silent = silent
        self.logger = logger or logging.getLogger(self.__class__.__name__)
        self._clients = [
            self._make_client(env, extra_headers)
        ]

        if additional_envs:
            if not isinstance(additional_envs, (list, tuple)):
                additional_envs = [additional_envs]

            for env in additional_envs:
                self._clients.append(self._make_client(env, extra_headers))

    def _make_client(self, env: MayaEnvironment, extra_headers):
        return MayaNodeClient(self.session, logger=self.logger, env=env,
                              extra_headers=extra_headers)

    def set_client_id_for_all(self, client_id):
        for client in self._clients:
            client.set_client_id_header(client_id)

    @property
    def first_client(self) -> MayaNodeClient:
        return self._clients[0]

    @property
    def first_client_node_url(self):
        return self.first_client.env.mayanode_url

    @property
    def first_client_rpc_url(self):
        return self.first_client.env.rpc_url

    async def _request(self, path, is_rpc=False, treat_empty_as_ok=True):
        for client in self._clients:
            for attempt in range(1, client.env.retries + 1):
                if attempt > 1:
                    self.logger.debug(f'Retry #{attempt} for path "{path}"')
                try:
                    data = await client.request(path, is_rpc=is_rpc)

                    if treat_empty_as_ok:
                        if data is not None:
                            return data
                    else:
                        if data:
                            # only non-empty data is considered as valid
                            return data
                        else:
                            # if data is empty and treat_empty_as_ok==False, try next client
                            break  # breaks the retry loop
                except NotImplementedError:
                    # Do no retries, no backups. Something is wrong with your code
                    raise
                except (FileNotFoundError, AttributeError,
                        ConnectionError, asyncio.TimeoutError,
                        ClientError, ServerDisconnectedError) as e:
                    if not self.silent:
                        raise
                    else:
                        err_type = type(e).__name__
                        self.logger.warning(f'#{attempt}. Failed to query {client} for "{path}" (err: {err_type}).')
                if d := client.env.retry_delay:
                    self.logger.debug(f'#{attempt}. Delay before retry: {d} sec...')
                    await asyncio.sleep(d)
