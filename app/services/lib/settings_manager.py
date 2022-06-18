import ujson

from services.lib.config import Config
from services.lib.db import DB
from services.lib.db_one2one import OneToOne
from services.lib.delegates import INotified, WithDelegates
from services.lib.utils import class_logger, random_hex
from services.models.node_watchers import AlertWatchers
from services.notify.channel import Messengers, ChannelDescriptor
from services.notify.personal.helpers import NodeOpSetting, GeneralSettings


class SettingsManager(WithDelegates):
    TOKEN_LEN = 16

    KEY_MESSENGER = '_messenger'

    def __init__(self, db: DB, cfg: Config):
        super().__init__()
        self.db = db
        self.cfg = cfg
        self.public_url = cfg.as_str('web.public_url').rstrip('/')
        self.logger = class_logger(self)
        self.token_channel_db = OneToOne(db, 'Token-Channel')

    def get_link(self, token):
        return f'{self.public_url}/?token={token}'

    @staticmethod
    def db_key_settings(channel_id):
        return f'Settings:Data:{channel_id}'

    async def generate_new_token(self, channel_id: str):
        await self.revoke_token(channel_id)
        token = random_hex(self.TOKEN_LEN).decode()
        await self.token_channel_db.put(channel_id, token)
        return token

    async def revoke_token(self, channel_id: str):
        await self.token_channel_db.delete(channel_id)

    def _parse_settings(self, data):
        return ujson.loads(data) if data else {}

    async def get_settings(self, channel_id: str):
        if not channel_id:
            return {}
        data = await self.db.redis.get(self.db_key_settings(channel_id))
        return self._parse_settings(data)

    async def get_settings_multi(self, channels_ids):
        channels_ids = [cid for cid in channels_ids if cid]
        if not channels_ids:
            return {}
        channels_keys = [self.db_key_settings(cid) for cid in channels_ids]
        data_chunks = await self.db.redis.mget(keys=channels_keys)
        return {
            cid: self._parse_settings(data)
            for cid, data in zip(channels_ids, data_chunks)
        }

    @classmethod
    def set_messenger_data(cls, settings: dict, platform=Messengers.TELEGRAM, username='?', channel_name='?'):
        settings[cls.KEY_MESSENGER] = {
            'platform': platform,
            'username': username,
            'name': channel_name,
        }
        return settings

    @classmethod
    def get_platform(cls, settings: dict):
        messenger = settings.get(cls.KEY_MESSENGER, {})
        return messenger.get('platform', Messengers.TELEGRAM).lower()

    async def get_settings_from_token(self, token: str):
        channel = await self.token_channel_db.get(token)
        return await self.get_settings(channel)

    async def set_settings(self, channel_id: str, settings):
        if not channel_id:
            return

        if settings:
            await self.db.redis.set(self.db_key_settings(channel_id), ujson.dumps(settings))
            # additional processing
            await self.pass_data_to_listeners((channel_id, settings))
        else:
            await self.db.redis.delete(self.db_key_settings(channel_id))

    def get_context(self, user_id) -> 'SettingsContext':
        return SettingsContext(self, user_id)

    async def make_inactive(self, user):
        async with self.get_context(user) as context:
            if not context.is_inactive:
                context.stop()
            self.logger.warning(f'Auto-paused alerts for {user}! It is marked as "Inactive" now!')


class SettingsContext:
    def __init__(self, manager: SettingsManager, user_id):
        self.manager = manager
        self.user_id = user_id
        self._curr_settings = {}

    async def __aenter__(self):
        self._curr_settings = await self.manager.get_settings(self.user_id)
        return self

    async def __aexit__(self, exc_type, exc, tb):
        if exc_type is None:
            await self.manager.set_settings(self.user_id, self._curr_settings)

    def __setitem__(self, key, item):
        self._curr_settings[key] = item

    def __getitem__(self, key):
        return self._curr_settings[key]

    def __repr__(self):
        return repr(self._curr_settings)

    def __len__(self):
        return len(self._curr_settings)

    def __delitem__(self, key):
        del self._curr_settings[key]

    @property
    def is_inactive(self):
        return bool(self._curr_settings.get(GeneralSettings.INACTIVE, False))

    def stop(self):
        self.stop_s(self._curr_settings)

    def resume(self):
        self.resume_s(self._curr_settings)

    @staticmethod
    def stop_s(settings):
        settings[GeneralSettings.INACTIVE] = True

    @staticmethod
    def resume_s(settings):
        settings[GeneralSettings.INACTIVE] = False


class SettingsProcessorGeneralAlerts(INotified):
    def __init__(self, db: DB, alert_watcher: AlertWatchers):
        self.db = db
        self.logger = class_logger(self)
        self.alert_watcher = alert_watcher

    async def on_data(self, sender: SettingsManager, data):
        channel_id, settings = data
        await self._general_alerts_process(channel_id, settings)

    async def _general_alerts_process(self, channel_id: str, settings):
        platform = SettingsManager.get_platform(settings)
        if not platform:
            return

        is_general_enabled = settings.get(GeneralSettings.GENERAL_ALERTS, False)
        await self.alert_watcher.set_user_to_node(channel_id, GeneralSettings.GENERAL_ALERTS,
                                                  value=is_general_enabled)

    async def get_general_alerts_channels(self, settings_man: SettingsManager):
        channels = await self.alert_watcher.all_users_for_node(GeneralSettings.GENERAL_ALERTS)
        their_settings = await settings_man.get_settings_multi(channels)

        results = []
        for channel in channels:
            settings = their_settings.get(channel, {})

            if bool(settings.get(GeneralSettings.INACTIVE, False)):
                continue  # skip those who paused all the events.

            if bool(settings.get(NodeOpSetting.PAUSE_ALL_ON, False)):
                continue  # paused

            platform = SettingsManager.get_platform(settings)
            results.append(
                ChannelDescriptor(platform, channel)
            )
        return results
