from fastapi import HTTPException, status

class NotFoundException(HTTPException):
    def __init__(self, detail: str = "Resource not found"):
        super().__init__(status_code=status.HTTP_404_NOT_FOUND, detail=detail)

class ValidationException(HTTPException):
    def __init__(self, detail: str = "Validation failed"):
        super().__init__(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=detail)

class BusinessRuleViolationException(HTTPException):
    def __init__(self, detail: str = "Operation violates business rule"):
        super().__init__(status_code=status.HTTP_400_BAD_REQUEST, detail=detail)

class ModelInferenceException(HTTPException):
    def __init__(self, detail: str = "Machine learning inference error"):
        super().__init__(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=detail)
