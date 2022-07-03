import asyncio
import logging
from typing import Optional

from aiogram.dispatcher.filters.state import StatesGroup, State
from aiogram.dispatcher.storage import FSMContextProxy
from aiogram.types import *
from aiogram.utils.helper import HelperMode

from localization.base import BaseLocalization
from services.dialog.base import BaseDialog, message_handler, query_handler
from services.dialog.picture.lp_picture import lp_pool_picture, lp_address_summary_picture
from services.dialog.telegram.inline_list import TelegramInlineList, InlineListResult
from services.jobs.fetch.runeyield import get_rune_yield_connector
from services.lib.constants import NetworkIdents, Chains
from services.lib.date_utils import today_str
from services.lib.depcont import DepContainer
from services.lib.draw_utils import img_to_bio
from services.lib.money import short_address
from services.lib.new_feature import Features
from services.lib.texts import kbd, cut_long_text
from services.models.lp_info import LPAddress
from services.notify.personal.balance import WalletWatchlist


def get_thoryield_address(network: str, address: str, chain: str = Chains.THOR):
    if network == NetworkIdents.TESTNET_MULTICHAIN:
        return f'https://mctn.vercel.app/dashboard?{chain}={address}'
    else:
        chain = chain.lower()
        return f'https://app.thoryield.com/accounts?{chain}={address}'


class LPMenuStates(StatesGroup):
    mode = HelperMode.snake_case
    MAIN_MENU = State()
    WALLET_MENU = State()


