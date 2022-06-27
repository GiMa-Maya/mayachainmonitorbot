from typing import List

from proto import NativeThorTx, parse_thor_address, DecodedEvent, thor_decode_amount_field
from proto.thor_types import MsgSend
from services.lib.constants import thor_to_float
from services.lib.delegates import WithDelegates, INotified
from services.models.transfer import RuneTransfer


class RuneTransferDetectorNativeTX(WithDelegates, INotified):
    def __init__(self, address_prefix='thor'):
        super().__init__()
        self.address_prefix = address_prefix

    def address_parse(self, raw_address):
        return parse_thor_address(raw_address, self.address_prefix)

    async def on_data(self, sender, txs: List[NativeThorTx]):
        transfers = []
        for tx in txs:
            for message in tx.tx.body.messages:
                if isinstance(message, MsgSend):
                    from_addr = self.address_parse(message.from_address)
                    to_addr = self.address_parse(message.to_address)
                    for coin in message.amount:
                        transfers.append(RuneTransfer(
                            from_addr=from_addr,
                            to_addr=to_addr,
                            block=0,  # fixme
                            tx_hash=tx.hash,
                            amount=thor_to_float(coin.amount),
                            usd_per_rune=1.0,  # where to get it?
                            is_native=True,
                            asset=coin.denom
                        ))
        await self.pass_data_to_listeners(transfers)


class RuneTransferDetectorBlockEvents(WithDelegates, INotified):
    async def on_data(self, sender, events: List[DecodedEvent]):
        transfers = []
        for event in events:
            if event.type == 'transfer':
                amount, asset = event.attributes['amount']
                transfers.append(RuneTransfer(
                    event.attributes['sender'],
                    event.attributes['recipient'],
                    block=0,
                    tx_hash='',
                    amount=thor_to_float(amount),
                    usd_per_rune=1.0,
                    is_native=True,
                    asset=asset
                ))
        await self.pass_data_to_listeners(transfers)


class RuneTransferDetectorFromTxResult(WithDelegates, INotified):
    async def on_data(self, sender, data: List[tuple]):
        transfers = []
        for tx_result, events, height in data:
            senders = events.get('transfer.sender')
            recipients = events.get('transfer.recipient')
            amounts = events.get('transfer.amount')

            if not all((senders, recipients, amounts)):
                continue

            tx_hash = events['tx.hash'][0]
            for sender, recipient, amount_obj in zip(senders, recipients, amounts):
                amount, asset = thor_decode_amount_field(amount_obj)

                # ignore fee transfers
                if is_fee_tx(amount, asset, recipient, self.reserve_address):
                    continue

                transfers.append(RuneTransfer(
                    sender, recipient,
                    height, tx_hash,
                    thor_to_float(amount),
                    asset=asset,
                    is_native=True
                ))

        await self.pass_data_to_listeners(transfers)

    def __init__(self, reserve_address=''):
        super().__init__()
        self.reserve_address = reserve_address


def is_fee_tx(amount, asset, to_addr, reserve_address):
    return amount == 2000000 and asset == 'rune' and to_addr == reserve_address
