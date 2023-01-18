class NotPermissionsError(Exception):
    pass


class NoPostError(Exception):
    pass


class NoUserError(Exception):
    pass


class UserAttrsAlreadyExist(Exception):
    pass


class ActionDuplicateError(Exception):
    pass


class VerifierTimeoutError(Exception):
    pass


class VerifierUnavailable(Exception):
    pass


class UnVerifiedEmailError(Exception):
    pass
