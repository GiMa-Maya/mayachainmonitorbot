import json

from aioredis import Redis

from services.jobs.scanner.swap_props import SwapProps
from services.lib.db import DB


class EventDatabase:
    def __init__(self, db: DB):
        self.db = db

    @staticmethod
    def key_to_tx(tx_id):
        return f'tx:tracker:{tx_id}'

    async def read_tx_status(self, tx_id) -> SwapProps:
        r: Redis = await self.db.get_redis()
        props = await r.hgetall(self.key_to_tx(tx_id))
        return SwapProps.restore_events_from_tx_status(props)

    @staticmethod
    def _convert_type(v):
        if isinstance(v, bool):
            return 1 if v else 0
        elif isinstance(v, (int, float, str, bytes)):
            return v
        else:
            try:
                return json.dumps(v)
            except TypeError:
                return str(v)

    async def write_tx_status(self, tx_id, mapping):
        if mapping:
            r: Redis = await self.db.get_redis()
            kwargs = {k: self._convert_type(v) for k, v in mapping.items()}
            await r.hset(self.key_to_tx(tx_id), mapping=kwargs)

    async def write_tx_status_kw(self, tx_id, **kwargs):
        await self.write_tx_status(tx_id, kwargs)