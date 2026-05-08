class NotFoundError(Exception):
    """요청한 엔티티가 DB에 존재하지 않을 때"""
    def __init__(self, entity: str, id_value):
        super().__init__(f"{entity} (id={id_value}) 를 찾을 수 없습니다.")
        self.entity = entity
        self.id_value = id_value


class ValidationError(Exception):
    """입력값 유효성 검사 실패 시"""
    pass


class DatabaseError(Exception):
    """DB 조작 중 예기치 않은 오류 발생 시"""
    pass
