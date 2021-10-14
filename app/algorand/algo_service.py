import requests
import json
from typing import List
from sqlalchemy.orm import Session
from database import crud
from database.exceptions import (
    AssetCreationException, AssetLogException, NoInvoicesToBeTokenized, InvoicesAlreadyTokenized, InvoicesNotFinancable, TokenizationException
)
from utils.common import AssetLogResponse, FinanceStatus, FundedInvoice, LogData, NewLoanParams, NewLogAssetInput, NewAssetResponse, NewLogEntryInput
from database.models import Invoice

from starlette.status import (HTTP_200_OK, HTTP_400_BAD_REQUEST)
from utils.logger import get_logger

class AlgoService():
    def __init__(self, base_url: str, password: str):
        """ initialize client and get access token from RC-sandbox """
        self.base_url = base_url
        self.headers = {"Authorization": f"Bearer {password}"}
        # TODO add logging
        self._logger = get_logger(self.__class__.__name__)

    def get_invoices_to_be_tokenized(self, loan_id, db):
        """
        gets all invoices related to a given loan_id
        @returns list of invoices that should go into the metadata of the token
        throws if the loan is already tokenized
        throws if there are no invoices for a given loan id
        throws if the invoices are in any other state than "FINANCED"
        throws if there is an invoice that has no real world tx-ref"
        """
 
        # verify loan_id exists
        all_invoices: List[Invoice] = crud.invoice.get_all_invoices(db)
        invoices_from_loan = [i for i in all_invoices if json.loads(i.payment_details)['loan_id'] == loan_id]
        if not invoices_from_loan:
            raise NoInvoicesToBeTokenized()
        
        # verify no invoice is already tokenized
        invoices_already_tokenized = [i.order_ref for i in invoices_from_loan if "tokenization" in json.loads(i.payment_details).keys()]
        print(invoices_already_tokenized)
        if invoices_already_tokenized:
            raise InvoicesAlreadyTokenized(
                msg=f"Invoices already tokenized with order ref: {str(invoices_already_tokenized)}"
            )
        
        # verify all invoices in state FINANCED
        invoices_not_in_state_financed = [
            (i.order_ref, i.finance_status) for i in invoices_from_loan if i.finance_status != FinanceStatus.FINANCED
        ]
        if invoices_not_in_state_financed:
            raise InvoicesNotFinancable(
                msg=f"Invoices not in state to be tokenized: {str(invoices_not_in_state_financed)}"
            )

        # verify all invoices have a real-world tx-reference
        invoices_without_tx_ref = [
            i.order_ref for i in invoices_from_loan if not(bool(json.loads(i.payment_details).get('disbursal_transaction_id', 0)))
        ]
        if invoices_without_tx_ref:
            raise InvoicesNotFinancable(
                msg=f"Invoices are missing tx-reference: {str(invoices_without_tx_ref)}"
            )
        
        return invoices_from_loan

    def tokenize_loan(self, loan_id: str, db: Session):
        """
        - gets all invoices related to a given loan_id, 
        - summarizes the essential data that should be put onto the metadata of the token
        - creates the asset
        - writes the asset_id into the payment_details of each invoice
        @returns success: the new asset_id of the created NFT
        throws if there is an issue with the invoices (see self.get_invoices_to_be_tokenized)
        """
        invoices_to_be_tokenized = self.get_invoices_to_be_tokenized(loan_id, db)
        self._logger.info(f"Tokenizing {len(invoices_to_be_tokenized)} invoices for loan ID {loan_id}")
       
        # summarize financable invoices
        compact_invoice_info = [
            FundedInvoice(
                invoice_id=i.id,
                order_id=i.order_ref,
                value=i.value,
                transaction_ref=json.loads(i.payment_details).get("disbursal_transaction_id"),
                financed_on=str(i.financed_on),
            ) for i in invoices_to_be_tokenized]
        
        # TODO how to summarize the terms from multiple invoices into the terms of one loan?
        # - which start dates: for now: just choose one from one invoice
        sample_invoice: Invoice = invoices_to_be_tokenized[0]
        # how to identify the borrower: -> supplier name
        borrower = crud.supplier.get(db, supplier_id=sample_invoice.supplier_id)

        new_asset_input = NewLogAssetInput(
            asset_name=f"ArbLogAsset-{loan_id}",
            loan_params=NewLoanParams(
                loan_id=loan_id,
                borrower_info=borrower.name,
                principal=sum(i.value for i in compact_invoice_info),
                apr=sample_invoice.apr,
                tenor_in_days=sample_invoice.tenor_in_days,
                start_date=sample_invoice.financed_on.timestamp(),
                collection_frequency="daily",
                data=str([i.dict() for i in compact_invoice_info])
            )
        )
        self._logger.info(f"Summarized for asset metadata like this: {new_asset_input}")

        url = self.base_url + "/v1/log/new"
        response = requests.request("POST", url, json=new_asset_input.to_camelized_dict(), headers=self.headers)
        print('resp', response)
        if response.status_code != HTTP_200_OK:
            err_msg = str(response.json())
            self._logger.exception(f"request to Algorand-logger API failed with {err_msg}")
            raise TokenizationException(msg=err_msg)
        
        try:
            raw_response = response.json()
            self._logger.info(f"Tokenization success! Response: {raw_response}")
            # write asset_id into each invoice.payment_details
            data = NewAssetResponse(**raw_response)
            new_asset_info = {
                'asset_id': data.assetId,
                'transactions': {data.txId: "creation"}
            }
            for inv in invoices_to_be_tokenized:
                crud.invoice.update_invoice_payment_details(
                    invoice_id=inv.id, new_data={"tokenization": new_asset_info}, db=db
                )
            print('new asset data', new_asset_info)
            return data
        except Exception as e:
            err_msg = f"Error storing created asset {str(e)}"
            self._logger.exception(err_msg)
            raise AssetCreationException(err_msg)

        # if not data["flag"]:
        #     raise AttributeError(data["message"])  # TODO define exception
        # else:
        #     balances = response.json()["data"]
        #     return {inv: result_to_balance(val) for inv, val in balances.items()}

    def log_invoice_repayment(self, invoice_id: str, tx_ref: str, db: Session):
        """
        Creates a log-tx for on the invoice's loan-asset assuming full repayment
        """
        try:
            invoice = crud.invoice.get(db=db, id=invoice_id)
            payment_details = json.loads(invoice.payment_details)
            asset_id = payment_details.get('tokenization', {}).get('asset_id', False)
            if not asset_id:
                raise TokenizationException(f"Invoice not tokenized, no asset-id found.")
            url = self.base_url + f"/v1/log/{asset_id}"
            # log_data = NewLogEntryInput(
            log_data=LogData(
                data={
                'type': 'repay',
                'subtype': 'full',
                'amount': invoice.value,
                'tx_ref': tx_ref
            }).dict()
            # )
            response = requests.request("POST", url, json=log_data, headers=self.headers)
            raw_response = response.json()
            self._logger.info(f"Result:{raw_response}")
            if response.status_code != HTTP_200_OK:
                raise AssertionError(str(raw_response))

            # store reference to blockchain tx on invoice
            log_response = AssetLogResponse(**raw_response)
            new_tx_entry = { log_response.txId: { 'log_data': log_data, 'tx_info': log_response.data } }
            return new_tx_entry
 
        except Exception as e:
            # TODO more fine-grained handling here
            raise AssetLogException(str(e))

    


# TODO load from env
ALGO_LOG_BASE_URL='http://localhost:8001'
ALGO_LOG_API_SECRET="sWUCzK7ZaT5E8zgWY95wUL1e6cNpJli5DzcwAYXsRpw="

algo_service = AlgoService(
    base_url=ALGO_LOG_BASE_URL,
    password=ALGO_LOG_API_SECRET
)