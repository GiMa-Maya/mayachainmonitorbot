import logging
from typing import List

from semver import VersionInfo

from localization import BaseLocalization
from services.jobs.fetch.base import INotified
from services.lib.config import SubConfig
from services.lib.cooldown import Cooldown
from services.lib.date_utils import parse_timespan_to_seconds
from services.lib.depcont import DepContainer
from services.models.node_info import NodeSetChanges, ZERO_VERSION


class VersionNotifier(INotified):
    def __init__(self, deps: DepContainer):
        self.deps = deps
        self.logger = logging.getLogger(self.__class__.__name__)

        cfg: SubConfig = deps.cfg.node_info.version

        cd_activate_sec = parse_timespan_to_seconds(str(cfg.get('version_activates', '1h')))
        self.cd_activate_version = Cooldown(deps.db, 'activate_version', cd_activate_sec)

        cd_new_ver_sec = parse_timespan_to_seconds(str(cfg.get('new_version_appears', '1h')))
        self.cd_new_version = Cooldown(deps.db, 'new_version', cd_new_ver_sec)

    DB_KEY_NEW_VERSION = 'THORNode.Version.Already.Notified.As.New'

    async def _find_new_versions(self, data: NodeSetChanges) -> List[VersionInfo]:
        old_ver_set = data.version_set(data.nodes_previous)
        new_ver_set = data.version_set(data.nodes_all)
        new_versions = new_ver_set - old_ver_set

        if new_versions:
            if not await self.cd_new_version.can_do():
                return []

            r = await self.deps.db.get_redis()

            # filter out known ones
            versions_to_announce = []
            for new_v in new_versions:
                was_notified = await r.sismember(self.DB_KEY_NEW_VERSION, str(new_v))
                if not was_notified:
                    versions_to_announce.append(new_v)

            return list(sorted(versions_to_announce))
        else:
            return []

    async def _mark_as_known(self, string_versions):
        r = await self.deps.db.get_redis()
        for v in string_versions:
            await r.sadd(self.DB_KEY_NEW_VERSION, v)

    @staticmethod
    def _test_active_version_changed(data: NodeSetChanges):
        previous_active_version = data.minimal_active_version(data.previous_active_only_nodes)
        current_active_version = data.minimal_active_version(data.active_only_nodes)
        if previous_active_version != ZERO_VERSION and current_active_version != ZERO_VERSION:
            if previous_active_version != current_active_version:
                return previous_active_version, current_active_version

        return None, None  # no change

    async def on_data(self, sender, data: NodeSetChanges):
        new_versions = await self._find_new_versions(data)

        old_active_ver, new_active_ver = self._test_active_version_changed(data)
        activated_version_alert = old_active_ver != new_active_ver

        if activated_version_alert or new_versions:
            await self.deps.broadcaster.notify_preconfigured_channels(
                self.deps.loc_man,
                BaseLocalization.notification_text_version_upgrade,
                data,
                new_versions,
                old_active_ver,
                new_active_ver
            )

        if new_versions:
            await self._mark_as_known(new_versions)
            await self.cd_new_version.do()

        if activated_version_alert:
            await self.cd_activate_version.do()
