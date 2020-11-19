from localization.base import BaseLocalization
from services.models.price import RuneFairPrice, PriceReport
from services.models.pool_info import PoolInfo
from services.models.cap_info import ThorInfo
from services.models.tx import StakeTx, short_asset_name, StakePoolStats
from services.lib.utils import link, code, bold, pre, x_ses
from services.lib.money import pretty_dollar, pretty_money, short_address, adaptive_round_to_str, calc_percent_change, \
    emoji_for_percent_change


class RussianLocalization(BaseLocalization):
    # ---- WELCOME ----
    def help(self):
        return (
            f"Этот бот уведомляет о крупных движениях с сети {link('https://thorchain.org/', 'THORChain')}.\n"
            f"Команды:\n"
            f"/help – эта помощь\n"
            f"/start – запуск и установка языка\n"
            f"/cap – текущий кап для стейка в пулах Chaosnet\n"
            f"/price – текущая цена {self.R}.\n"
            f"<b>⚠️ Бот теперь уведомляет только в канале️ @thorchain_alert!</b>\n"
        )

    def welcome_message(self, info: ThorInfo):
        return (
            f"Привет! <b>{info.stacked:.0f}</b> монет из <b>{info.cap:.0f}</b> сейчас застейканы.\n"
            f"{self._cap_pb(info)}"
            f"Цена {self.R} сейчас <code>{info.price:.3f} BUSD</code>.\n"
            f"<b>⚠️ Бот теперь уведомляет только в канале️ @thorchain_alert!</b>\n"
            f"Набери /help, чтобы видеть список команд."
        )

    def unknown_command(self):
        return (
            "Извини, я не знаю такой команды.\n"
            "/help"
        )

    # ----- CAP ------
    def notification_cap_change_text(self, old: ThorInfo, new: ThorInfo):
        verb = "подрос" if old.cap < new.cap else "упал"
        call = "Ай-да застейкаем!\n" if new.cap > old.cap else ''
        return (
            f'<b>Кап {verb} с {pretty_money(old.cap)} до {pretty_money(new.cap)}!</b>\n'
            f'Сейчас в пулы помещено <b>{pretty_money(new.stacked)}</b> {self.R}.\n'
            f"{self._cap_pb(new)}"
            f'Цена {self.R} в пуле <code>{new.price:.3f} BUSD</code>.\n'
            f'{call}'
            f'https://chaosnet.bepswap.com/'
        )

    # ------ PRICE -------
    def price_message(self, info: ThorInfo, fair_price: RuneFairPrice):
        return (
            f"Последняя цена {self.R}: <code>{info.price:.3f} BUSD</code>.\n"
            f"Детерминистическая цена {self.R} сейчас: <code>${fair_price.fair_price:.3f}</code>."
        )

    # ------ TXS -------
    def tx_text(self, tx: StakeTx, dollar_per_rune: float, pool: StakePoolStats, pool_info: PoolInfo):
        msg = ''
        if tx.type == 'stake':
            msg += f'🐳 <b>Кит добавил ликвидности</b> 🟢\n'
        elif tx.type == 'unstake':
            msg += f'🐳 <b>Кит вывел ликвидность</b> 🔴\n'

        rp, ap = tx.symmetry_rune_vs_asset()
        total_usd_volume = tx.full_rune * dollar_per_rune if dollar_per_rune != 0 else 0.0
        pool_depth_usd = pool_info.usd_depth(dollar_per_rune)
        info = link(f'https://viewblock.io/thorchain/address/{tx.address}', short_address(tx.address))

        return (
            f"<b>{pretty_money(tx.rune_amount)} {self.R}</b> ({rp:.0f}%) ↔️ "
            f"<b>{pretty_money(tx.asset_amount)} {short_asset_name(tx.pool)}</b> ({ap:.0f}%)\n"
            f"Всего: <code>${pretty_money(total_usd_volume)}</code>\n"
            f"Глубина пула сейчас: <b>${pretty_money(pool_depth_usd)}</b>.\n"
            f"Смотреть: {info}"
        )

    # ------- QUEUE -------

    def queue_update(self, item_type, step, value):
        if step == 0:
            return f"☺️ Очередь {item_type} снова опустела!"
        else:
            return f"🤬 <b>Внимание!</b> Очередь {code(item_type)} имеет {value} транзакций!"

    # ------- PRICE -------

    def price_change(self, p: PriceReport, ath=False):
        title = bold('Обновление цены') if not ath else bold('🚀 Достигнуть новый исторический максимум!')

        c_gecko_url = 'https://www.coingecko.com/ru/%D0%9A%D1%80%D0%B8%D0%BF%D1%82%D0%BE%D0%B2%D0%B0%D0%BB%D1%8E%D1%82%D1%8B/thorchain'
        c_gecko_link = link(c_gecko_url, 'RUNE')

        message = f"{title} | {c_gecko_link}\n"
        price = p.fair_price.real_rune_price

        pr_text = pretty_dollar(price)
        message += f"Цена RUNE сейчас {code(pr_text)}\n"

        time_combos = zip(
            ('1ч.', '24ч.', '7дн.'),
            (p.price_1h, p.price_24h, p.price_7d)
        )
        for title, old_price in time_combos:
            if old_price:
                pc = calc_percent_change(old_price, price)
                message += pre(f"{title.rjust(5)}:{adaptive_round_to_str(pc, True).rjust(8)} % "
                               f"{emoji_for_percent_change(pc).ljust(4).rjust(6)}") + "\n"

        fp = p.fair_price
        if fp.rank >= 1:
            message += f"Капитализация: {bold(pretty_dollar(fp.market_cap))} (#{bold(fp.rank)} место)\n"

        if fp.tlv_usd >= 1:
            message += (f"TLV (кроме RUNE): ${pre(pretty_money(fp.tlv_usd))}\n"
                        f"Детерминистическая цена руны: ${code(pretty_money(fp.fair_price))}\n"
                        f"Спекулятивый множитель: {pre(x_ses(fp.fair_price, price))}\n")

        return message.rstrip()
