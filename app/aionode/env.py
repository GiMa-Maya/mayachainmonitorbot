from copy import copy
from dataclasses import dataclass


@dataclass
class MayaEnvironment:
    seed_url: str = ''
    midgard_url: str = ''
    mayanode_url: str = ''
    rpc_url: str = ''

    timeout: float = 6.0

    retries: int = 1
    retry_delay: float = 0.0

    path_queue: str = '/mayachain/queue'
    path_nodes_height: str = '/mayachain/nodes?height={height}'
    path_nodes: str = '/mayachain/nodes'
    path_pools: str = "/mayachain/pools"
    path_pools_height: str = "/mayachain/pools?height={height}"
    path_pool: str = "/mayachain/pool/{pool}"
    path_pool_height: str = "/mayachain/pool/{pool}?height={height}"

    path_last_blocks: str = "/mayachain/lastblock"
    path_constants: str = "/mayachain/constants"
    path_mimir: str = "/mayachain/mimir"
    path_mimir_nodes: str = '/mayachain/mimir/nodes'
    path_mimir_votes: str = '/mayachain/mimir/nodes_all'
    path_inbound_addresses: str = "/mayachain/inbound_addresses"
    path_vault_yggdrasil: str = "/mayachain/vaults/yggdrasil"
    path_vault_asgard: str = "/mayachain/vaults/asgard"
    path_balance: str = '/cosmos/bank/v1beta1/balances/{address}'
    path_supply: str = '/cosmos/bank/v1beta1/supply'
    path_block_by_height: str = '/block?height={height}'
    path_tx_by_hash: str = '/cosmos/tx/v1beta1/txs/{hash}'
    path_tx_by_hash_old: str = '/tx?hash={hash}'
    path_tx_search: str = '/tx_search?query={query}&prove={prove}&page={page}&per_page={per_page}&order_by={order_by}'

    path_genesis: str = '/genesis'
    path_status: str = '/status?'

    path_liq_provider_details = '/mayachain/pool/{asset}/liquidity_provider/{address}?height={height}'
    path_liq_providers = '/mayachain/pool/{asset}/liquidity_providers?height={height}'

    path_saver_details = '/mayachain/pool/{asset}/saver/{address}?height={height}'
    path_savers = '/mayachain/pool/{asset}/savers?height={height}'
    path_pol = '/mayachain/pol?height={height}'
    path_network = '/mayachain/network?height={height}'

    path_block_results = '/block_results?height={height}'

    kind: str = ''

    def copy(self):
        return copy(self)

    def set_timeout(self, timeout):
        assert timeout > 0.0
        self.timeout = timeout
        return self

    def set_retries(self, retries=1, delay=0.0):
        assert retries >= 1
        self.retries = retries
        self.retry_delay = delay
        return self


class MayaURL:
    class MAYANode:
        PUBLIC = 'https://mayanode.mayachain.info'
        NINE_REALMS = 'https://mayanode.mayachain.info'
        THORSWAP = 'https://mayanode.mayachain.info'

        STAGENET = 'https://stagenet.mayanode.mayachain.info'
        TESTNET = 'https://testnet.thornode.thorchain.info'

    class RPC:
        PUBLIC = 'https://tendermint.mayachain.info'
        NINE_REALMS = 'https://tendermint.mayachain.info'
        THORSWAP = 'https://tendermint.mayachain.info'

        STAGENET = 'https://stagenet.tendermint.mayachain.info'
        TESTNET = 'https://testnet.rpc.thorchain.info/'

    class Midgard:
        PUBLIC = 'https://midgard.mayachain.info'
        NINE_REALMS = 'https://midgard.mayachain.info'
        THORSWAP = 'https://midgard.mayachain.info'

        STAGENET = 'https://stagenet.midgard.mayachain.info'
        TESTNET = 'https://testnet.midgard.thorchain.info'

    class Seed:
        MAINNET = 'https://seed.thorchain.info'
        TESTNET = 'https://testnet.seed.thorchain.info'


TEST_NET_ENVIRONMENT_MULTI_1 = MayaEnvironment(
    seed_url=MayaURL.Seed.TESTNET,
    midgard_url=MayaURL.Midgard.TESTNET,
    mayanode_url=MayaURL.MAYANode.TESTNET,
    rpc_url=MayaURL.RPC.TESTNET,
    kind='testnet',
)

MULTICHAIN_STAGENET_ENVIRONMENT = MayaEnvironment(
    midgard_url=MayaURL.Midgard.STAGENET,
    mayanode_url=MayaURL.MAYANode.STAGENET,
    rpc_url=MayaURL.RPC.STAGENET,
    kind='stagenet',
)

MAINNET_ENVIRONMENT = MayaEnvironment(
    seed_url=MayaURL.Seed.MAINNET,
    midgard_url=MayaURL.Midgard.NINE_REALMS,
    mayanode_url=MayaURL.MAYANode.NINE_REALMS,
    rpc_url=MayaURL.RPC.NINE_REALMS,
    kind='mainnet',
)

MULTICHAIN_MAINNET_9R_ENVIRONMENT = MayaEnvironment(
    seed_url=MayaURL.Seed.MAINNET,
    midgard_url=MayaURL.Midgard.NINE_REALMS,
    mayanode_url=mayaURL.MAYANode.NINE_REALMS,
    rpc_url=MayaURL.RPC.NINE_REALMS,
    kind='mainnet',
)

MULTICHAIN_MAINNET_THORSWAP_ENVIRONMENT = MayaEnvironment(
    seed_url=MayaURL.Seed.MAINNET,
    midgard_url=MayaURL.Midgard.THORSWAP,
    mayanode_url=MayaURL.MAYANode.THORSWAP,
    rpc_url=MayaURL.RPC.THORSWAP,
    kind='mainnet',
)

MAINNET = MAINNET_ENVIRONMENT  # alias
STAGENET = MULTICHAIN_STAGENET_ENVIRONMENT  # alias
MCTN = TEST_NET_ENVIRONMENT_MULTI_1  # alias
MCCN_9R = MULTICHAIN_MAINNET_9R_ENVIRONMENT  # alias
MCCN_THORSWAP = MULTICHAIN_MAINNET_THORSWAP_ENVIRONMENT  # alias

MAYANODE_PORT = 1317
TENDERMINT_RPC_PORT_TESTNET = 26657
TENDERMINT_RPC_PORT_MAINNET = 27147
