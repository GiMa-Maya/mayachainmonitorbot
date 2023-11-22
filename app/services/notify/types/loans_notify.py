from typing import Optional, Union, List

from services.jobs.scanner.event_db import EventDatabase
from services.lib.constants import MAYA_PREFIX
from services.lib.delegates import INotified, WithDelegates
from services.lib.depcont import DepContainer
from services.lib.money import DepthCurve
from services.lib.utils import WithLogger, hash_of_string_repr
from services.models.loans import AlertLoanRepayment, AlertLoanOpen


class LoanTxNotifier(INotified, WithDelegates, WithLogger):
    def __init__(self, deps: DepContainer, prefix=MAYA_PREFIX, curve: Optional[DepthCurve] = None):
        super().__init__()
        self.deps = deps
        self.prefix = prefix

        self._ev_db = EventDatabase(deps.db)
        self.min_volume_usd = self.deps.cfg.as_float('tx.loans.min_usd_total', 2500.0)

        # todo: use this curve to evaluate min threshold across all pools involved
        self.curve_mult = self.deps.cfg.as_float('tx.loans.curve_mult', 1.0)
        self.curve = curve

    async def on_data(self, sender, events: List[Union[AlertLoanOpen, AlertLoanRepayment]]):
        for loan_ev in events:
            if loan_ev.collateral_usd > self.min_volume_usd:
                virt_tx_id = hash_of_string_repr(loan_ev)
                if not await self._ev_db.is_announced_as_started(virt_tx_id):
                    await self._ev_db.announce_tx_started(virt_tx_id)
                    await self.pass_data_to_listeners(loan_ev)

