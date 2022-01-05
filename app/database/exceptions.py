class BaseException(Exception):
    """ Base class for all exceptions that are thrown here """

    def __init__(self, msg="Input is ill-formatted. See output above"):
        self.msg = msg
        super().__init__(self.msg)


class WhitelistException(BaseException):
    pass

class SupplierException(BaseException):
    pass

class UnknownSupplierException(BaseException):
    pass

class UnknownPurchaserException(BaseException):
    pass


class CreditLimitException(BaseException):
    pass

class SupplierLimitException(CreditLimitException):
    pass

class PurchaserLimitException(CreditLimitException):
    pass

class RelationshipLimitException(BaseException):
    pass

class DuplicateInvoiceException(BaseException):
    pass


class UnknownInvoiceException(BaseException):
    pass


class DuplicateWhitelistEntryException(BaseException):
    pass

class InsufficientCreditException(BaseException):
    pass


class DuplicateSupplierEntryException(BaseException):
    pass


class DuplicatePurchaserEntryException(BaseException):
    pass

class NoInvoicesToBeTokenized(BaseException):
    pass

class InvoicesAlreadyTokenized(BaseException):
    pass


class InvoicesNotFinancable(BaseException):
    pass

class TokenizationException(BaseException):
    pass

class AssetLogException(BaseException):
    pass

class AssetCreationException(BaseException):
    pass







