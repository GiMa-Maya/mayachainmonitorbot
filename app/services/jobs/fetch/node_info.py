from time import perf_counter
from typing import List

from services.jobs.fetch.base import BaseFetcher
from services.jobs.node_churn import NodeStateDatabase
from services.lib.date_utils import parse_timespan_to_seconds
from services.lib.depcont import DepContainer
from services.lib.geo_ip import GeoIPManager
from services.lib.midgard.urlgen import free_url_gen
from services.models.node_info import NodeInfo, NetworkNodeIpInfo


class NodeInfoFetcher(BaseFetcher):
    def __init__(self, deps: DepContainer):
        sleep_period = parse_timespan_to_seconds(deps.cfg.node_info.fetch_period)
        super().__init__(deps, sleep_period)

        self._geo_ip = GeoIPManager(self.deps)

    async def fetch_current_node_list(self) -> List[NodeInfo]:
        thor = self.deps.thor_connector
        # noinspection PyTypeChecker
        raw_nodes = await thor._request(thor.env.path_nodes, None)

        if raw_nodes is None:
            self.logger.warning(f'No luck trying to access THORNode, shall I try Midgard instead?')
            raw_nodes = await self.deps.midgard_connector.request_random_midgard(
                free_url_gen.url_thor_nodes()
            )

        if raw_nodes is None:
            self.logger.error('Again no luck! Failed to obtain node list!')
            raise FileNotFoundError('node_list')

        nodes = []
        for j in raw_nodes:
            node = NodeInfo.from_json(j)
            # node = self._dbg_node_magic(node)  # fixme: debug
            nodes.append(node)

        nodes.sort(key=lambda k: (k.status, -k.bond))

        # nodes = self._dbg_test_churn(nodes)  # fixme: debug
        return nodes

    async def fetch(self) -> List[NodeInfo]:
        nodes = await self.fetch_current_node_list()

        if nodes:
            try:
                await self.get_node_list_and_geo_info(nodes)
            except Exception as e:
                self.logger.exception(
                    f'get_node_list_and_geo_info failed ({e}), but it is not that bad, I will go on.', stack_info=True)

            self.deps.node_holder.nodes = nodes

        return nodes

    async def get_node_list_and_geo_info(self, node_list=None):
        if node_list is None:
            node_list = await self.fetch_current_node_list()

        ip_addresses = [node.ip_address for node in node_list if node.ip_address]

        t0 = perf_counter()
        self.logger.info(f'Requesting info for {len(ip_addresses)} IP addresses.')

        ip_info_dict = await self._geo_ip.get_ip_info_bulk_as_dict(ip_addresses)

        time_elapsed = perf_counter() - t0
        self.logger.info(f'Got {len(ip_info_dict)} IP address info pieces. It took: {time_elapsed:.3f} sec.')

        for node in node_list:
            node.ip_info = ip_info_dict.get(node.ip_address, {})

        return NetworkNodeIpInfo(
            node_list,
            ip_info_dict
        )

    async def post_action(self, info_list: List[NodeInfo]):
        await NodeStateDatabase(self.deps).save_node_info_list(info_list)
        self.logger.info(f'Saved previous state of {len(info_list)} nodes.')

        # fixme: debug(!) ------ 8< -------
        # from collections import defaultdict
        # chain_block_height = defaultdict(int)
        # for node in info_list:
        #     if not node.observe_chains:
        #         continue
        #     for chain_info in node.observe_chains:
        #         chain = chain_info['chain']
        #         height = int(chain_info['height'])
        #         if chain and height:
        #             chain_block_height[chain] = max(chain_block_height[chain], height)
        #     # chain_block_height[Chains.THOR].append(node.active_block_height) # todo!
        # print('my height (!)', chain_block_height)
        # fixme: debug(!) ------ 8< -------

    @staticmethod
    def _dbg_test_churn(new_nodes: List[NodeInfo]):
        """
        This is for debug purposes
        """
        import random

        n_changes = 0
        for i in range(100):
            node = new_nodes[random.randint(0, len(new_nodes))]
            if node.status == node.ACTIVE:
                node.status = node.STANDBY
                n_changes += 1
            elif node.status == node.STANDBY:
                node.status = node.ACTIVE
                n_changes += 1
            if n_changes >= 5:
                break

        return new_nodes

    @staticmethod
    def _dbg_node_magic(node):
        # if node.node_address == 'thor15tjtgxq7mz3ljwk0rzw6pvj43tz3xsv9f2wfzp':
        if node.node_address == 'thor15tjtgxq7mz3ljwk0rzw6pvj43tz3xsv9f2wfzp':
            # node.status = node.STANDBY
            node.version = '1.88.5'
            ...
            # node.ip_address = f'127.0.0.{random.randint(1, 255)}'
            # node.bond = 100000 + random.randint(0, 1000000)
            print('dyatel', node.node_address, node.bond)
        return node