# fixme: Use dialog with settings to store wallets in global settings!
class MyWalletsMenu(BaseDialog):
    QUERY_REMOVE_ADDRESS = 'remove-addr'
    QUERY_SUMMARY_OF_ADDRESS = 'summary-addr'
    QUERY_TOGGLE_VIEW_VALUE = 'toggle-view-value'
    QUERY_TOGGLE_LP_PROT = 'toggle-lp-prot'
    QUERY_TOGGLE_BALANCE = 'toggle-balance'

    KEY_MY_ADDRESSES = 'my-address-list'
    KEY_CAN_VIEW_VALUE = 'can-view-value'
    KEY_ADD_LP_PROTECTION = 'add-lp-prot'
    KEY_ACTIVE_ADDRESS = 'active-addr'
    KEY_ACTIVE_ADDRESS_INDEX = 'active-addr-id'
    KEY_IS_EXTERNAL = 'is-external'
    KEY_MY_POOLS = 'my-pools'

    PROP_TRACK_BALANCE = 'track_balance'
    PROP_ADDRESS = 'address'

    # ----------- ENTER ------------

    async def on_enter(self, message: Message):
        await self._show_address_selection_menu(message)

    # ---- WALLET LIST ------

    async def _add_address_handler(self, message: Message, edit: bool):
        # this handler adds an address
        address = message.text.strip()
        if not address:
            return

        if not LPAddress.validate_address(address):
            await message.answer(self.loc.TEXT_INVALID_ADDRESS, disable_notification=True)
            return

        if address.lower() in self.prohibited_addresses:
            await message.answer(self.loc.TEXT_CANNOT_ADD, disable_notification=True)
            return

        self._add_address(address, Chains.BNB)

        # redraw menu!
        await self._show_address_selection_menu(message, edit=edit)

    @message_handler(state=LPMenuStates.MAIN_MENU)
    async def wallet_list_message_handler(self, message: Message):
        await self._add_address_handler(message, edit=False)

    def _make_address_keyboard_list(self, my_addresses):
        extra_row = []

        def address_label(a_obj):
            address = a_obj[self.PROP_ADDRESS]
            # todo: await dynamical look up!
            name = self.deps.name_service.lookup_name_by_address_local(address)
            label = name.name if name else short_address(address, begin=10, end=7)
            return label, address

        # Every button is tuple of (label, full_address)
        short_addresses = [address_label(addr) for addr in my_addresses]

        return TelegramInlineList(
            short_addresses, data_proxy=self.data,
            max_rows=5, back_text=self.loc.BUTTON_BACK, data_prefix='my_addr'
        ).set_extra_buttons_above([extra_row])

    async def _show_address_selection_menu(self, message: Message, edit=False, show_add_more=True):
        await LPMenuStates.MAIN_MENU.set()

        my_addresses = self.my_addresses
        if not my_addresses:
            await message.answer(self.loc.TEXT_NO_ADDRESSES,
                                 reply_markup=kbd([self.loc.BUTTON_BACK]),
                                 disable_notification=True)
        else:
            keyboard = self._make_address_keyboard_list(my_addresses).keyboard()
            if edit:
                await message.edit_text(self.loc.TEXT_YOUR_ADDRESSES, reply_markup=keyboard)
            else:
                await message.answer(self.loc.TEXT_YOUR_ADDRESSES, reply_markup=keyboard)

        if show_add_more:
            msg = self.loc.TEXT_SELECT_ADDRESS_ABOVE if my_addresses else ''
            msg += self.loc.TEXT_SELECT_ADDRESS_SEND_ME
            await message.answer(msg, reply_markup=ReplyKeyboardRemove(), disable_notification=True)

    async def _on_selected_address(self, query: CallbackQuery, list_result: InlineListResult):
        await LPMenuStates.WALLET_MENU.set()
        address = self.data[self.KEY_ACTIVE_ADDRESS] = list_result.selected_data_tag
        self.data[self.KEY_ACTIVE_ADDRESS_INDEX] = list_result.selected_item_index

        await self.show_pool_menu_for_address(query.message, address, edit=True)

    @query_handler(state=LPMenuStates.MAIN_MENU)
    async def on_tap_address(self, query: CallbackQuery):
        result = await self._make_address_keyboard_list(self.my_addresses).handle_query(query)

        if result.result == result.BACK:
            await self.go_back(query.message)
        elif result.result == result.SELECTED:
            await self._on_selected_address(query, result)

    # ----- INSIDE WALLET MENU -----

    @message_handler(state=LPMenuStates.WALLET_MENU)
    async def inside_wallet_message_handler(self, message: Message):
        await self._add_address_handler(message, edit=False)

    async def show_pool_menu_for_address(self, message: Message,
                                         address: str,
                                         reload_pools=True,
                                         edit=True,
                                         external=False):
        # external means that it is not in my list! (called from MainMenu)
        self.data[self.KEY_ACTIVE_ADDRESS] = address
        self.data[self.KEY_IS_EXTERNAL] = external

        if reload_pools:
            loading_message = None
            if edit:
                await message.edit_text(text=self.loc.text_lp_loading_pools(address))
            else:
                # message = await message.answer(text=self.loc.text_lp_loading_pools(address),
                #                                reply_markup=kbd([self.loc.BUTTON_SM_BACK_MM]))
                loading_message = await message.answer(text=self.loc.text_lp_loading_pools(address),
                                                       reply_markup=ReplyKeyboardRemove())
            try:
                rune_yield = get_rune_yield_connector(self.deps)
                my_pools = await rune_yield.get_my_pools(address)
            except FileNotFoundError:
                logging.error(f'not found pools for address {address}')
                my_pools = []
            finally:
                if loading_message:
                    await self.safe_delete(loading_message)

            self.data[self.KEY_MY_POOLS] = my_pools

        await self._present_wallet_contents_menu(message, edit=edit)

    async def _present_wallet_contents_menu(self, message: Message, edit: bool):
        address = self.data[self.KEY_ACTIVE_ADDRESS]
        my_pools = self.data[self.KEY_MY_POOLS]

        balances = await self.get_balances(address)

        text = self.loc.text_inside_my_wallet_title(address, my_pools, balances)
        tg_list = self._keyboard_inside_wallet_menu()
        inline_kbd = tg_list.keyboard()
        if edit:
            await message.edit_text(text=text,
                                    reply_markup=inline_kbd,
                                    disable_web_page_preview=True)
        else:
            await message.answer(text=text,
                                 reply_markup=inline_kbd,
                                 disable_web_page_preview=True,
                                 disable_notification=True)

    def _keyboard_inside_wallet_menu(self) -> TelegramInlineList:
        external = self.data.get(self.KEY_IS_EXTERNAL, False)
        view_value = self.data.get(self.KEY_CAN_VIEW_VALUE, True)
        # lp_prot_on = self.data.get(self.KEY_ADD_LP_PROTECTION, True)
        my_pools = self.data.get(self.KEY_MY_POOLS, [])

        addr_idx = int(self.data.get(self.KEY_ACTIVE_ADDRESS_INDEX, 0))
        address = self.data.get(self.KEY_ACTIVE_ADDRESS)
        address_obj = self._get_address_object(address)
        track_balance = address_obj.get(self.PROP_TRACK_BALANCE, False)

        if my_pools is None:
            my_pools = []

        chain = Chains.detect_chain(address)
        chain = chain if chain else Chains.BTC  # fixme: how about other chains?

        # ---------------------------- POOLS ------------------------------
        pool_labels = [(cut_long_text(pool), pool) for pool in my_pools]

        tg_list = TelegramInlineList(
            pool_labels, data_proxy=self.data,
            max_rows=3,
            back_text='', data_prefix='pools',
        )

        below_button_matrix = []

        # ---------------------------- ROW 1 ------------------------------
        row1 = []
        if my_pools:
            # Summary button (only if there are LP pools)
            row1.append(InlineKeyboardButton(
                self.loc.BUTTON_SM_SUMMARY,
                callback_data=f'{self.QUERY_SUMMARY_OF_ADDRESS}:{addr_idx}'))

        # THOR YIELD button
        row1.append(InlineKeyboardButton(
            self.loc.BUTTON_VIEW_RUNE_DOT_YIELD,
            url=get_thoryield_address(self.deps.cfg.network_id, address, chain)))

        below_button_matrix.append(row1)

        # ---------------------------- ROW 2 ------------------------------
        row2 = []
        if my_pools:
            # row2.append(InlineKeyboardButton(
            #     self.loc.BUTTON_LP_PROT_ON if lp_prot_on else self.loc.BUTTON_LP_PROT_OFF,
            #     callback_data=self.QUERY_TOGGLE_LP_PROT))

            # View value ON/OFF toggle switch
            row2.append(InlineKeyboardButton(
                self.loc.BUTTON_VIEW_VALUE_ON if view_value else self.loc.BUTTON_VIEW_VALUE_OFF,
                callback_data=self.QUERY_TOGGLE_VIEW_VALUE))

        if chain == Chains.THOR:
            # Track balance ON/OFF toggle switch
            text = self.loc.BUTTON_TRACK_BALANCE_ON if track_balance else self.loc.BUTTON_TRACK_BALANCE_OFF
            text = self.text_new_feature(text, Features.F_PERSONAL_TRACK_BALANCE)
            row2.append(InlineKeyboardButton(text, callback_data=self.QUERY_TOGGLE_BALANCE))

        below_button_matrix.append(row2)

        # ---------------------------- ROW 3 ------------------------------
        row3 = []

        if not external:
            # Remove this address button
            row3.append(InlineKeyboardButton(self.loc.BUTTON_REMOVE_THIS_ADDRESS,
                                             callback_data=f'{self.QUERY_REMOVE_ADDRESS}:{addr_idx}'), )

        # Back button
        row3.append(InlineKeyboardButton(self.loc.BUTTON_SM_BACK_TO_LIST, callback_data=tg_list.data_back))

        below_button_matrix.append(row3)

        # install all extra buttons to the List
        tg_list.set_extra_buttons_below(below_button_matrix)
        return tg_list

    @query_handler(state=LPMenuStates.WALLET_MENU)
    async def on_wallet_query(self, query: CallbackQuery):
        result = await self._keyboard_inside_wallet_menu().handle_query(query)

        if result.result == result.BACK:
            await self._show_address_selection_menu(query.message, edit=True, show_add_more=False)
        elif result.result == result.SELECTED:
            await self.view_pool_report(query, result.selected_data_tag)
            await self._show_wallet_again(query)
        elif query.data.startswith(f'{self.QUERY_SUMMARY_OF_ADDRESS}:'):
            await self.view_address_summary(query)
            await self._show_wallet_again(query)
        elif query.data.startswith(f'{self.QUERY_REMOVE_ADDRESS}:'):
            _, index = query.data.split(':')
            await self._remove_address(index)
            await self._show_address_selection_menu(query.message, edit=True, show_add_more=False)
        elif query.data == self.QUERY_TOGGLE_VIEW_VALUE:
            self.data[self.KEY_CAN_VIEW_VALUE] = not self.data.get(self.KEY_CAN_VIEW_VALUE, True)
            await self._present_wallet_contents_menu(query.message, edit=True)
        # elif query.data == self.QUERY_TOGGLE_LP_PROT:
        #     self.data[self.KEY_ADD_LP_PROTECTION] = not self.data.get(self.KEY_ADD_LP_PROTECTION, True)
        #     await self._present_wallet_contents_menu(query.message, edit=True)
        elif query.data == self.QUERY_TOGGLE_BALANCE:
            address = self.data[self.KEY_ACTIVE_ADDRESS]
            is_on = self._toggle_address_property(address, self.PROP_TRACK_BALANCE)
            await self._process_wallet_balance_flag(address, is_on)
            await self._present_wallet_contents_menu(query.message, edit=True)

    async def _show_wallet_again(self, query: CallbackQuery):
        address = self.data[self.KEY_ACTIVE_ADDRESS]
        await self.show_pool_menu_for_address(query.message, address, edit=False)

    # --- LP Pic generation actions:

    @property
    def add_il_protection(self):
        # return bool(self.data.get(self.KEY_ADD_LP_PROTECTION, True))
        return True

    async def view_pool_report(self, query: CallbackQuery, pool):
        address = self.data[self.KEY_ACTIVE_ADDRESS]

        # POST A LOADING STICKER
        sticker = await self.answer_loading_sticker(query.message)

        # WORK...
        rune_yield = get_rune_yield_connector(self.deps)
        rune_yield.add_il_protection_to_final_figures = self.add_il_protection
        lp_report = await rune_yield.generate_yield_report_single_pool(address, pool)

        # GENERATE A PICTURE
        value_hidden = not self.data.get(self.KEY_CAN_VIEW_VALUE, True)

        picture = await lp_pool_picture(self.deps.price_holder, lp_report, self.loc, value_hidden=value_hidden)
        picture_io = img_to_bio(picture, f'Thorchain_LP_{pool}_{today_str()}.png')

        # ANSWER
        await self._present_wallet_contents_menu(query.message, edit=False)
        await query.message.answer_photo(picture_io,  # caption=self.loc.TEXT_LP_IMG_CAPTION,
                                         disable_notification=True)

        # CLEAN UP
        await asyncio.gather(self.safe_delete(query.message),
                             self.safe_delete(sticker))

    async def view_address_summary(self, query: CallbackQuery):
        address = self.data[self.KEY_ACTIVE_ADDRESS]

        my_pools = self.data[self.KEY_MY_POOLS]
        if not my_pools:
            await query.message.answer(self.loc.TEXT_LP_NO_POOLS_FOR_THIS_ADDRESS)
            return

        # POST A LOADING STICKER
        sticker = await self.answer_loading_sticker(query.message)

        # WORK
        rune_yield = get_rune_yield_connector(self.deps)
        rune_yield.add_il_protection_to_final_figures = self.add_il_protection
        yield_summary = await rune_yield.generate_yield_summary(address, my_pools)

        # GENERATE A PICTURE
        value_hidden = not self.data.get(self.KEY_CAN_VIEW_VALUE, True)
        picture = await lp_address_summary_picture(list(yield_summary.reports),
                                                   yield_summary.charts,
                                                   self.loc, value_hidden=value_hidden)
        picture_io = img_to_bio(picture, f'Thorchain_LP_Summary_{today_str()}.png')

        # ANSWER
        await self._present_wallet_contents_menu(query.message, edit=False)
        await query.message.answer_photo(picture_io,
                                         disable_notification=True)

        # CLEAN UP
        await asyncio.gather(self.safe_delete(query.message),
                             self.safe_delete(sticker))

    # --- MANAGE ADDRESSES ---

    @property
    def my_addresses(self):
        return self.data.get(self.KEY_MY_ADDRESSES, [])

    def _add_address(self, new_addr, chain):
        new_addr = str(new_addr).strip()
        current_list = self.my_addresses
        my_unique_addr = set(a[self.PROP_ADDRESS] for a in current_list)
        if new_addr not in my_unique_addr:
            new_addr_obj = {
                self.PROP_ADDRESS: new_addr,
                'chain': chain,
                self.PROP_TRACK_BALANCE: False,
            }
            current_list.append(new_addr_obj)
            self.data[self.KEY_MY_ADDRESSES] = current_list

    async def _remove_address(self, index):
        try:
            index = int(index)
            address_list = self.my_addresses
            address = address_list[index][self.PROP_ADDRESS]
            del address_list[index]
            await self._process_wallet_balance_flag(address, is_on=False)
        except IndexError:
            logging.error(f'Cannot delete address at {index = },')

    def _toggle_address_property(self, address, prop, default=False):
        obj = self._get_address_object(address)
        if obj:
            obj[prop] = not obj.get(prop, default)
            return obj[prop]

    def _get_address_object(self, address):
        try:
            return next(a for a in self.my_addresses if a[self.PROP_ADDRESS] == address)
        except StopIteration:
            return {}

    # --- MISC ---

    async def get_balances(self, address: str):
        if LPAddress.is_thor_prefix(address):
            try:
                return await self.deps.thor_connector.query_balance(address)
            except Exception:
                pass

    @property
    def prohibited_addresses(self):
        addresses = self.deps.cfg.get_pure('native_scanner.prohibited_addresses')
        return addresses if isinstance(addresses, list) else []

    async def _process_wallet_balance_flag(self, address: str, is_on: bool):
        user_id = str(self.data.fsm_context.user)
        await self._wallet_watch.set_user_to_node(user_id, address, is_on)

    def __init__(self, loc: BaseLocalization, data: Optional[FSMContextProxy], d: DepContainer, message: Message):
        super().__init__(loc, data, d, message)
        self._wallet_watch = WalletWatchlist(d.db)