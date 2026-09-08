from fastapi import APIRouter, Depends, HTTPException, Response, status
from fastapi.security import HTTPBearer

from app.auth.schemas import (
    LoginRequest,
    LoginResponse,
    ErrorResponse,
)
from app.auth.service import AuthService

router = APIRouter(prefix="/auth", tags=["auth"])


def get_auth_service() -> AuthService:
    return AuthService()


@router.post(
    "/login",
    response_model=LoginResponse,
    status_code=status.HTTP_200_OK,
    operation_id="login",
    responses={
        401: {"model": ErrorResponse, "description": "Invalid credentials"},
        422: {"model": ErrorResponse, "description": "Validation error"},
        429: {"model": ErrorResponse, "description": "Too many requests"},
    },
)
async def login(
    payload: LoginRequest,
    response: Response,
    service: AuthService = Depends(get_auth_service),
) -> LoginResponse:
    """Authenticate a user with email and password and return JWT tokens."""
    result = await service.login(payload=payload, response=response)
    return result
