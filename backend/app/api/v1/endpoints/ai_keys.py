from typing import Annotated

from cryptography.fernet import InvalidToken
from fastapi import APIRouter, Depends, HTTPException, status

from app.api.deps import DatabaseSession, get_current_admin
from app.crud import ai_key as key_crud
from app.core.security import decrypt_secret
from app.models.ai_key import AIKey
from app.models.user import User
from app.schemas.ai_key import AIKeyCreate, AIKeyRead, AIKeyVerifyResult
from app.services.ai_verify import verify_key_format

router = APIRouter(
    prefix="/admin/ai-keys",
    tags=["administration"],
    dependencies=[Depends(get_current_admin)],
)


def _get_key_or_404(db: DatabaseSession, key_id: int) -> AIKey:
    key = key_crud.get_admin_key(db, key_id)
    if key is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"AI key {key_id} not found",
        )
    return key


@router.get("", response_model=list[AIKeyRead])
def list_keys(db: DatabaseSession) -> list[AIKey]:
    return key_crud.list_admin_keys(db)


@router.post("", response_model=AIKeyRead, status_code=status.HTTP_201_CREATED)
def create_key(
    payload: AIKeyCreate,
    db: DatabaseSession,
    current_admin: Annotated[User, Depends(get_current_admin)],
) -> AIKey:
    valid, message = verify_key_format(payload.provider, payload.api_key)
    if not valid:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail=message
        )
    return key_crud.create_key(db, current_admin.id, payload)


@router.delete("/{key_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_key(key_id: int, db: DatabaseSession) -> None:
    key_crud.delete_key(db, _get_key_or_404(db, key_id))


@router.post("/{key_id}/activate", response_model=AIKeyRead)
def activate_key(key_id: int, db: DatabaseSession) -> AIKey:
    return key_crud.activate_key(db, _get_key_or_404(db, key_id))


@router.post("/{key_id}/verify", response_model=AIKeyVerifyResult)
def verify_key(key_id: int, db: DatabaseSession) -> AIKeyVerifyResult:
    key = _get_key_or_404(db, key_id)
    try:
        raw_key = decrypt_secret(key.encrypted_key)
    except InvalidToken:
        return AIKeyVerifyResult(
            key_id=key.id,
            provider=key.provider,
            status="invalid_format",
            message="This key can no longer be decrypted with the server key.",
        )

    valid, message = verify_key_format(key.provider, raw_key)
    return AIKeyVerifyResult(
        key_id=key.id,
        provider=key.provider,
        status="format_ok" if valid else "invalid_format",
        message=message,
    )
