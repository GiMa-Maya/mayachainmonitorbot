import logging

from localization import LocalizationManager
from services.config import Config
from services.fetch.cap import CapInfoFetcher
from services.models.cap_info import ThorInfo
from services.notify.broadcast import Broadcaster, telegram_chats_from_config


class CapFetcherNotification(CapInfoFetcher):
    def __init__(self, cfg: Config, broadcaster: Broadcaster, locman: LocalizationManager):
        super().__init__(cfg)
        self.broadcaster = broadcaster
        self.loc_man = locman
        self.db = broadcaster.db

    async def on_got_info(self, new_info: ThorInfo):
        if not new_info.is_ok:
            logging.warning('no info got!')
            return

        db = self.db
        old_info = await ThorInfo.get_old_cap(db)
        await ThorInfo.update_ath(db, new_info.price)
        await new_info.save(db)

        if new_info.cap != old_info.cap:
            await self.notify_when_cap_changed(old_info, new_info)

    async def notify_when_cap_changed(self, old: ThorInfo, new: ThorInfo):
        user_lang_map = telegram_chats_from_config(self.cfg, self.loc_man)

        async def message_gen(chat_id):
            return user_lang_map[chat_id].notification_cap_change_text(old, new)

        await self.broadcaster.broadcast(user_lang_map.keys(), message_gen)
