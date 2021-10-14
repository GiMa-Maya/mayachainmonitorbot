from aiogram import filters
from aiogram.dispatcher.filters.state import StatesGroup, State
from aiogram.types import *
from aiogram.utils.helper import HelperMode

from services.dialog.avatar_picture_dialog import AvatarDialog
from services.dialog.base import BaseDialog, message_handler
from services.dialog.lp_info_dialog import LiquidityInfoDialog, LPMenuStates
from services.dialog.metrics_menu import MetricsDialog
from services.dialog.node_op_menu import NodeOpDialog
from services.dialog.settings_menu import SettingsDialog
from services.lib.date_utils import DAY
from services.lib.texts import kbd
from services.notify.types.cap_notify import LiquidityCapNotifier


class MainStates(StatesGroup):
    mode = HelperMode.snake_case

    MAIN_MENU = State()
    ASK_LANGUAGE = State()
    SETTINGS = State()


class MainMenuDialog(BaseDialog):
    @message_handler(commands='start,lang', state='*')
    async def entry_point(self, message: Message):
        user_id = message.chat.id
        await self.deps.broadcaster.register_user(user_id)
        loc_man = self.deps.loc_man
        current_language = await loc_man.get_lang(user_id, self.deps.db)
        components = message.text.split(' ')
        if len(components) == 2 and components[0] == '/start':
            # deep linking
            await self._handle_start_lp_view(message, components[1])
        elif message.get_command(pure=True) == 'lang' or current_language is None:
            await SettingsDialog(self.loc, self.data, self.deps).ask_language(message)
        else:
            info = await LiquidityCapNotifier(self.deps).get_last_cap()

            keyboard = kbd([
                # 1st row
                [self.loc.BUTTON_MM_MY_ADDRESS, self.loc.BUTTON_MM_METRICS],
                # 2nd row
                [self.loc.BUTTON_MM_MAKE_AVATAR] + (
                    [self.loc.BUTTON_MM_NODE_OP] if NodeOpDialog.is_enabled(self.deps.cfg) else []
                ),
                # 3rd row
                [self.loc.BUTTON_MM_SETTINGS]
            ])

            await message.answer(self.loc.welcome_message(info),
                                 reply_markup=keyboard,
                                 disable_notification=True)
            await MainStates.MAIN_MENU.set()

    async def _handle_start_lp_view(self, message: Message, address):
        message.text = ''
        await LPMenuStates.MAIN_MENU.set()
        await LiquidityInfoDialog(self.loc, self.data, self.deps).show_pool_menu_for_address(message, address,
                                                                                             edit=False,
                                                                                             external=True)

    @message_handler(commands='cap', state='*')
    async def cmd_cap(self, message: Message):
        await MetricsDialog(self.loc, self.data, self.deps).show_cap(message)

    @message_handler(commands='price', state='*')
    async def cmd_price(self, message: Message):
        message.text = str(DAY)
        await MetricsDialog(self.loc, self.data, self.deps).on_price_duration_answered(message)

    @message_handler(commands='nodes', state='*')
    async def cmd_nodes(self, message: Message):
        await MetricsDialog(self.loc, self.data, self.deps).show_node_list(message)

    @message_handler(commands='stats', state='*')
    async def cmd_stats(self, message: Message):
        await MetricsDialog(self.loc, self.data, self.deps).show_last_stats(message)

    @message_handler(commands='queue', state='*')
    async def cmd_queue(self, message: Message):
        await MetricsDialog(self.loc, self.data, self.deps).show_queue(message, DAY)

    @message_handler(commands='lp', state='*')
    async def cmd_lp(self, message: Message):
        message.text = ''
        await LiquidityInfoDialog(self.loc, self.data, self.deps).on_enter(message)

    @message_handler(commands='help', state='*')
    async def cmd_help(self, message: Message):
        await message.answer(self.loc.help_message(),
                             disable_web_page_preview=True,
                             disable_notification=True)

    @message_handler(filters.RegexpCommandsFilter(regexp_commands=[r'/.*']), state='*')
    async def on_unknown_command(self, message: Message):
        await message.answer(self.loc.unknown_command(), disable_notification=True)

    @message_handler(state=MainStates.MAIN_MENU)
    async def on_main_menu(self, message: Message):
        if message.text == self.loc.BUTTON_MM_METRICS:
            message.text = ''
            await MetricsDialog(self.loc, self.data, self.deps).on_enter(message)
        elif message.text == self.loc.BUTTON_MM_MY_ADDRESS:
            message.text = ''
            await LiquidityInfoDialog(self.loc, self.data, self.deps).on_enter(message)
        elif message.text == self.loc.BUTTON_MM_SETTINGS:
            message.text = ''
            await SettingsDialog(self.loc, self.data, self.deps).on_enter(message)
        elif message.text == self.loc.BUTTON_MM_MAKE_AVATAR:
            message.text = ''
            await AvatarDialog(self.loc, self.data, self.deps).on_enter(message)
        elif message.text == self.loc.BUTTON_MM_NODE_OP and NodeOpDialog.is_enabled(self.deps.cfg):
            await NodeOpDialog(self.loc, self.data, self.deps).show_main_menu(message)
        else:
            return False
