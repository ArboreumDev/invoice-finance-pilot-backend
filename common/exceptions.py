class SwarmAiException(Exception):
    """ Base class for all exceptions that are thrown here """

    def __init__(self, msg="Input is ill-formatted. See output above"):
        self.msg = msg
        # maybe in the future we want to store more general information here, e.g. on the pilot?
        super().__init__(self.msg)


class InsufficientFundException(SwarmAiException):
    def __init__(self, user_id: str, has: float, spends: float, purpose: str = ""):
        super().__init__(f"user {user_id} wants to spend {spends} on {purpose} but only has {has} in their account.")


class InsufficientFundsInCorpusException(SwarmAiException):
    pass


class OverRepaymentCorpusException(SwarmAiException):
    pass


class UnknownLoanException(SwarmAiException):
    def __init__(self, loan_id: str):
        super().__init__(f"Unknown loan / request id: {loan_id}")


class InternalError(SwarmAiException):
    pass


class InvalidLoanParams(SwarmAiException):
    pass


class InvalidParameterException(SwarmAiException):
    pass


class DuplicateLoanIdException(SwarmAiException):
    pass
