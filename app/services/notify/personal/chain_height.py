from collections import defaultdict

from services.lib.constants import Chains
from services.lib.cooldown import CooldownBiTrigger, INFINITE_TIME
from services.lib.date_utils import parse_timespan_to_seconds, HOUR
from services.lib.depcont import DepContainer
from services.lib.utils import most_common
from services.models.node_info import NodeEvent, NodeEventType, EventBlockHeight
from services.models.thormon import ThorMonNodeTimeSeries, ThorMonAnswer, get_last_thormon_node_state
from services.notify.personal.helpers import BaseChangeTracker, NodeOpSetting


class ChainHeightTracker(BaseChangeTracker):
    def __init__(self, deps: DepContainer):
        self.deps = deps
        self.block_times = dict(deps.cfg.get_pure('blockchain.block_time', {}))
        for chain, en_time in self.block_times.items():
            self.block_times[chain] = parse_timespan_to_seconds(en_time)

        self.recent_max_blocks = {}

    def get_block_time(self, chain):
        return self.block_times.get(chain, Chains.block_time_default(chain))

    def blocks_to_lag(self, chain: str, seconds: float):
        return seconds / self.get_block_time(chain)

    @staticmethod
    def estimate_block_height_most_common(data: ThorMonAnswer):
        chain_block_height = defaultdict(list)
        for node in data.nodes:
            for name, chain_info in node.observe_chains.items():
                if chain_info.valid:
                    chain_block_height[name].append(chain_info.height)
            # chain_block_height[Chains.THOR].append(node.active_block_height) # todo!

        return {chain: most_common(height_list) for chain, height_list in chain_block_height.items()}

    @staticmethod
    def estimate_block_height_maximum(data: ThorMonAnswer):
        chain_block_height = defaultdict(int)
        for node in data.nodes:
            for name, chain_info in node.observe_chains.items():
                if chain_info.valid:
                    chain_block_height[name] = max(chain_block_height[name], chain_info.height)
            # chain_block_height[Chains.THOR].append(node.active_block_height) # todo!
        return chain_block_height

    def estimate_block_height(self, data: ThorMonAnswer, maximum=False):
        if maximum:
            self.recent_max_blocks = self.estimate_block_height_maximum(data)
        else:
            self.recent_max_blocks = self.estimate_block_height_most_common(data)

    async def get_node_events(self, node_address, telemetry: ThorMonNodeTimeSeries):
        if not node_address or not telemetry:
            return []

        events = []
        last_node_state = get_last_thormon_node_state(telemetry)

        for chain, expected_block_height in self.recent_max_blocks.items():
            actual = last_node_state.observe_chains.get(chain)
            actual_block_height = actual.height if actual else 0
            if actual_block_height == 0:
                continue

            is_ok = actual_block_height >= expected_block_height

            trigger = CooldownBiTrigger(self.deps.db,
                                        f'height.{chain}.{node_address}',
                                        cooldown_sec=INFINITE_TIME,
                                        switch_cooldown_sec=0,
                                        default=True)

            if await trigger.turn(is_ok):
                # the state has changed
                if is_ok:
                    ev_type = NodeEventType.BLOCK_HEIGHT_OK
                else:
                    ev_type = NodeEventType.BLOCK_HEIGHT_STUCK

                time_delay = abs(actual_block_height - expected_block_height) * self.get_block_time(chain)
                ev_data = EventBlockHeight(chain, expected_block_height, actual_block_height, time_delay, is_ok)

                events.append(NodeEvent(node_address, ev_type, ev_data, thor_node=last_node_state, tracker=self))

        return events

    async def is_event_ok(self, event: NodeEvent, settings: dict) -> bool:
        if not bool(settings.get(NodeOpSetting.CHAIN_HEIGHT_ON, True)):
            return False

        # fixme!

        if event.type == NodeEventType.BLOCK_HEIGHT_STUCK:
            threshold_interval = float(settings.get(NodeOpSetting.CHAIN_HEIGHT_INTERVAL, HOUR))
            return event.data.how_long_behind >= threshold_interval
        else:
            return True
