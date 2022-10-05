from typing import NamedTuple, Optional

from services.lib.utils import load_json
from services.lib.w3.token_list import CONTRACT_DATA_BASE_PATH
from services.lib.w3.web3_helper import Web3Helper


class SwapInArgs(NamedTuple):
    fn_name: str
    tc_router: str
    tc_vault: str
    tc_memo: str
    from_token: str
    amount: int
    amount_out_min: int
    deadline: int


class AggregatorContract:
    DEFAULT_ABI_AGGREGATOR = f'{CONTRACT_DATA_BASE_PATH}/aggregator.abi.json'

    def __init__(self, helper: Web3Helper):
        self.helper = Web3Helper
        self.contract = helper.w3.eth.contract(abi=load_json(self.DEFAULT_ABI_AGGREGATOR))

    def decode_input(self, input_str) -> Optional[SwapInArgs]:
        func, args_dic = self.contract.decode_function_input(input_str)
        args = None
        if func.fn_name == 'swapIn':
            args = SwapInArgs(
                fn_name=func.fn_name,
                tc_router=args_dic.get('tcRouter'),
                tc_vault=args_dic.get('tcVault'),
                tc_memo=args_dic.get('tcMemo'),
                from_token=args_dic.get('token'),
                amount=args_dic.get('amount'),
                amount_out_min=args_dic.get('amountOutMin'),
                deadline=args_dic.get('deadline'),
            )
        return args
