class JWTException(Exception):
    """JWT 관련 기본 예외 클래스"""
    def __init__(self, message: str):
        self.message = message
        super().__init__(self.message)

class TokenExpiredException(JWTException):
    """토큰이 만료된 경우 발생하는 예외"""
    def __init__(self):
        super().__init__("Token has expired")

class InvalidTokenException(JWTException):
    """토큰이 유효하지 않은 경우 발생하는 예외"""
    def __init__(self):
        super().__init__("Invalid token")

class TokenDecodingException(JWTException):
    """토큰 디코딩 중 오류가 발생한 경우의 예외"""
    def __init__(self):
        super().__init__("Could not decode token")

