class RoadmapCreatorMaxCountException(Exception):
    """로드맵 생성자 최대 개수 초과 예외"""
    def __init__(self, message: str):
        self.message = message
        super().__init__(self.message)
