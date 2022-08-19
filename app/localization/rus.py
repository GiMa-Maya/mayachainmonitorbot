from datetime import datetime
from math import ceil
from typing import List

from aiothornode.types import ThorChainInfo, ThorBalances
from semver import VersionInfo

from localization.base import BaseLocalization, CREATOR_TG, URL_LEADERBOARD_MCCN
from services.jobs.fetch.circulating import SupplyEntry
from services.lib.constants import Chains, rune_origin
from services.lib.date_utils import format_time_ago, seconds_human, now_ts
from services.lib.explorers import get_explorer_url_to_address, get_thoryield_address, \
    get_ip_info_link
from services.lib.money import pretty_dollar, pretty_money, short_address, adaptive_round_to_str, calc_percent_change, \
    emoji_for_percent_change, Asset, short_money, short_dollar, format_percent, RAIDO_GLYPH, short_rune
from services.lib.texts import bold, link, code, ital, pre, x_ses, progressbar, bracketify, \
    up_down_arrow, plural, grouper, regroup_joining, shorten_text
from services.models.cap_info import ThorCapInfo
from services.models.killed_rune import KilledRuneEntry
from services.models.last_block import BlockProduceState, EventBlockSpeed
from services.models.mimir import MimirChange, MimirHolder, MimirVoting, MimirVoteOption
from services.models.mimir_naming import MimirUnits
from services.models.net_stats import NetworkStats
from services.models.node_info import NodeSetChanges, NodeInfo, NodeVersionConsensus, NodeEvent, EventDataSlash, \
    NodeEventType, EventBlockHeight
from services.models.pool_info import PoolInfo, PoolChanges, PoolDetailHolder
from services.models.price import PriceReport, RuneMarketInfo
from services.models.queue import QueueInfo
from services.models.transfer import RuneTransfer, RuneCEXFlow
from services.models.tx import ThorTxExtended, ThorTxType


