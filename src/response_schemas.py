"""Esquemas Pydantic para as respostas da API com mensagens técnicas não
relacionadas aos requisitos de negócio."""

from abc import ABC
from typing import Optional

from fastapi import status
from pydantic import BaseModel

# Classes de respostas de dados da API para mensagens técnicas


class ResponseData(ABC, BaseModel):
    """Classe abstrata para conter os métodos comuns a todos os modelos
    de dados de resposta da API."""

    _title = ""

    @classmethod
    def get_title(cls):
        """Retorna o título da resposta."""
        return cls._title.default

    @classmethod
    def docs(cls, examples: Optional[dict] = None) -> dict:
        """Retorna a documentação da resposta para o método, exibida pelo
        FastAPI na interface OpenAPI."""
        docs = {
            "model": cls,
            "description": cls.get_title(),
            "content": {"application/json": {}},
        }
        if examples is not None:
            docs["content"]["application/json"]["examples"] = examples
        return docs


class OKMessageResponse(ResponseData):
    """Resposta da API para mensagens bem sucedidas."""

    _status_code = status.HTTP_200_OK
    _title = "OK"
    message: str


class BadRequestErrorResponse(ResponseData):
    """Resposta da API para erros de autorização."""

    _status_code = status.HTTP_400_BAD_REQUEST
    _title = "Bad request"
    detail: str


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


class NotFoundErrorResponse(ResponseData):
    """Resposta da API para erros de permissão."""

    _status_code = status.HTTP_404_NOT_FOUND
    _title = "Not found"
    detail: str


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


# Funções auxiliares para documentação de possíveis respostas técnicas
# na API.

# Documentação de respostas comuns a diversos endpoints
not_logged_error = {
    401: UnauthorizedErrorResponse.docs(
        examples={"Invalid credentials": {"value": {"detail": "Not authenticated"}}}
    ),
}
not_admin_error = {
    **not_logged_error,
    403: ForbiddenErrorResponse.docs(
        examples={
            "Forbidden": {
                "value": {"detail": "Usuário não tem permissões de administrador"}
            }
        }
    ),
}
outra_unidade_error = {
    **not_logged_error,
    403: ForbiddenErrorResponse.docs(
        examples={
            "Forbidden": {
                "value": {
                    "detail": "Usuário não tem permissão na cod_unidade_autorizadora informada"
                }
            }
        }
    ),
}
email_validation_error = {
    422: ValidationErrorResponse.docs(
        examples={
            "Invalid email format": {
                "value": ValidationErrorResponse(
                    detail=[
                        ValidationError(
                            type="value_error",
                            loc=["email"],
                            msg="value is not a valid email address: "
                            "An email address must have an @-sign.",
                            input="my_username",
                            ctx={"reason": "An email address must have an @-sign."},
                            url="https://errors.pydantic.dev/2.8/v/value_error",
                        )
                    ]
                ).json()
            }
        }
    )
}
value_response_example = lambda message: {"example": {"value": {"detail": message}}}
