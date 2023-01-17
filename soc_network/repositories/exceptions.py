class DbError(Exception):
    pass


class DbUnavailable(Exception):
    def __init__(self, code: int, message: str):
        self.code = code
        self.message = message