class RussianLocalization(BaseLocalization):
    LOADING = '⌛ Загрузка...'
    SUCCESS = '✅ Успех!'
    ND = 'Неопр.'
    NA = 'Н/Д'

    LIST_NEXT_PAGE = 'След. стр. »'
    LIST_PREV_PAGE = '« Пред. стр.'

    BOT_LOADING = '⌛ Бот был недавно перезапущен и все еще загружается. Пожалуйста, повторите попытку через пару минут.'

    RATE_LIMIT_WARNING = '🔥 <b>Внимание!</b>\n' \
                         'Кажется, вы получаете слишком много персональных уведомлений. ' \
                         'На некоторое время получение будет ограничено. ' \
                         'Проверьте настройки, чтобы отрегулировать частоту уведомлений.'

    SHORT_MONEY_LOC = {
        'K': ' тыс',
        'M': ' млн',
        'B': ' млрд',
        'T': ' трлн',
    }

    # ---- WELCOME ----
    def help_message(self):
        return (
            f"Этот бот уведомляет о крупных движениях с сети {link(self.THORCHAIN_LINK, 'THORChain')}.\n"
            f"Команды:\n"
            f"/help – эта помощь\n"
            f"/start – запуск и перезапуск бота\n"
            f"/lang – изменить язык\n"
            f"/cap – текущий кап для ликвидности в пулах THORChain\n"
            f"/price – текущая цена {self.R}\n"
            f"/queue – размер очереди транзакций\n"
            f"/nodes – список нод\n"
            f"/stats – THORChain статистика сети\n"
            f"/chains – Подключенные блокчейны\n"
            f"/lp – мониторинг ваших пулов\n"
            f"<b>⚠️ Бот теперь уведомляет только в канале {self.alert_channel_name}!</b>\n"
            f"🤗 Отзывы и поддержка: {CREATOR_TG}."
        )

    def welcome_message(self, info: ThorCapInfo):
        return (
            f"Привет! Здесь ты можешь найти метрики THORChain и узнать результаты предоставления ликвидности в пулы.\n"
            f"Цена {self.R} сейчас <code>{info.price:.3f} $</code>.\n"
            f"<b>⚠️ Бот теперь уведомляет только в канале {self.alert_channel_name}!</b>\n"
            f"Набери /help, чтобы видеть список команд.\n"
            f"🤗 Отзывы и поддержка: {CREATOR_TG}."
        )

    def unknown_command(self):
        return (
            "🙄 Извини, я не знаю такой команды.\n"
            "Нажми на /help, чтобы увидеть доступные команды."
        )

    # ----- MAIN MENU ------

    BUTTON_MM_MY_ADDRESS = '🏦 Мои кошельки'
    BUTTON_MM_METRICS = '📐 Метрики'
    BUTTON_MM_SETTINGS = f'⚙️ Настройки'
    BUTTON_MM_MAKE_AVATAR = f'🦹‍️️ Сделай аву'
    BUTTON_MM_NODE_OP = '🤖 Операторам нод'

    # ------ MY WALLETS MENU -----

    BUTTON_SM_ADD_ADDRESS = '➕ Добавить новый адрес'
    BUTTON_BACK = '🔙 Назад'
    BUTTON_SM_BACK_TO_LIST = '🔙 Назад к адресам'
    BUTTON_SM_BACK_MM = '🔙 Главное меню'

    BUTTON_SM_SUMMARY = '💲 Сводка'

    BUTTON_VIEW_RUNE_DOT_YIELD = '🌎 Открыть на THORYield'
    BUTTON_VIEW_VALUE_ON = 'Скрыть деньги: НЕТ'
    BUTTON_VIEW_VALUE_OFF = 'Скрыть деньги: ДА'

    BUTTON_LP_PROT_ON = 'IL защита: ДА'
    BUTTON_LP_PROT_OFF = 'IL защита: НЕТ'

    BUTTON_TRACK_BALANCE_ON = 'Следить: ДА'
    BUTTON_TRACK_BALANCE_OFF = 'Следить: НЕТ'

    BUTTON_SET_RUNE_ALERT_LIMIT = 'Уст. мин. лимит R'

    BUTTON_REMOVE_THIS_ADDRESS = '❌ Удалить этот адрес'

    TEXT_NO_ADDRESSES = "🔆 Вы еще не добавили никаких адресов. Пришлите мне адрес, чтобы добавить."
    TEXT_YOUR_ADDRESSES = '🔆 Вы добавили следующие адреса:'
    TEXT_INVALID_ADDRESS = code('⛔️ Ошибка в формате адреса!')
    TEXT_SELECT_ADDRESS_ABOVE = 'Выбери адрес выше ☝️ '
    TEXT_SELECT_ADDRESS_SEND_ME = 'Если хотите добавить адрес, пришлите его мне 👇'
    TEXT_LP_NO_POOLS_FOR_THIS_ADDRESS = '📪 <i>На этом адресе нет пулов ликвидности.</i>'
    TEXT_CANNOT_ADD = '😐 Простите, но вы не можете добавить этот адрес.'
    TEXT_ANY = 'Любые'

    TEXT_INVALID_LIMIT = '⛔ <b>Неправильное число!</b> Вам следует ввести положительное число.'

    BUTTON_CANCEL = 'Отмена'

    def text_set_rune_limit_threshold(self, address, curr_limit):
        return (
            f'🎚 Введите минимальное количество Рун '
            f'для срабатывания уведомлений о переводах на этом адресе ({address}).\n'
            f'Сейчас это: {ital(short_rune(curr_limit))}.\n\n'
            f'Вы можете прислать мне число сообщением или выбрать один из вариантов на кнопках.'
        )

    def text_lp_img_caption(self):
        bot_link = "@" + self.this_bot_name
        start_me = self.url_start_me
        return f'Сгенерировано: {link(start_me, bot_link)}'

    LP_PIC_POOL = 'ПУЛ'
    LP_PIC_RUNE = 'RUNE'
    LP_PIC_ADDED = 'Добавлено'
    LP_PIC_WITHDRAWN = 'Выведено'
    LP_PIC_REDEEM = 'Можно забрать'
    LP_PIC_GAIN_LOSS = 'Доход / убыток'
    LP_PIC_IN_USD = 'в USD'
    LP_PIC_IN_USD_CAP = 'или в USD'
    LP_PIC_R_RUNE = f'В {RAIDO_GLYPH}une'
    LP_PIC_IN_ASSET = 'или в {0}'
    LP_PIC_ADDED_VALUE = 'Добавлено всего'
    LP_PIC_WITHDRAWN_VALUE = 'Выведено всего'
    LP_PIC_CURRENT_VALUE = 'В пуле (+чай)'
    LP_PIC_PRICE_CHANGE = 'Изменение цены'
    LP_PIC_PRICE_CHANGE_2 = 'с 1го добавления'
    LP_PIC_LP_VS_HOLD = 'Против ХОЛД'
    LP_PIC_LP_APY = 'Годовых'
    LP_PIC_LP_APY_OVER_LIMIT = 'Очень много %'
    LP_PIC_EARLY = 'Еще рано...'
    LP_PIC_FOOTER = ""  # my LP scanner is used
    LP_PIC_FEES = 'Ваши чаевые'
    LP_PIC_IL_PROTECTION = 'Страховка от IL'
    LP_PIC_NO_NEED_PROTECTION = 'Не требуется'
    LP_PIC_EARLY_TO_PROTECT = 'Рано, подождите...'
    LP_PIC_PROTECTION_DISABLED = 'Отключена'

    LP_PIC_SUMMARY_HEADER = 'Сводка по пулам ликвидности'
    LP_PIC_SUMMARY_ADDED_VALUE = 'Добавлено'
    LP_PIC_SUMMARY_WITHDRAWN_VALUE = 'Выведено'
    LP_PIC_SUMMARY_CURRENT_VALUE = 'Сейчас в пуле'
    LP_PIC_SUMMARY_TOTAL_GAIN_LOSS = 'Доход/убыток'
    LP_PIC_SUMMARY_TOTAL_GAIN_LOSS_PERCENT = 'Доход/убыток %'
    LP_PIC_SUMMARY_AS_IF_IN_RUNE = f'Если все в {RAIDO_GLYPH}'
    LP_PIC_SUMMARY_AS_IF_IN_USD = 'Если все в $'
    LP_PIC_SUMMARY_TOTAL_LP_VS_HOLD = 'Итого холд против пулов, $'
    LP_PIC_SUMMARY_NO_WEEKLY_CHART = "Нет недельного графика, извините..."

    def pic_lping_days(self, total_days, first_add_ts):
        start_date = datetime.fromtimestamp(first_add_ts).strftime('%d.%m.%Y')
        return f'{ceil(total_days)} дн. ({start_date})'

    TEXT_PLEASE_WAIT = '⏳ <b>Пожалуйста, подождите...</b>'

    def text_lp_loading_pools(self, address):
        return f'{self.TEXT_PLEASE_WAIT}\n' \
               f'Идет загрузка пулов для адреса {pre(address)}...\n' \
               f'Иногда она может идти долго, если Midgard сильно нагружен.'

    def text_inside_my_wallet_title(self, address, pools, balances: ThorBalances, min_limit: float, chain):
        if pools:
            title = '\n'
            footer = '\n\n👇 Выберите пул, чтобы получить подробную карточку информации о ликвидности.'
        else:
            title = self.TEXT_LP_NO_POOLS_FOR_THIS_ADDRESS + '\n\n'
            footer = ''

        explorer_links = self.explorer_link_to_address_with_domain(address)

        balance_str = self.text_balances(balances, 'Балансы аккаунта: ')

        acc_caption = ''
        # todo: dynamic!
        addr_name = self.name_service.lookup_name_by_address_local(address)
        if addr_name:
            acc_caption = f' ({addr_name.name})'

        thor_yield_url = get_thoryield_address(self.cfg.network_id, address, chain)
        thor_yield_link = link(thor_yield_url, 'THORYield')

        if min_limit is not None:
            limit_str = f'📨 Транзакции ≥ {short_rune(min_limit)} отслеживаются.\n'
        else:
            limit_str = ''

        return (
            f'🛳️ Аккаунт: "{pre(address)}"{acc_caption}\n'
            f'{title}'
            f"{balance_str}"
            f'{limit_str}'
            f"🔍 Обозреватель: {explorer_links}\n"
            f"🌎 Посмотреть на {thor_yield_link}"
            f"{footer}"
        )

    def text_lp_today(self):
        today = datetime.now().strftime('%d.%m.%Y')
        return f'Сегодня: {today}'

    # ----- CAP ------

    def notification_text_cap_change(self, old: ThorCapInfo, new: ThorCapInfo):
        up = old.cap < new.cap
        verb = "подрос" if up else "упал"
        arrow = '⬆️' if up else '⚠️ ⬇️'
        call = "Ай-да запулим еще!\n" if up else ''
        return (
            f'{arrow} <b>Кап {verb} с {pretty_money(old.cap)} до {pretty_money(new.cap)}!</b>\n'
            f'Сейчас в пулы помещено <b>{pretty_money(new.pooled_rune)}</b> {self.R}.\n'
            f"{self._cap_progress_bar(new)}\n"
            f'🤲🏻 Вы можете добавить еще {bold(pretty_money(new.how_much_rune_you_can_lp) + " " + RAIDO_GLYPH)} {self.R} '
            f'или {bold(pretty_dollar(new.how_much_usd_you_can_lp))}.\n'
            f'Цена {self.R} в пуле <code>{new.price:.3f} $</code>.\n'
            f'{call}'
            f'{self.thor_site()}'
        )

    def notification_text_cap_full(self, cap: ThorCapInfo):
        return (
            '🙆‍♀️ <b>Ликвидность достигла установленного предела!</b>\n'
            'Пожалуйста, пока что не пытайтесь ничего добавить в пулы. '
            'Вы получите возврат ваших средств!\n'
            f'<b>{pretty_money(cap.pooled_rune)} {self.R}</b> из '
            f"<b>{pretty_money(cap.cap)} {self.R}</b> сейчас в пулах.\n"
            f"{self._cap_progress_bar(cap)}\n"
        )

    def notification_text_cap_opened_up(self, cap: ThorCapInfo):
        return (
            '💡 <b>Освободилось место в пулах ликвидности!</b>\n'
            f'Сейчас в пулах <i>{pretty_money(cap.pooled_rune)} {self.R}</i> из '
            f"<i>{pretty_money(cap.cap)} {self.R}</i> максимально возможных.\n"
            f"{self._cap_progress_bar(cap)}\n"
            f'🤲🏻 Вы можеще еще добавить {bold(pretty_money(cap.how_much_rune_you_can_lp) + " " + RAIDO_GLYPH)} {self.R} '
            f'или {bold(pretty_dollar(cap.how_much_usd_you_can_lp))}.\n👉🏻 {self.thor_site()}'
        )

    # ------ PRICE -------

    PRICE_GRAPH_TITLE = f'Цена {RAIDO_GLYPH}уны'
    PRICE_GRAPH_LEGEND_DET_PRICE = 'Детерминистская цена'
    PRICE_GRAPH_LEGEND_ACTUAL_PRICE = 'Цена пулов'
    PRICE_GRAPH_LEGEND_CEX_PRICE = f'CEX BEP2 цена'

    # ------ TXS -------

    TEXT_MORE_TXS = ' и {n} еще'

    @staticmethod
    def none_str(x):
        return 'нет' if x is None else x

    def notification_text_large_single_tx(self, tx: ThorTxExtended,
                                          usd_per_rune: float,
                                          pool_info: PoolInfo,
                                          cap: ThorCapInfo = None):
        (ap, asset_side_usd_short, chain, percent_of_pool, pool_depth_usd, rp, rune_side_usd_short,
         total_usd_volume) = self.lp_tx_calculations(usd_per_rune, pool_info, tx)

        heading = ''
        if tx.type == ThorTxType.TYPE_ADD_LIQUIDITY:
            heading = f'🐳 <b>Кит добавил ликвидности</b> 🟢'
        elif tx.type == ThorTxType.TYPE_WITHDRAW:
            heading = f'🐳 <b>Кит вывел ликвидность</b> 🔴'
        elif tx.type == ThorTxType.TYPE_DONATE:
            heading = f'🙌 <b>Безвозмездное добавление в пул</b>'
        elif tx.type == ThorTxType.TYPE_SWAP:
            heading = f'🐳 <b>Крупный обмен</b> 🔁'
        elif tx.type == ThorTxType.TYPE_REFUND:
            heading = f'🐳️ <b>Большой возврат средств</b> ↩️❗'
        elif tx.type == ThorTxType.TYPE_SWITCH:
            heading = f'🐳 <b>Крупный апгрейд {self.R}</b> 🆙'

        asset = Asset(tx.first_pool).name

        content = ''
        if tx.type in (ThorTxType.TYPE_ADD_LIQUIDITY, ThorTxType.TYPE_WITHDRAW, ThorTxType.TYPE_DONATE):
            if tx.affiliate_fee > 0:
                aff_fee_usd = tx.get_affiliate_fee_usd(usd_per_rune)
                mark = self._exclamation_sign(aff_fee_usd, 'fee_usd_limit')
                aff_text = f'Партнерский бонус: {bold(short_dollar(aff_fee_usd))}{mark} ' \
                           f'({format_percent(tx.affiliate_fee)})\n'
            else:
                aff_text = ''

            ilp_rune = tx.meta_withdraw.ilp_rune if tx.meta_withdraw else 0
            if ilp_rune > 0:
                ilp_rune_fmt = pretty_money(ilp_rune, postfix=" " + self.R)
                ilp_text = f'🛡️ Выплачено защиты от IL: {code(ilp_rune_fmt)} ' \
                           f'({pretty_dollar(ilp_rune * usd_per_rune)})\n'
            else:
                ilp_text = ''

            content = (
                f"<b>{pretty_money(tx.rune_amount)} {self.R}</b> ({rp:.0f}% = {rune_side_usd_short}) ↔️ "
                f"<b>{pretty_money(tx.asset_amount)} {asset}</b> "
                f"({ap:.0f}% = {asset_side_usd_short})\n"
                f"Всего: <code>${pretty_money(total_usd_volume)}</code> ({percent_of_pool:.2f}% от всего пула).\n"
                f"{aff_text}"
                f"{ilp_text}"
                f"Глубина пула сейчас: <b>${pretty_money(pool_depth_usd)}</b>.\n"
            )
        elif tx.type == ThorTxType.TYPE_SWITCH:
            # [Amt] Rune [Blockchain: ERC20/BEP2] -> [Amt] THOR Rune ($usd)
            in_rune_amt = tx.asset_amount
            out_rune_amt = tx.rune_amount
            killed_rune = max(0.0, in_rune_amt - out_rune_amt)
            killed_usd_str = short_dollar(killed_rune * usd_per_rune)
            killed_percent_str = format_percent(killed_rune, in_rune_amt)
            origin = rune_origin(tx.first_input_tx.first_asset)
            content = (
                f"{bold(short_money(in_rune_amt))} {origin} {self.R} ➡️ "
                f"{bold(short_money(out_rune_amt))} нативных {self.R} "
                f"({short_dollar(tx.get_usd_volume(usd_per_rune))})"
            )
            if killed_rune > 0:
                content += f'\n☠️ Уничтожено {bold(short_rune(killed_rune))} ' \
                           f'({killed_percent_str} или {killed_usd_str})!'
        elif tx.type == ThorTxType.TYPE_REFUND:
            reason = shorten_text(tx.meta_refund.reason, 180)
            content = (
                    self.tx_convert_string(tx, usd_per_rune) +
                    f"\nПричина: {pre(reason)}"
            )
        elif tx.type == ThorTxType.TYPE_SWAP:
            content = self.tx_convert_string(tx, usd_per_rune)
            slip_str = f'{tx.meta_swap.trade_slip_percent:.3f} %'
            l_fee_usd = tx.meta_swap.liquidity_fee_rune_float * usd_per_rune

            if tx.affiliate_fee > 0:
                aff_fee_usd = tx.get_affiliate_fee_usd(usd_per_rune)
                mark = self._exclamation_sign(aff_fee_usd, 'fee_usd_limit')
                aff_text = f'Партнерский бонус: {bold(short_dollar(aff_fee_usd))}{mark} ' \
                           f'({format_percent(tx.affiliate_fee)})\n'
            else:
                aff_text = ''

            slip_mark = self._exclamation_sign(l_fee_usd, 'slip_usd_limit')
            content += (
                f"\n{aff_text}"
                f"Проскальзывание: {bold(slip_str)}\n"
                f"Комиссия пулам: {bold(pretty_dollar(l_fee_usd))}{slip_mark}"
            )

        blockchain_components = [f"Пользователь: {self.link_to_explorer_user_address_for_tx(tx)}"]

        if tx.in_tx:
            in_links = self.links_to_txs(tx.in_tx, tx.tx_hash)
            if in_links:
                blockchain_components.append('Входы: ' + in_links)

        if tx.out_tx:
            out_links = self.links_to_txs(tx.out_tx, tx.tx_hash)
            if out_links:
                blockchain_components.append('Выходы: ' + out_links)

        msg = f"{heading}\n{content}\n" + " / ".join(blockchain_components)

        if cap:
            msg += (
                f"\n\n"
                f"Кап ликвидности {self._cap_progress_bar(cap)}.\n"
                f'Вы можете добавить еще {code(pretty_money(cap.how_much_rune_you_can_lp))} {bold(self.R)} '
                f'({pretty_dollar(cap.how_much_usd_you_can_lp)}).'
            )

        return msg.strip()

    # ------- QUEUE -------

    def notification_text_queue_update(self, item_type, is_free, value):
        if is_free:
            return f"☺️ Очередь {item_type} снова опустела!"
        else:
            if item_type != 'internal':
                extra = f"\n[{item_type}] транзакции могут запаздывать."
            else:
                extra = ''

            return f"🤬 <b>Внимание!</b> Очередь {code(item_type)} имеет {value} транзакций!{extra}"

    # ------- PRICE -------

    def notification_text_price_update(self, p: PriceReport, ath=False, halted_chains=None):
        title = bold('Обновление цены') if not ath else bold('🚀 Достигнуть новый исторический максимум!')

        c_gecko_url = 'https://www.coingecko.com/ru/' \
                      '%D0%9A%D1%80%D0%B8%D0%BF%D1%82%D0%BE%D0%B2%D0%B0%D0%BB%D1%8E%D1%82%D1%8B/thorchain'
        c_gecko_link = link(c_gecko_url, 'RUNE')

        message = f"{title} | {c_gecko_link}\n\n"

        if halted_chains:
            hc = pre(', '.join(halted_chains))
            message += f"🚨 <code>Торговля по-прежнему остановлена на {hc}.</code>\n\n"

        price = p.market_info.pool_rune_price

        btc_price = f"₿ {p.btc_pool_rune_price:.8f}"
        pr_text = f"${price:.2f}"
        message += f"Цена <b>RUNE</b> сейчас {code(pr_text)} ({btc_price}).\n"

        fp = p.market_info

        if fp.cex_price > 0.0:
            message += f"Цена <b>RUNE</b> на централизованной бирже {self.ref_cex_name}: " \
                       f"{bold(pretty_dollar(fp.cex_price))}.\n"

            div, div_p = fp.divergence_abs, fp.divergence_percent
            message += f"<b>Расхождение</b> родной и BEP2 Руны: {code(pretty_dollar(div))} ({div_p:.1f}%).\n"

        last_ath = p.last_ath
        if last_ath is not None and ath:
            if isinstance(last_ath.ath_date, float):
                last_ath_pr = f'{last_ath.ath_price:.2f}'
            else:
                last_ath_pr = str(last_ath.ath_price)
            ago_str = self.format_time_ago(now_ts() - last_ath.ath_date)
            message += f"Последний ATH был ${pre(last_ath_pr)} ({ago_str}).\n"

        time_combos = zip(
            ('1ч.', '24ч.', '7дн.'),
            (p.price_1h, p.price_24h, p.price_7d)
        )
        for title, old_price in time_combos:
            if old_price:
                pc = calc_percent_change(old_price, price)
                message += pre(f"{title.rjust(5)}:{adaptive_round_to_str(pc, True).rjust(8)} % "
                               f"{emoji_for_percent_change(pc).ljust(4).rjust(6)}") + "\n"

        if fp.rank >= 1:
            message += f"Капитализация: {bold(pretty_dollar(fp.market_cap))} (#{bold(fp.rank)} место)\n"

        if fp.total_trade_volume_usd > 0:
            message += f"Объем торгов сегодня: {bold(pretty_dollar(fp.total_trade_volume_usd))}.\n"

        message += '\n'

        if fp.tlv_usd >= 1:
            message += (f"TVL (не-RUNE активов): ${bold(pretty_money(fp.tlv_usd))}\n"
                        f"Детерминистическая цена: {code(pretty_money(fp.fair_price, prefix='$'))}\n"
                        f"Спекулятивый множитель: {pre(x_ses(fp.fair_price, price))}\n")

        return message.rstrip()

    # ------- POOL CHURN -------

    def notification_text_pool_churn(self, pc: PoolChanges):
        if pc.pools_changed:
            message = bold('🏊 Изменения в пулах ликвидности:') + '\n\n'
        else:
            message = ''

        ru_stat = {
            PoolInfo.DEPRECATED_ENABLED: 'включен',
            PoolInfo.AVAILABLE: 'включен',
            PoolInfo.SUSPENDED: 'приостановлен',

            PoolInfo.DEPRECATED_BOOTSTRAP: 'ожидает',
            PoolInfo.STAGED: 'ожидает'
        }

        def pool_text(pool_name, status, to_status=None):
            if PoolInfo.is_status_enabled(to_status):
                extra = '🎉 ПУЛ АКТИВИРОВАН!'
            else:
                extra = ital(ru_stat[status])
                if to_status is not None:
                    extra += f' → {ital(ru_stat[to_status])}'
                extra = f'({extra})'
            return f'  • {self.pool_link(pool_name)}: {extra}'

        if pc.pools_added:
            message += '✅ Пулы добавлены:\n' + '\n'.join([pool_text(*a) for a in pc.pools_added]) + '\n'
        if pc.pools_removed:
            message += '❌ Пулы удалены:\n' + '\n'.join([pool_text(*a) for a in pc.pools_removed]) + '\n'
        if pc.pools_changed:
            message += '🔄 Пулы изменились:\n' + '\n'.join([pool_text(*a) for a in pc.pools_changed]) + '\n'

        return message.rstrip()

    # -------- SETTINGS --------

    TEXT_SETTING_INTRO = '<b>Настройки</b>\nЧто вы хотите поменять в настройках?'
    BUTTON_SET_LANGUAGE = '🌐 Язык'
    BUTTON_SET_NODE_OP_GOTO = '🖥 Операторам нод'
    BUTTON_SET_PRICE_DIVERGENCE = '↕️ Расхождение цен'

    TEXT_SETTINGS_LANGUAGE_SELECT = 'Пожалуйста, выберите язык / Please select a language'

    # ------- PERSONAL PRICE DIVERGENCE -------

    TEXT_PRICE_DIV_MIN_PERCENT = (
        '↕️ Здесь вы можете настроить ваши персональные уведомления о расхождении цен BEP2 Руны и Нативной Руны.\n'
        'Для начала введите <b>минимальный</b> процент отклонения (<i>не может быть меньше, чем 0.1</i>).\n'
        'Если вы, не хотите получать уведомления с минимальной стороны, просто нажмите "Далее"'
    )

    BUTTON_PRICE_DIV_NEXT = 'Далее ⏭️'
    BUTTON_PRICE_DIV_TURN_OFF = 'Выключить 📴'

    TEXT_PRICE_DIV_TURNED_OFF = 'Уведомления о расхождении цен выключены.'

    TEXT_PRICE_DIV_MAX_PERCENT = (
        'Хорошо!\n'
        'А теперь введите <b>максимальный</b> процент отклонения (<i>не более 100%</i>).\n'
        'Если вы не хотите уведомлений с максимальной стороны, нажмите "Далее"'
    )

    TEXT_PRICE_DIV_INVALID_NUMBER = '<code>Не правильное число!</code> Попробуйте еще раз.'

    @staticmethod
    def text_price_div_finish_setup(min_percent, max_percent):
        message = '✔️ Готово!\n'
        if min_percent is None and max_percent is None:
            message += '🔘 Вы <b>не</b> будете получать уведомления о расхождении цен.'
        else:
            message += 'Ваши триггеры:\n'
            if min_percent:
                message += f'→ Расхождение цен Рун &lt;= {pretty_money(min_percent)}%\n'
            if max_percent:
                message += f'→ Расхождение цен Рун &gt;= {pretty_money(max_percent)}%\n'
        return message.strip()

    def notification_text_price_divergence(self, info: RuneMarketInfo, is_low: bool):
        title = f'〰 Низкое расхождение цены!' if is_low else f'🔺 Высокое расхождение цены!'

        div, div_p = info.divergence_abs, info.divergence_percent
        text = (
            f"🖖 {bold(title)}\n"
            f"Цена BEP2 Руны (на биржах): {code(pretty_dollar(info.cex_price))}\n"
            f"Взвешенная цена Руны в пулах: {code(pretty_dollar(info.pool_rune_price))}\n"
            f"<b>Расхождение</b> нативной руны и BEP2 руны: {code(pretty_dollar(div))} ({div_p:.1f}%)."
        )

        return text

    # -------- METRICS ----------

    BUTTON_METR_S_FINANCIAL = '💱 Финансовые'
    BUTTON_METR_S_NET_OP = '🔩 Работа сети'

    BUTTON_METR_CAP = '✋ Кап ливкидности'
    BUTTON_METR_PRICE = f'💲 {BaseLocalization.R} инфо о цене'
    BUTTON_METR_QUEUE = f'👥 Очередь'
    BUTTON_METR_STATS = f'📊 Статистика'
    BUTTON_METR_NODES = '🖥 Ноды (узлы)'
    BUTTON_METR_LEADERBOARD = '🏆 Доска рекордов'
    BUTTON_METR_CHAINS = '⛓️ Блокчейны'
    BUTTON_METR_MIMIR = '🎅 Мимир'
    BUTTON_METR_VOTING = '🏛️ Голосование'
    BUTTON_METR_BLOCK_TIME = '⏱️ Время блоков'
    BUTTON_METR_TOP_POOLS = '🏊 Топ Пулов'
    BUTTON_METR_CEX_FLOW = '🌬 Поток бирж'
    BUTTON_METR_SUPPLY = f'🪙 Rune предложение'

    TEXT_METRICS_INTRO = 'Что вы хотите узнать?'

    def cap_message(self, info: ThorCapInfo):
        if info.can_add_liquidity:
            rune_vacant = info.how_much_rune_you_can_lp
            usd_vacant = rune_vacant * info.price
            more_info = f'🤲🏻 Можно добавить еще {bold(pretty_money(rune_vacant) + " " + RAIDO_GLYPH)} {self.R} ' \
                        f'или {bold(pretty_dollar(usd_vacant))}.\n👉🏻 {self.thor_site()}'
        else:
            more_info = '🛑 Вы не можете добавлять ликвидность сейчас. Дождитесь уведомления о поднятии капы!'

        return (
            f"<b>{pretty_money(info.pooled_rune)} {RAIDO_GLYPH} {self.R}</b> монет из "
            f"<b>{pretty_money(info.cap)} {RAIDO_GLYPH} {self.R}</b> сейчас в пулах.\n"
            f"{self._cap_progress_bar(info)}\n"
            f"{more_info}\n"
            f"Цена {bold(self.R)} сейчас <code>{info.price:.3f} $</code>.\n"
        )

    def text_leaderboard_info(self):
        return f"🏆 Доска лушчих трейдеров THORChain:\n" \
               f"\n" \
               f" 👉 {bold(URL_LEADERBOARD_MCCN)} 👈\n"

    def queue_message(self, queue_info: QueueInfo):
        return (
                   f"<b>Информация об очередях:</b>\n"
                   f"Исходящие транзакции (outbound): {code(queue_info.outbound)} шт.\n"
                   f"Очередь обменов (swap): {code(queue_info.swap)} шт.\n"
                   f"Внутренняя очередь (internal): {code(queue_info.internal)} шт.\n"
               ) + (
                   f"Если в очереди много транзакций, ваши операции могут занять гораздо больше времени, чем обычно."
                   if queue_info.is_full else ''
               )

    TEXT_PRICE_INFO_ASK_DURATION = 'За какой период времени вы хотите получить график?'

    BUTTON_1_HOUR = '1 часов'
    BUTTON_24_HOURS = '24 часа'
    BUTTON_1_WEEK = '1 неделя'
    BUTTON_30_DAYS = '30 дней'

    # ------- AVATAR -------

    TEXT_AVA_WELCOME = '🖼️ Скинь мне квадратное фото, и я сделаю для тебя аватар в стиле THORChain ' \
                       'с градиентной рамкой. Можешь отправить мне картинку как документ, ' \
                       'чтобы избежать проблем потерей качества из-за сжатия.'

    TEXT_AVA_ERR_INVALID = '⚠️ Фото неправильного формата!'
    TEXT_AVA_ERR_NO_PIC = '⚠️ Не удалось загрузить твое фото из профиля!'
    TEXT_AVA_READY = '🥳 <b>Твой THORChain аватар готов!</b> ' \
                     'Скачай это фото и установи его в Телеграм и социальных сетях.'

    BUTTON_AVA_FROM_MY_USERPIC = '😀 Из фото профиля'

    # ------- NETWORK SUMMARY -------

    def network_bond_security_text(self, network_security_ratio):
        if network_security_ratio > 0.9:
            return "🥱 НЕЭФФЕКТИВНА"
        elif 0.9 >= network_security_ratio > 0.75:
            return "🥸 ПЕРЕОБЕСПЕЧЕНА"
        elif 0.75 >= network_security_ratio >= 0.6:
            return "⚡ ОПТИМАЛЬНА"
        elif 0.6 > network_security_ratio >= 0.5:
            return "🤢 НЕДООБЕСПЕЧЕНА"
        elif network_security_ratio == 0:
            return '🚧 ДАННЫЕ НЕ ПОЛУЧЕНЫ...'
        else:
            return "🤬 НЕБЕЗОПАСНА"

    def notification_text_network_summary(self,
                                          old: NetworkStats, new: NetworkStats,
                                          market: RuneMarketInfo,
                                          killed: KilledRuneEntry):
        message = bold('🌐 THORChain статистика') + '\n'

        message += '\n'

        security_pb = progressbar(new.network_security_ratio, 1.0, 12) if new.network_security_ratio != 0 else ''
        security_text = self.network_bond_security_text(new.network_security_ratio)
        message += f'🕸️ Сейчас сеть {bold(security_text)} {security_pb}.\n'

        active_nodes_change = bracketify(up_down_arrow(old.active_nodes, new.active_nodes, int_delta=True))
        standby_nodes_change = bracketify(up_down_arrow(old.active_nodes, new.active_nodes, int_delta=True))
        message += f"🖥️ {bold(new.active_nodes)} активных нод{active_nodes_change} " \
                   f"и {bold(new.standby_nodes)} нод в режиме ожидания{standby_nodes_change}.\n"

        # -- BOND

        current_bond_text = bold(short_rune(new.total_active_bond_rune))
        current_bond_change = bracketify(
            up_down_arrow(old.total_active_bond_rune, new.total_active_bond_rune, money_delta=True))

        current_bond_usd_text = bold(short_dollar(new.total_active_bond_usd))
        current_bond_usd_change = bracketify(
            up_down_arrow(old.total_active_bond_usd, new.total_active_bond_usd, money_delta=True, money_prefix='$')
        )

        current_total_bond_text = bold(short_rune(new.total_bond_rune))
        current_total_bond_change = bracketify(
            up_down_arrow(old.total_bond_rune, new.total_bond_rune, money_delta=True))

        current_total_bond_usd_text = bold(short_dollar(new.total_bond_usd))
        current_total_bond_usd_change = bracketify(
            up_down_arrow(old.total_bond_usd, new.total_bond_usd, money_delta=True, money_prefix='$')
        )

        message += f"🔗 Бонд активных нод: {current_bond_text}{current_bond_change} или " \
                   f"{current_bond_usd_text}{current_bond_usd_change}.\n"

        message += f"🔗 Бонд всех нод: {current_total_bond_text}{current_total_bond_change} или " \
                   f"{current_total_bond_usd_text}{current_total_bond_usd_change}.\n"

        # -- POOL

        current_pooled_text = bold(short_rune(new.total_rune_pooled))
        current_pooled_change = bracketify(
            up_down_arrow(old.total_rune_pooled, new.total_rune_pooled, money_delta=True))

        current_pooled_usd_text = bold(short_dollar(new.total_pooled_usd))
        current_pooled_usd_change = bracketify(
            up_down_arrow(old.total_pooled_usd, new.total_pooled_usd, money_delta=True, money_prefix='$'))

        message += f"🏊 Всего в пулах: {current_pooled_text}{current_pooled_change} или " \
                   f"{current_pooled_usd_text}{current_pooled_usd_change}.\n"

        # -- LIQ

        current_liquidity_usd_text = bold(short_dollar(new.total_liquidity_usd))
        current_liquidity_usd_change = bracketify(
            up_down_arrow(old.total_liquidity_usd, new.total_liquidity_usd, money_delta=True, money_prefix='$'))

        message += f"🌊 Всего ликвидности (TVL): {current_liquidity_usd_text}{current_liquidity_usd_change}.\n"

        # -- TVL

        tlv_change = bracketify(
            up_down_arrow(old.total_locked_usd, new.total_locked_usd, money_delta=True, money_prefix='$'))
        message += f'🏦 TVL + бонды нод: {code(short_dollar(new.total_locked_usd))}{tlv_change}.\n'

        # -- RESERVE

        reserve_change = bracketify(up_down_arrow(old.reserve_rune, new.reserve_rune,
                                                  postfix=RAIDO_GLYPH, money_delta=True))

        message += f'💰 Резервы: {bold(short_rune(new.reserve_rune))}{reserve_change}.\n'

        # --- FLOWS:

        message += '\n'

        if old.is_ok:
            # 24 h Add/withdrawal
            added_24h_rune = new.added_rune - old.added_rune
            withdrawn_24h_rune = new.withdrawn_rune - old.withdrawn_rune
            swap_volume_24h_rune = new.swap_volume_rune - old.swap_volume_rune
            switched_24h_rune = new.switched_rune - old.switched_rune

            add_rune_text = bold(short_rune(added_24h_rune))
            withdraw_rune_text = bold(short_rune(withdrawn_24h_rune))
            swap_rune_text = bold(short_rune(swap_volume_24h_rune))
            switch_rune_text = bold(short_rune(switched_24h_rune))

            price = new.usd_per_rune

            add_usd_text = short_dollar(added_24h_rune * price)
            withdraw_usd_text = short_dollar(withdrawn_24h_rune * price)
            swap_usd_text = short_dollar(swap_volume_24h_rune * price)
            switch_usd_text = short_dollar(switched_24h_rune * price)

            message += f'{ital("За последние 24 часа:")}\n'

            if added_24h_rune:
                message += f'➕ Добавлено в пулы: {add_rune_text} ({add_usd_text}).\n'
            if withdrawn_24h_rune:
                message += f'➖ Выведено из пулов: {withdraw_rune_text} ({withdraw_usd_text}).\n'
            if swap_volume_24h_rune:
                message += f'🔀 Объем торгов: {swap_rune_text} ({swap_usd_text}) ' \
                           f'при {bold(new.swaps_24h)} обменов совершено.\n'
            if switched_24h_rune:
                message += f'💎 Rune конвертировано в нативные: {switch_rune_text} ({switch_usd_text}).\n'

            # synthetics:
            synth_volume_rune = code(short_rune(new.synth_volume_24h))
            synth_volume_usd = code(short_dollar(new.synth_volume_24h_usd))
            synth_op_count = short_money(new.synth_op_count)

            message += f'💊 Объем торговли синтетиками: {synth_volume_rune} ({synth_volume_usd}) ' \
                       f'путем {synth_op_count} обменов 🆕\n'

            if new.loss_protection_paid_24h_rune:
                ilp_rune_str = code(short_rune(new.loss_protection_paid_24h_rune))
                ilp_usd_str = code(short_dollar(new.loss_protection_paid_24h_rune * new.usd_per_rune))
                message += f'🛡️ Выплачено страховки от IL сегодня: {ilp_rune_str} ({ilp_usd_str}) 🆕\n'

            message += '\n'

        # switched ----
        switch_rune_total_text = bold(short_rune(new.switched_rune))
        message += (
            f'💎 Всего Rune перевели в нативные: {switch_rune_total_text} '
            f'({format_percent(new.switched_rune, market.total_supply)}).\n'
        )

        if killed.block_id:
            rune_left = bold(short_rune(killed.unkilled_unswitched_rune))
            switched_killed = bold(short_rune(killed.killed_switched))  # killed when switched
            total_killed = bold(short_rune(killed.total_killed))  # potentially dead + switched killed
            message += (
                f'☠️ Убито Рун при апргейде {switched_killed}, '
                f'всего убито Рун: {total_killed}, '
                f'неапгрейднутых Рун осталось: {rune_left}\n'
            )

        message += '\n'

        # API ---

        bonding_apy_change, liquidity_apy_change = self._extract_apy_deltas(new, old)
        message += (
            f'📈 Доход от бондов в нодах, годовых: '
            f'{code(pretty_money(new.bonding_apy, postfix="%"))}{bonding_apy_change} и '
            f'доход от пулов в среднем, годовых: '
            f'{code(pretty_money(new.liquidity_apy, postfix="%"))}{liquidity_apy_change}.\n'
        )

        message += (
            f'🛡️ Всего выплачено страховки от IL (непостоянных потерь): '
            f'{code(short_dollar(new.loss_protection_paid_usd))}.\n')

        if new.users_daily or new.users_monthly:
            daily_users_change = bracketify(up_down_arrow(old.users_daily, new.users_daily, int_delta=True))
            monthly_users_change = bracketify(up_down_arrow(old.users_monthly, new.users_monthly, int_delta=True))
            message += f'👥 Пользователей за день: {code(new.users_daily)}{daily_users_change}, ' \
                       f'пользователей за месяц: {code(new.users_monthly)}{monthly_users_change} 🆕\n'
            message += '\n'

        active_pool_changes = bracketify(up_down_arrow(old.active_pool_count,
                                                       new.active_pool_count, int_delta=True))
        pending_pool_changes = bracketify(up_down_arrow(old.pending_pool_count,
                                                        new.pending_pool_count, int_delta=True))
        message += f'{bold(new.active_pool_count)} активных пулов{active_pool_changes} и ' \
                   f'{bold(new.pending_pool_count)} ожидающих активации пулов{pending_pool_changes}.\n'

        if new.next_pool_to_activate:
            next_pool_wait = self.seconds_human(new.next_pool_activation_ts - now_ts())
            next_pool = self.pool_link(new.next_pool_to_activate)
            message += f"Вероятно, будет активирован пул: {next_pool} через {next_pool_wait}."
        else:
            message += f"Пока что нет достойного пула для активации."

        return message

    # ------- NETWORK NODES -------

    TEXT_PIC_ACTIVE_NODES = 'Активные'
    TEXT_PIC_STANDBY_NODES = 'Ожидающие'
    TEXT_PIC_ALL_NODES = 'Все ноды'
    TEXT_PIC_NODE_DIVERSITY = 'Распределение нод'
    TEXT_PIC_NODE_DIVERSITY_SUBTITLE = 'по провайдеру инфраструктуры'
    TEXT_PIC_OTHERS = 'Другие'
    TEXT_PIC_UNKNOWN = 'Не известно'

    def _format_node_text(self, node: NodeInfo, add_status=False, extended_info=False, expand_link=False):
        if expand_link:
            node_ip_link = link(get_ip_info_link(node.ip_address), node.ip_address) if node.ip_address else 'No IP'
        else:
            node_ip_link = node.ip_address or 'no IP'

        thor_explore_url = get_explorer_url_to_address(self.cfg.network_id, Chains.THOR, node.node_address)
        node_thor_link = link(thor_explore_url, short_address(node.node_address, 0))

        node_status = node.status.lower()
        if node_status == node.STANDBY:
            status = 'Ожидание'
        elif node_status == node.ACTIVE:
            status = 'Активна'
        elif node_status == node.DISABLED:
            status = 'Отключена!'
        else:
            status = node.status

        extra = ''
        if extended_info:
            if node.slash_points:
                extra += f", {bold(node.slash_points)} штрафов"
            if node.current_award:
                award_text = bold(pretty_money(node.current_award, postfix=RAIDO_GLYPH))
                extra += f", {award_text} награды"

        status = f', ({status})' if add_status else ''
        return f'{bold(node_thor_link)} ({node.flag_emoji}{node_ip_link}, версия {node.version}) ' \
               f'с {bold(pretty_money(node.bond, postfix=RAIDO_GLYPH))} бонд {status}{extra}'.strip()

    def _node_bond_change_after_churn(self, changes: NodeSetChanges):
        bond_in, bond_out = changes.bond_churn_in, changes.bond_churn_out
        bond_delta = bond_in - bond_out
        return f'Изменение активного бонда: {code(short_money(bond_delta, postfix=RAIDO_GLYPH))}'

    def notification_text_for_node_churn(self, changes: NodeSetChanges):
        message = ''

        if changes.nodes_activated or changes.nodes_deactivated:
            message += bold('♻️ Перемешивание нод') + '\n\n'

        message += self._make_node_list(changes.nodes_added, '🆕 Новые ноды появились:', add_status=True)
        message += self._make_node_list(changes.nodes_activated, '➡️ Ноды активироны:')
        message += self._make_node_list(changes.nodes_deactivated, '⬅️️ Ноды деактивированы:')
        message += self._make_node_list(changes.nodes_removed, '🗑️ Ноды отключились или исчезли:', add_status=True)

        if changes.nodes_activated or changes.nodes_deactivated:
            message += self._node_bond_change_after_churn(changes)

        return message.rstrip()

    def node_list_text(self, nodes: List[NodeInfo], status, items_per_chunk=12):
        add_status = False
        if status == NodeInfo.ACTIVE:
            title = '✅ Активные ноды:'
            nodes = [n for n in nodes if n.is_active]
        elif status == NodeInfo.STANDBY:
            title = '⏱ Ожидающие активации ноды:'
            nodes = [n for n in nodes if n.is_standby]
        else:
            title = '❔ Ноды в других статусах:'
            nodes = [n for n in nodes if n.in_strange_status]
            add_status = True

        groups = list(grouper(items_per_chunk, nodes))

        starts = []
        current_start = 1
        for group in groups:
            starts.append(current_start)
            current_start += len(group)

        return [
            self._make_node_list(group,
                                 title if start == 1 else '',
                                 extended_info=True,
                                 add_status=add_status,
                                 start=start).rstrip()
            for start, group in zip(starts, groups)
        ]

    # ------ VERSION ------

    @staticmethod
    def node_version(v, data: NodeSetChanges, active=True):
        realm = data.active_only_nodes if active else data.nodes_all
        n_nodes = len(data.find_nodes_with_version(realm, v))
        return f"{code(v)} ({n_nodes} {plural(n_nodes, 'node', 'nodes')})"

    def notification_text_version_upgrade_progress(self,
                                                   data: NodeSetChanges,
                                                   ver_con: NodeVersionConsensus):
        msg = bold('🕖 Прогресс обновления протокола THORChain\n\n')

        progress = ver_con.ratio * 100.0
        pb = progressbar(progress, 100.0, 14)

        msg += f'{pb} {progress:.0f} %\n'
        msg += f"{pre(ver_con.top_version_count)} из {pre(ver_con.total_active_node_count)} нод " \
               f"обновились до версии {pre(ver_con.top_version)}\n\n"

        cur_version_txt = self.node_version(data.current_active_version, data, active=True)
        msg += f"⚡️ Активная версия протокола сейчас – {cur_version_txt}\n" + \
               ital('* Это минимальная версия среди всех активных нод.') + '\n\n'

        return msg

    def notification_text_version_upgrade(self,
                                          data: NodeSetChanges,
                                          new_versions: List[VersionInfo],
                                          old_active_ver: VersionInfo,
                                          new_active_ver: VersionInfo):

        msg = bold('💫 Обновление версии протокола THORChain') + '\n\n'

        def version_and_nodes(v, all=False):
            realm = data.nodes_all if all else data.active_only_nodes
            n_nodes = len(data.find_nodes_with_version(realm, v))
            return f"{code(v)} ({n_nodes} {plural(n_nodes, 'нода', 'нод')})"

        current_active_version = data.current_active_version

        if new_versions:
            new_version_joined = ', '.join(version_and_nodes(v, all=True) for v in new_versions)
            msg += f"🆕 Обнаружена новая версия: {new_version_joined}\n\n"

            msg += f"⚡️ Активная версия протокола сейчас – {version_and_nodes(current_active_version)}\n" + \
                   ital('* Это минимальная версия среди всех активных нод.') + '\n\n'

        if old_active_ver != new_active_ver:
            action = 'улучшилась' if new_active_ver > old_active_ver else 'откатилась'
            emoji = '🆙' if new_active_ver > old_active_ver else '⬇️'
            msg += (
                f"{emoji} {bold('Внимание!')} Активная версия протокола {bold(action)} "
                f"с версии {pre(old_active_ver)} "
                f"до версии {version_and_nodes(new_active_ver)}\n\n"
            )

            cnt = data.version_counter(data.active_only_nodes)
            if len(cnt) == 1:
                msg += f"Все активные ноды имеют версию {code(current_active_version)}\n"
            elif len(cnt) > 1:
                msg += bold(f"Самые популярные версии нод:") + '\n'
                for i, (v, count) in enumerate(cnt.most_common(5), start=1):
                    active_node = ' 👈' if v == current_active_version else ''
                    msg += f"{i}. {version_and_nodes(v)} {active_node}\n"
                msg += f"Максимальная доступная версия – {version_and_nodes(data.max_available_version)}\n"

        return msg

    # --------- CHAIN INFO SUMMARY ------------

    def text_chain_info(self, chain_infos: List[ThorChainInfo]):
        text = '⛓️ ' + bold('THORChain подключен к блокчейнам:') + '\n\n'
        for c in chain_infos:
            address_link = link(get_explorer_url_to_address(self.cfg.network_id, c.chain, c.address), 'СКАН')
            status = '🛑 Остановлен' if c.halted else '🆗 Активен'
            text += f'{bold(c.chain)}:\n' \
                    f'Статус: {status}\n' \
                    f'Входящий адрес: {pre(c.address)} {address_link}\n'

            if c.router:
                router_link = link(get_explorer_url_to_address(self.cfg.network_id, c.chain, c.router), 'СКАН')
                text += f'Роутер: {pre(c.router)} {router_link}\n'

            text += f'Цена газа: {pre(c.gas_rate)}\n\n'

        if not chain_infos:
            text += 'Инфо о блокчейнах еще не загружено...'

        return text.strip()

    # --------- MIMIR INFO ------------

    MIMIR_STANDARD_VALUE = "стандарт:"
    MIMIR_OUTRO = f'\n\n🔹 – {ital("Админ Мимир")}\n' \
                  f'🔸 – {ital("Голосование нод")}\n' \
                  f'▪️ – {ital("Автоматика")}'
    MIMIR_NO_DATA = 'Нет данных'
    MIMIR_BLOCKS = 'блоков'
    MIMIR_DISABLED = 'ВЫКЛЮЧЕНО'
    MIMIR_YES = 'ДА'
    MIMIR_NO = 'НЕТ'
    MIMIR_UNDEFINED = 'неопределено'
    MIMIR_LAST_CHANGE = 'Последнее изменение'
    MIMIR_UNKNOWN_CHAIN = 'Неизв. сеть'

    def text_mimir_intro(self):
        text = f'🎅 {bold("Глобальные константы и Мимир")}\n'
        cheatsheet_link = link(self.MIMIR_CHEAT_SHEET_URL, 'Описание констант')
        what_is_mimir_link = link(self.MIMIR_DOC_LINK, "Что такое Мимир?")
        text += f"{what_is_mimir_link} А еще {cheatsheet_link}.\n\n"
        return text

    def text_node_mimir_voting(self, holder: MimirHolder):
        title = '🏛️' + bold('Голосование нод за Мимир') + '\n\n'
        if not holder.voting_manager.all_voting:
            title += 'Пока нет активных логосований.'
            return [title]

        messages = [title]
        for voting in holder.voting_manager.all_voting.values():
            voting: MimirVoting
            name = holder.pretty_name(voting.key)
            msg = f"{bold(name)}\n"

            for option in voting.top_options:
                pb = self.make_voting_progress_bar(option, voting)
                extra = self._text_votes_to_pass(option)
                units = MimirUnits.get_mimir_units(voting.key)
                pretty_value = self.format_mimir_value(voting.key, str(option.value), units)
                msg += f"➔ чтобы стало {code(pretty_value)}: " \
                       f"{bold(format_percent(option.number_votes, voting.active_nodes))}" \
                       f" ({option.number_votes}/{voting.active_nodes}) {pb} {extra}\n"

            messages.append(msg)

        return regroup_joining(self.NODE_MIMIR_VOTING_GROUP_SIZE, messages)

    def _text_votes_to_pass(self, option):
        show = 0 < option.need_votes_to_pass <= self.NEED_VOTES_TO_PASS_MAX
        return f'{option.need_votes_to_pass} еще голосов, чтобы прошло' if show else ''

    def notification_text_mimir_voting_progress(self, holder: MimirHolder, key, prev_progress,
                                                voting: MimirVoting,
                                                option: MimirVoteOption):
        message = '🏛️' + bold('Прогресс голосования нод за Мимир') + '\n\n'

        name = holder.pretty_name(key)
        message += f"{code(name)}\n"

        pb = self.make_voting_progress_bar(option, voting)
        percent = format_percent(option.number_votes, voting.active_nodes)
        extra = (f'{option.need_votes_to_pass} еще голосов, чтобы прошло'
                 if option.need_votes_to_pass <= self.NEED_VOTES_TO_PASS_MAX else '')
        message += f"➔ чтобы стало {code(option.value)}: {bold(percent)}" \
                   f" ({option.number_votes}/{voting.active_nodes}) {pb} {extra}\n"
        return message

    # --------- TRADING HALTED -----------

    def notification_text_trading_halted_multi(self, chain_infos: List[ThorChainInfo]):
        msg = ''

        halted_chains = ', '.join(c.chain for c in chain_infos if c.halted)
        if halted_chains:
            msg += f'🚨🚨🚨 <b>Внимание!</b> Торговля остановлена на блокчейнах: {code(halted_chains)}! ' \
                   f'Воздержитесь от обменов, пока торговля не будет снова запущена! 🚨🚨🚨\n\n'

        resumed_chains = ', '.join(c.chain for c in chain_infos if not c.halted)
        if resumed_chains:
            msg += f'✅ <b>Внимание!</b> Торговля снова возобновлена на блокчейнах: {code(resumed_chains)}!'

        return msg.strip()

    # ---------- BLOCK HEIGHT -----------

    TEXT_BLOCK_HEIGHT_CHART_TITLE = 'THORChain блоков в минут'
    TEXT_BLOCK_HEIGHT_LEGEND_ACTUAL = 'Фактически блоков в минуту'
    TEXT_BLOCK_HEIGHT_LEGEND_EXPECTED = 'Ожидаемая (10 бл/мин или 6 сек на блок)'

    def notification_text_block_stuck(self, e: EventBlockSpeed):
        good_time = e.time_without_blocks is not None and e.time_without_blocks > 1
        str_t = ital(self.seconds_human(e.time_without_blocks) if good_time else self.NA)
        if e.state == BlockProduceState.StateStuck:
            return f'📛 {bold("THORChain высота блоков перестала увеличиваться")}!\n' \
                   f'Новые блоки не генерируются уже {str_t}.'
        else:
            return f"🆗 {bold('THORChain снова генерирует блоки!')}\n" \
                   f"Сбой длился {str_t}"

    @staticmethod
    def get_block_time_state_string(state, state_changed):
        if state == BlockProduceState.NormalPace:
            if state_changed:
                return '👌 Скорость генерации блоков вернулась к нормальной.'
            else:
                return '👌 Скорость генерации блоков в норме.'
        elif state == BlockProduceState.TooSlow:
            return '🐌 Блоки производятся слишком медленно.'
        elif state == BlockProduceState.TooFast:
            return '🏃 Блоки производятся слишком быстро.'
        else:
            return ''

    def notification_text_block_pace(self, e: EventBlockSpeed):
        phrase = self.get_block_time_state_string(e.state, True)
        block_per_minute = self.format_bps(e.block_speed)

        return (
            f'<b>Обновление по скорости производства блоков THORChain</b>\n'
            f'{phrase}\n'
            f'В настоящий момент <code>{block_per_minute}</code> блоков в минуту, другими словами '
            f'нужно <code>{self.format_block_time(e.block_speed)} сек</code> на создание блока.'
        )

    def text_block_time_report(self, last_block, last_block_ts, recent_bps, state):
        phrase = self.get_block_time_state_string(state, False)
        block_per_minute = self.format_bps(recent_bps)
        ago = self.format_time_ago(last_block_ts)
        block_str = f"#{last_block}"
        return (
            f'<b>THORChain темпы производства блоков.</b>\n'
            f'{phrase}\n'
            f'В настоящее время <code>{block_per_minute}</code> блоков в минуту, другими словами'
            f'нужно <code>{self.format_block_time(block_per_minute)} сек</code> на создание блока.\n'
            f'Последний номер блока THORChain: {code(block_str)} (обновлено: {ago}).'
        )

    # --------- MIMIR CHANGED -----------

    def notification_text_mimir_changed(self, changes: List[MimirChange], mimir: MimirHolder):
        if not changes:
            return ''

        text = '🔔 <b>Обновление Мимир!</b>\n\n'

        for change in changes:
            old_value_fmt = code(self.format_mimir_value(change.entry.name, change.old_value, change.entry.units))
            new_value_fmt = code(self.format_mimir_value(change.entry.name, change.new_value, change.entry.units))
            name = code(change.entry.pretty_name if change.entry else change.name)

            e = change.entry
            if e:
                if e.source == e.SOURCE_AUTO:
                    text += bold('[🤖 Автоматика платежеспособности ]  ')
                elif e.source == e.SOURCE_ADMIN:
                    text += bold('[👩‍💻 Администраторы ]  ')
                elif e.source == e.SOURCE_NODE:
                    text += bold('[🤝 Голосование нод ]  ')
                elif e.source == e.SOURCE_NODE_CEASED:
                    text += bold('[💔 Мимир нод отменен ]  ')

            if change.kind == MimirChange.ADDED_MIMIR:
                text += (
                    f'➕ Настройка "{name}" теперь переопределена новым Мимиром. '
                    f'Старое значение по умолчанию было: {old_value_fmt} → '
                    f'новое значение стало: {new_value_fmt}‼️'
                )
            elif change.kind == MimirChange.REMOVED_MIMIR:
                text += f'➖ Настройка Мимира "{name}" была удалена! Ранее она имела значение: {old_value_fmt}.'
                if change.new_value is not None:
                    text += f' Теперь она вернулась к исходной константе: {new_value_fmt}‼️'
            else:
                text += (
                    f'🔄 Настройка Мимира "{name}" была изменена. '
                    f'Старое значение: {old_value_fmt} → '
                    f'новое значение теперь: {new_value_fmt}‼️'
                )
                if change.entry.automatic:
                    text += f' (на блоке #{ital(change.non_zero_value)}).'
            text += '\n\n'

        text += link("https://docs.thorchain.org/how-it-works/governance#mimir", "Что такое Mimir?")

        return text

    # ------- NODE OP TOOLS -------

    BUTTON_NOP_ADD_NODES = '➕ Добавь ноды'
    BUTTON_NOP_MANAGE_NODES = '🖊️ Редактировать'
    BUTTON_NOP_SETTINGS = '⚙️ Настройки'
    BUTTON_NOP_GET_SETTINGS_LINK = '⚙️ Настройка на сайте New!'

    def pretty_node_desc(self, node: NodeInfo, name=None):
        addr = self.short_node_name(node.node_address, name)
        return f'{pre(addr)} ({bold(short_money(node.bond, prefix="R"))} бонд)'

    TEXT_NOP_INTRO_HEADING = bold('Добро пожаловать в Инстременты Операторов Нод.')

    def text_node_op_welcome_text_part2(self, watch_list: list, last_signal_ago: float):
        text = 'Мы будем отправлять вам персонифицированные уведомления ' \
               'когда что-то важное случается с нодами, которые вы мониторите.\n\n'
        if watch_list:
            text += f'У вас {len(watch_list)} нод в списке слежения.'
        else:
            text += f'Вы не добавили еще пока ни одной ноды в список слежения. ' \
                    f'Нажмите "{ital(self.BUTTON_NOP_ADD_NODES)}" сперва 👇.'

        text += f'\n\nПоследний сигнал был: {ital(self.format_time_ago(last_signal_ago))}'
        if last_signal_ago > 60:
            text += '🔴'
        elif last_signal_ago > 20:
            text += '🟠'
        else:
            text += '🟢'

        return text

    TEXT_NOP_MANAGE_LIST_TITLE = \
        'Вы добавили <pre>{n}</pre> нод в ваш список слежения. ' \
        'Вы можете убрать ноды из списка слежения, нажав на кпонки снизу.'

    TEXT_NOP_ADD_INSTRUCTIONS = '🤓 Если вам уже известны адреса интересующих вас нод, ' \
                                f'пожалуйста, отправьте мне их списком через сообщение. ' \
                                f'Вы можете использовать полный адрес {pre("thorAbc5andD1so2on")} или ' \
                                f'последние 3 или более символов. ' \
                                f'Имена нод в списке могут быть разделены пробелами, запятыми или энтерами.\n\n' \
                                f'Пример: {pre("66ew, xqmm, 7nv9")}'
    BUTTON_NOP_ADD_ALL_NODES = 'Добавить все ноды'
    BUTTON_NOP_ADD_ALL_ACTIVE_NODES = 'Добавить все активные'

    TEXT_NOP_SEARCH_NO_VARIANTS = 'Совпадений не найдено! Попробуйте уточнить свой запрос ' \
                                  'или воспользуйтесь списком для поиска нужных нод.'
    TEXT_NOP_SEARCH_VARIANTS = 'Мы нашли следующие ноды, подходящие под ваш поисковый запрос:'

    TEXT_NOP_SETTINGS_TITLE = 'Настройте ваши уведомления здесь. Выберите тему для настройки:'

    def text_nop_get_weblink_title(self, link):
        return f'Ваша ссылка для настройки готова: {link}!\n' \
               f'Там вы сможете выбрать ноды для мониторинга и настроить уведомления.'

    BUTTON_NOP_SETT_OPEN_WEB_LINK = '🌐 Открыть в браузере'
    BUTTON_NOP_SETT_REVOKE_WEB_LINK = '🤜 Отозвать ссылку'

    TEXT_NOP_REVOKED_URL_SUCCESS = 'Ссылка для настроек и токен были отозваны!'

    BUTTON_NOP_SETT_SLASHING = 'Штрафы'
    BUTTON_NOP_SETT_VERSION = 'Версии'
    BUTTON_NOP_SETT_OFFLINE = 'Оффлайн'
    BUTTON_NOP_SETT_CHURNING = 'Перемешивание'
    BUTTON_NOP_SETT_BOND = 'Бонд'
    BUTTON_NOP_SETT_HEIGHT = 'Высота блоков'
    BUTTON_NOP_SETT_IP_ADDR = 'IP адр.'
    BUTTON_NOP_SETT_PAUSE_ALL = 'Приостановить все уведомления'

    @staticmethod
    def text_enabled_disabled(is_on):
        return 'включены' if is_on else 'выключены'

    def text_nop_slash_enabled(self, is_on):
        en_text = self.text_enabled_disabled(is_on)
        return f'Уведомления о начислении штрафных очков нодам {bold(en_text)}.'

    def text_nop_bond_is_enabled(self, is_on):
        en_text = self.text_enabled_disabled(is_on)
        return f'Уведомления об изменении бонда {bold(en_text)}.'

    def text_nop_new_version_enabled(self, is_on):
        en_text = self.text_enabled_disabled(is_on)
        return f'Уведомления о появлении новой версии {bold(en_text)}.\n\n' \
               f'<i>На следующием шаге вы настроите уведомления об обновлении ваших нод.</i>'

    def text_nop_version_up_enabled(self, is_on):
        en_text = self.text_enabled_disabled(is_on)
        return f'Уведомления об обновлении версии ноды {bold(en_text)}.'

    def text_nop_offline_enabled(self, is_on):
        en_text = self.text_enabled_disabled(is_on)
        return f'Уведомления об уходе ноды в оффлайн и возврате в онлайн {bold(en_text)}.\n\n' \
               f'<i>На следующих шагах вы настроите сервисы.</i>'

    def text_nop_churning_enabled(self, is_on):
        en_text = self.text_enabled_disabled(is_on)
        return f'Уведомлении о перемешивании нод {bold(en_text)}.\n\n' \
               f'<i>Вы получите персональное уведомление, ' \
               f'если ваша нода вступает в активный набор нод или покидает его.</i>'

    def text_nop_ip_address_enabled(self, is_on):
        en_text = self.text_enabled_disabled(is_on)
        return f'Уведомления об смене IP адреса {bold(en_text)}.\n\n' \
               f'<i>Вы получите уведомление, если нода вдруг изменит свой IP адрес.</i>'

    def text_nop_ask_offline_period(self, current):
        return f'Какой лимит времени вы хотите установить для оффлайн уведомлений?\n\n' \
               f'Если с сервисами вашей ноды нет соединения в течении указанного времени, ' \
               f'то вы получите сообщение.\n\n' \
               f'Сейчас: {pre(self.seconds_human(current))}.'

    def text_nop_chain_height_enabled(self, is_on):
        en_text = self.text_enabled_disabled(is_on)
        return f'Уведомления о зависших клиентах блокчейнов {bold(en_text)}.\n\n' \
               f'<i>Вы получите уведомление, если ваши блокчейн клиенты на нодах перестали сканировать блоки.</i>'

    BUTTON_NOP_LEAVE_ON = '✔ Вкл.'
    BUTTON_NOP_LEAVE_OFF = '✔ Выкл.'
    BUTTON_NOP_TURN_ON = 'Вкл.'
    BUTTON_NOP_TURN_OFF = 'Выкл.'

    BUTTON_NOP_INTERVALS = {
        '2m': '2 мин',
        '5m': '5 мин',
        '15m': '15 мин',
        '30m': '30 мин',
        '60m': '1 час',
        '2h': '2 часа',
        '6h': '6 ч.',
        '12h': '12 ч.',
        '24h': '1 день',
        '3d': '3 дня',
    }

    TEXT_NOP_SLASH_THRESHOLD = 'Выберете порог для сообщений о ' \
                               'штрафных очках (рекомендуем в районе 5 - 10):'

    def text_nop_ask_slash_period(self, pts):
        return f'Отлично! Выберите период мониторинга.\n' \
               f'К примеру, если вы установите <i>10 минут</i> и порог <i>{pts} очков</i>, то ' \
               f'вы получите уведомление, если ваша нода наберет ' \
               f'<i>{pts} очков штрафа</i> за последние <i>10 минут</i>.'

    def text_nop_ask_chain_height_lag_time(self, current_lag_time):
        return 'Пожалуйста, выберите промежуток времени для порога уведомления. ' \
               'Если ваша нода не сканирует блоки более этого времени, то вы получите уведомление об этом.\n\n' \
               'Если пороговое время меньше типичного времени блока для какой-либо цепочки блоков, ' \
               'то оно будет увеличено до 150% от типичного времени (15 минут для BTC).'

    def text_nop_success_add_banner(self, node_addresses):
        node_addresses_text = ','.join([self.short_node_name(a) for a in node_addresses])
        node_addresses_text = shorten_text(node_addresses_text, 80)
        message = f'😉 Успех! {node_addresses_text} добавлены в ваш список. ' \
                  f'Ожидайте уведомлений, если произойдет что-то важное!'
        return message

    BUTTON_NOP_CLEAR_LIST = '🗑️ Очистить все ({n})'
    BUTTON_NOP_REMOVE_INACTIVE = '❌ Убрать неактивные ({n})'
    BUTTON_NOP_REMOVE_DISCONNECTED = '❌ Убрать отключенные ({n})'

    def text_nop_success_remove_banner(self, node_addresses):
        node_addresses_text = ','.join([self.short_node_name(a) for a in node_addresses])
        node_addresses_text = shorten_text(node_addresses_text, 120)
        return f'😉 Успех! Вы убрали ноды из вашего списка слежения: ' \
               f'{node_addresses_text} ({len(node_addresses)} всего).'

    def notification_text_for_node_op_changes(self, c: NodeEvent):
        message = ''
        short_addr = self.node_link(c.address)
        if c.type == NodeEventType.SLASHING:
            data: EventDataSlash = c.data
            date_str = self.seconds_human(data.interval_sec)
            message = f'🔪 Нода {short_addr} получила штраф ' \
                      f'на {bold(data.delta_pts)} очков ≈{date_str} ' \
                      f'(сейчас в сумме: <i>{data.current_pts}</i> штрафных очков)!'
        elif c.type == NodeEventType.VERSION_CHANGED:
            old, new = c.data
            message = f'🆙 Нода {short_addr} обновилась с версии {ital(old)} до {bold(new)}!'
        elif c.type == NodeEventType.NEW_VERSION_DETECTED:
            message = f'🆕 Новая версия ПО ноды обнаружена! {bold(c.data)}! Рассмотрите возможность обновиться!'
        elif c.type == NodeEventType.BOND:
            old, new = c.data
            message = f'⚖️ Нода {short_addr}: изменение бонда с ' \
                      f'{short_money(old, postfix=RAIDO_GLYPH)} ' \
                      f'до {bold(short_money(new, postfix=RAIDO_GLYPH))}!'
        elif c.type == NodeEventType.IP_ADDRESS_CHANGED:
            old, new = c.data
            message = f'🏤 Нода {short_addr} сменила свой IP адрес с {ital(old)} на {bold(new)}!'
        elif c.type == NodeEventType.SERVICE_ONLINE:
            online, duration, service = c.data
            service = bold(str(service).upper())
            if online:
                message = f'✅ Сервис {service} ноды {short_addr} опять вернулся в <b>онлайн</b>!'
            else:
                message = f'🔴 Сервис {service} ноды {short_addr} ушел в <b>оффлайн</b> ' \
                          f'(уже как {self.seconds_human(duration)})!'
        elif c.type == NodeEventType.CHURNING:
            verb = 'активировалась ⬅️' if c.data else 'вышла из активного набора ➡️'
            bond = c.node.bond
            message = f'🌐 Нода {short_addr} ({short_money(bond)} {RAIDO_GLYPH} бонда) {bold(verb)}!'
        elif c.type == NodeEventType.BLOCK_HEIGHT:
            data: EventBlockHeight = c.data

            if data.is_sync:
                message = f'✅ Нода {short_addr} догнала актуальные блоки на блокчейне {pre(data.chain)}.'
            else:
                message = f'🔴 Нода {short_addr} на {pre(data.block_lag)} позади ' \
                          f'на блокчейне {pre(data.chain)} (≈{self.seconds_human(data.how_long_behind)})!'
        elif c.type == NodeEventType.PRESENCE:
            if c.data:
                message = f'🙋 Нода {short_addr} снова вернулась в сеть THORChain!'
            else:
                message = f'⁉️ Нода {short_addr} исчезла из сети THORChain!'
        elif c.type == NodeEventType.TEXT_MESSAGE:
            text = str(c.data)[:self.NODE_OP_MAX_TEXT_MESSAGE_LENGTH]
            message = f'⚠️ Сообщение всем: {code(text)}'
        elif c.type == NodeEventType.CABLE_DISCONNECT:
            message = f'💔️ NodeOp инструменты <b>отключились</b> от сети THORChain.\n' \
                      f'Пожалуйста, воспользуйтсь альтернативными сервисами для мониторинга нод, ' \
                      f'пока мы не исправим проблему.'
        elif c.type == NodeEventType.CABLE_RECONNECT:
            message = f'💚 NodeOp инструменты снова подключились к THORChain.'

        return message

    # ------- BEST POOLS -------

    def notification_text_best_pools(self, pd: PoolDetailHolder, n_pools):
        no_pool_text = 'Пока ничего, наверное, еще грузится...'
        text = '\n\n'.join([self.format_pool_top(top_pools, pd, title, no_pool_text, n_pools) for title, top_pools in [
            ('💎 Лучшие годовые %', pd.BY_APY),
            ('💸 Большие объемы', pd.BY_VOLUME_24h),
            ('🏊 Максимальная ликвидность', pd.BY_DEPTH),
        ]])

        return text

    # ------------------------------------------

    DATE_TRANSLATOR = {
        'just now': 'прямо сейчас',
        'never': 'никогда',
        'sec': 'сек',
        'min': 'мин',
        'hour': 'час',
        'hours': 'час',
        'day': 'дн',
        'days': 'дн',
        'ago': 'назад',
    }

    def format_time_ago(self, d):
        return format_time_ago(d, translate=self.DATE_TRANSLATOR)

    def seconds_human(self, s):
        return seconds_human(s, translate=self.DATE_TRANSLATOR)

    # ----- RUNE FLOW ------

    def notification_text_cex_flow(self, bep2flow: RuneCEXFlow):
        return (f'🌬️ <b>Rune потоки с централизованнвых бирж последние сутки</b>\n'
                f'Завели: {pre(short_money(bep2flow.rune_cex_inflow, postfix=RAIDO_GLYPH))} '
                f'({short_dollar(bep2flow.in_usd)})\n'
                f'Вывели: {pre(short_money(bep2flow.rune_cex_outflow, postfix=RAIDO_GLYPH))} '
                f'({short_dollar(bep2flow.out_usd)})\n'
                f'Поток: {pre(short_money(bep2flow.rune_cex_netflow, postfix=RAIDO_GLYPH))} '
                f'({short_dollar(bep2flow.netflow_usd)})')

    # ----- SUPPLY ------

    SUPPLY_HELPER_TRANSLATOR = {
        'Team': 'Команда',
        'Seed': 'Сид-инвесторы',
        'Reserves': 'Резервы',
        'Undeployed reserves': 'Неразвернутые резервы',
        'Preburn': 'Готово к сожжению',
        'Asgard': 'Горят в Асгарде',
    }

    def format_supply_entry(self, name, s: SupplyEntry, total_of_total: int):
        if s.locked and s.total != total_of_total:
            items = '\n'.join(
                f'∙ {pre(self.SUPPLY_HELPER_TRANSLATOR.get(name, name))}: '
                f'{code(short_rune(amount))} ({format_percent(amount, total_of_total)})'
                for name, amount in s.locked.items()
            )
            locked_summary = f'Заблокировано:\n{items}\n'
        else:
            locked_summary = ''

        return (
            f'{bold(name)}:\n'
            f'Циркулирует: {code(short_rune(s.circulating))} ({format_percent(s.circulating, total_of_total)})\n'
            f'{locked_summary}'
            f'Всего монет: {code(short_rune(s.total))} ({format_percent(s.total, total_of_total)})\n\n'
        )

    def text_metrics_supply(self, market_info: RuneMarketInfo, killed_rune: KilledRuneEntry):
        supply = market_info.supply_info
        message = f'🪙 {bold("Предложение монет Rune")}\n\n'

        message += self.format_supply_entry('BNB.Rune (BEP2)', supply.bep2_rune, supply.overall.total)
        message += self.format_supply_entry('ETH.Rune (ERC20)', supply.erc20_rune, supply.overall.total)

        if killed_rune.block_id:
            rune_left = code(short_rune(killed_rune.unkilled_unswitched_rune))
            switched_killed = code(short_rune(killed_rune.killed_switched))  # killed when switched
            total_killed = code(short_rune(killed_rune.total_killed))  # potentially dead + switched killed
            lost_rune = code(short_rune(market_info.supply_info.lost_forever))
            message += (
                f'☠️ <b>Убито Рун при апгрейде:</b> {switched_killed}\n'
                f'Всего убито Рун: {total_killed}\n'
                f'Осталось старых Рун: {rune_left}\n'
                f'Потерянные навсегда Руны: {lost_rune}\n\n'
            )

        message += self.format_supply_entry('Нативная THOR.RUNE', supply.thor_rune, supply.overall.total)
        message += self.format_supply_entry('Всего всех видов', supply.overall, supply.overall.total)

        message += f"Капитализация {bold(self.R)}: {bold(short_dollar(market_info.market_cap))} " \
                   f"(место #{bold(market_info.rank)})"
        return message

    SUPPLY_PIC_TITLE = 'THORChain: запасы Руны'
    SUPPLY_PIC_CIRCULATING = 'Циркулирующие'
    SUPPLY_PIC_KILLED = 'Убитые'
    SUPPLY_PIC_KILLED_LOST = 'Убитые при апгрейде и потерянные'
    SUPPLY_PIC_TEAM = 'Команда'
    SUPPLY_PIC_SEED = 'Сид-инвесторы'
    SUPPLY_PIC_RESERVES = 'Резерв'
    SUPPLY_PIC_UNDEPLOYED = 'Неразвернутый резерв'
    SUPPLY_PIC_BONDED = 'Бонд в нодах'
    SUPPLY_PIC_POOLED = 'В пулах'
    SUPPLY_PIC_SECTION_CIRCULATING = 'Нативные циркулируют'
    SUPPLY_PIC_SECTION_LOCKED = 'Нативные заблокированы'
    SUPPLY_PIC_SECTION_OLD = 'Устаревшие'

    # ---- MY WALLET ALERTS ----

    TX_COMMENT_TABLE = {
        'Deposit': 'Депозит',
        'Send': 'Перевод',
        'Outbound': 'Исходящая',
        'OutboundTx': 'Исходящая',
    }

    def notification_text_rune_transfer(self, t: RuneTransfer, my_addresses):
        asset, comment, from_my, to_my, tx_link, usd_amt, memo = self._native_transfer_prepare_stuff(my_addresses, t)
        comment = self.TX_COMMENT_TABLE.get(comment, comment)

        return f'🏦 <b>{comment}</b>{tx_link}: {code(short_money(t.amount, postfix=" " + asset))} {usd_amt} ' \
               f'от {from_my} ' \
               f'➡️ к {to_my}{memo}.'

    def notification_text_rune_transfer_public(self, t: RuneTransfer):
        asset, comment, from_my, to_my, tx_link, usd_amt, memo = self._native_transfer_prepare_stuff(None, t,
                                                                                                     tx_title='')

        return f'💸 <b>Большой перевод</b> {tx_link}: ' \
               f'{code(short_money(t.amount, postfix=" " + asset))}{usd_amt} ' \
               f'от {from_my} ➡️ к {to_my}{memo}.'
