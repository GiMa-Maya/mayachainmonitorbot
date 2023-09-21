import sys
from typing import Any

import yaml
from aiothornode.env import ThorEnvironment, MAINNET, MULTICHAIN_STAGENET_ENVIRONMENT
from dotenv import load_dotenv

from services.lib.constants import NetworkIdents
from services.lib.date_utils import parse_timespan_to_seconds
from services.lib.utils import strip_trailing_slash


class SubConfig:
    def __init__(self, config_data):
        self._root_config = config_data

    def get(self, path: str = None, default=None, pure=False) -> 'SubConfig':
        if path is None or path == '':
            return self._root_config

        if isinstance(path, int):
            # single number => subscript of list
            components = [path]
        else:
            components = map(str.strip, path.split('.'))

        sub_config = self._root_config
        try:
            for component in components:
                if isinstance(sub_config, (list, tuple)):
                    sub_config = sub_config[int(component)]
                elif isinstance(sub_config, dict):
                    sub_config = sub_config[component]

            if isinstance(sub_config, (list, tuple, dict)):
                # collection => SubConfig(it)
                return (
                    sub_config if pure else SubConfig(sub_config)
                ) if default is None else sub_config
            else:
                # primitive => always pure!
                return sub_config
        except LookupError:
            # fixme: ?? print(e)
            if default is not None:
                return default
            else:
                raise LookupError(f'Config path "{path}" not found!')

    def get_pure(self, path=None, default=None) -> Any:
        return self.get(path, default, pure=True)

    def as_int(self, path: str = None, default=None):
        return int(self.get(path, default))

    def as_float(self, path: str = None, default=None):
        return float(self.get(path, default))

    def as_str(self, path: str = None, default=None):
        return str(self.get(path, default))

    def as_list(self, path: str = None, default=None):
        return list(self.get(path, default)._root_config)

    def as_interval(self, path: str = None, default=None):
        return parse_timespan_to_seconds(self.as_str(path, default))

    @property
    def as_seconds(self):
        return parse_timespan_to_seconds(self._root_config)

    def __int__(self):
        return int(self._root_config)

    def __float__(self):
        return float(self._root_config)

    def __str__(self):
        return str(self._root_config)

    def __getattr__(self, item) -> 'SubConfig':
        return self.get(item)

    def __getitem__(self, item) -> 'SubConfig':
        return self.get(item)


class Config(SubConfig):
    DEFAULT = '../config.yaml'
    DEFAULT_ENV_FILE = '.env'

    def __init__(self, name=None, data=None):
        load_dotenv(self.DEFAULT_ENV_FILE)

        if data is None:
            if name:
                self._config_name = name
            else:
                if len(sys.argv) >= 2 and 'pytest' not in sys.argv[0]:
                    self._config_name = sys.argv[1]
                else:
                    self._config_name = self.DEFAULT

            with open(self._config_name, 'r') as f:
                data = yaml.load(f, Loader=yaml.SafeLoader)

        super().__init__(data)

        self.network_id = self.get('thor.network_id', NetworkIdents.MAINNET)

    def get_thor_env_by_network_id(self, backup=False) -> ThorEnvironment:
        network_id = self.network_id

        if network_id == NetworkIdents.TESTNET_MULTICHAIN:
            raise Exception('No more Testnet! Please use the Stagenet')
        elif network_id in (NetworkIdents.CHAOSNET_MULTICHAIN, NetworkIdents.MAINNET):
            ref_env = MAINNET.copy()
            ref_env = self._load_custom_urls(ref_env, backup)
        elif network_id == NetworkIdents.STAGENET_MULTICHAIN:
            ref_env = MULTICHAIN_STAGENET_ENVIRONMENT.copy()
        else:
            raise KeyError('unsupported network ID!')

        return ref_env

    def _load_custom_urls(self, ref_env, backup):
        node_key = 'thor.node.backup_node_url' if backup else 'thor.node.node_url'
        node_url = self.as_str(node_key, '')
        if node_url:
            ref_env.thornode_url = strip_trailing_slash(node_url)

        rpc_url = self.as_str('thor.node.rpc_node_url', '')
        if rpc_url:
            ref_env.rpc_url = strip_trailing_slash(rpc_url)

        midgard_url = self.as_str('thor.midgard.public_url', '')
        if midgard_url:
            ref_env.midgard_url = strip_trailing_slash(midgard_url)
        return ref_env

    @property
    def first_admin_id(self):
        return self.get('telegram.admins')[0]
