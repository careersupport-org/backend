class UnauthorizedException(Exception):
    """
    사용자 정보를 조회할 수 없을 때 발생하는 예외
    """

    def __init__(self, message: str):
        self.message = message
        super().__init__(self.message)

class EntityNotFoundException(Exception):
    """
    데이터베이스에서 엔티티를 찾을 수 없을 때 발생하는 예외
    """
    def __init__(self, message: str):
        self.message = message
        super().__init__(self.message)


class ForbiddenException(Exception):
    """
    권한이 없을 때 발생하는 예외
    """
    def __init__(self, message: str):
        self.message = message
        super().__init__(self.message)

class ModelInvocationException(Exception):
    """
    LLM 호출 중 발생하는 예외
    """
    def __init__(self, message: str, exception: Exception):
        self.message = message
        self.exception = exception
        super().__init__(self.message)
