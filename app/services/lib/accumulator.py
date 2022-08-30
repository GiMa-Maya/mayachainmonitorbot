import asyncio

from services.lib.date_utils import now_ts
from services.lib.db import DB
from services.lib.utils import take_closest


class Accumulator:
    def __init__(self, name, db: DB, tolerance: float):
        self.name = name
        self.db = db
        self.tolerance = tolerance

    def key(self, k):
        return f'Accum:{self.name}:{k}'

    def key_from_ts(self, ts):
        k = int(ts // self.tolerance * self.tolerance)
        return self.key(k)

    async def add(self, ts, **kwargs):
        accum_key = self.key_from_ts(ts)
        for k, v in kwargs.items():
            await self.db.redis.hincrbyfloat(accum_key, k, v)

    async def add_now(self, **kwargs):
        await self.add(now_ts(), **kwargs)

    async def set(self, ts, **kwargs):
        accum_key = self.key_from_ts(ts)
        for k, v in kwargs.items():
            await self.db.redis.hset(accum_key, k, v)

    async def get(self, timestamp=None, conv_to_float=True):
        timestamp = timestamp or now_ts()
        r = await self.db.redis.hgetall(self.key_from_ts(timestamp))
        return self._convert_values_to_float(r) if conv_to_float else r

    @staticmethod
    def _prepare_ts(start_ts: float, end_ts: float = None):
        if end_ts is None:
            end_ts = now_ts()
        if start_ts < 0:
            start_ts += now_ts()

        if end_ts < start_ts:
            end_ts, start_ts = start_ts, end_ts

        return start_ts, end_ts

    async def get_range(self, start_ts: float, end_ts: float = None, conv_to_float=True):
        start_ts, end_ts = self._prepare_ts(start_ts, end_ts)

        timestamps = []
        ts = end_ts
        while ts > start_ts:
            timestamps.append(ts)
            ts -= self.tolerance

        if not timestamps:
            return {}

        results = await asyncio.gather(*(self.get(ts, conv_to_float) for ts in timestamps))
        return dict(zip(timestamps, results))

    async def get_range_n(self, start_ts: float, end_ts: float = None, conv_to_float=True, n=10):
        assert n >= 2

        start_ts, end_ts = self._prepare_ts(start_ts, end_ts)

        points = await self.get_range(start_ts, end_ts, conv_to_float)
        real_time_points = list(points.keys())
        dt = (end_ts - start_ts) / (n - 1)

        results = []

        for step in range(n):
            ts = start_ts + dt * step
            closest_ts = take_closest(real_time_points, ts)
            results.append(
                (ts, points[closest_ts])
            )

        return results


    @staticmethod
    def _convert_values_to_float(r: dict):
        return {k: float(v) for k, v in r.items()}

    async def all_my_keys(self):
        return await self.db.redis.keys(self.key('*'))

    async def clear(self, before=None):
        keys = await self.all_my_keys()
        if before:
            keys = [k for k in keys if int(k.split(':')[-1]) < before]
        if keys:
            await self.db.redis.delete(*keys)
        return len(keys)
