from typing import List

from proto import NativeThorTx, parse_thor_address
from proto.thor_types import MsgSend
from services.lib.constants import thor_to_float
from services.lib.delegates import WithDelegates, INotified
from services.models.transfer import RuneTransfer


class RuneTransferDetector(WithDelegates, INotified):
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
