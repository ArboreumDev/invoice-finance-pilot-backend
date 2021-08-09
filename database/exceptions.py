class BaseException(Exception):
    """ Base class for all exceptions that are thrown here """

    def __init__(self, msg="Input is ill-formatted. See output above"):
        self.msg = msg
        super().__init__(self.msg)


class WhitelistException(BaseException):
    pass

class UnknownPurchaserException(BaseException):
    pass


class CreditLimitException(BaseException):
    pass

class DuplicateInvoiceException(BaseException):
    pass


class UnknownInvoiceException(BaseException):
    pass


class DuplicateWhitelistEntryException(BaseException):
    pass


