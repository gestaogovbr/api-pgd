"""Esquemas Pydantic para as respostas da API.
"""

from abc import ABC

from fastapi import status
from pydantic import BaseModel


class ResponseData(ABC, BaseModel):
    """Classe abstrata para conter os métodos comuns a todos os modelos
    de dados de resposta da API."""

    _title = ""

    @classmethod
    def get_title(cls):
        return cls._title.default


class ValidationError(BaseModel):
    """Estrutura retornada pelo Pydantic para cada erro de validação."""

    type: str
    loc: list[str]
    msg: str
    ctx: dict


class ValidationErrorResponse(ResponseData):
    """Resposta da API para erros de validação."""

    _status_code = status.HTTP_422_UNPROCESSABLE_ENTITY
    _title = "Unprocessable Entity"
    detail: list[ValidationError]


class UnauthorizedErrorResponse(ResponseData):
    """Resposta da API para erros de autorização."""

    _status_code = status.HTTP_401_UNAUTHORIZED
    _title = "Unauthorized access"
    detail: str


class ForbiddenErrorResponse(ResponseData):
    """Resposta da API para erros de permissão."""

    _status_code = status.HTTP_403_FORBIDDEN
    _title = "Forbidden"
    detail: str

RESPONSE_MODEL_FOR_STATUS_CODE = {
    status.HTTP_422_UNPROCESSABLE_ENTITY: ValidationErrorResponse,
    status.HTTP_401_UNAUTHORIZED: UnauthorizedErrorResponse,
    status.HTTP_403_FORBIDDEN: ForbiddenErrorResponse,
}
