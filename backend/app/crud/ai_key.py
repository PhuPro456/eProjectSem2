from sqlalchemy import select, update
from sqlalchemy.orm import Session

from app.core.ai_providers import mask_key
from app.core.security import encrypt_secret
from app.models.ai_key import AIKey
from app.models.user import User
from app.schemas.ai_key import AIKeyCreate


def _admin_keys_query() -> select:
    return (
        select(AIKey)
        .join(User, User.id == AIKey.user_id)
        .where(User.role == "admin")
        .order_by(AIKey.is_active.desc(), AIKey.created_at.desc(), AIKey.id.desc())
    )


def list_admin_keys(db: Session) -> list[AIKey]:
    return list(db.scalars(_admin_keys_query()).all())


def get_admin_key(db: Session, key_id: int) -> AIKey | None:
    return db.scalar(_admin_keys_query().where(AIKey.id == key_id))


def get_active_admin_key(db: Session) -> AIKey | None:
    return db.scalar(_admin_keys_query().where(AIKey.is_active.is_(True)).limit(1))


def activate_key(db: Session, key: AIKey) -> AIKey:
    admin_ids = select(User.id).where(User.role == "admin")
    db.execute(
        update(AIKey)
        .where(AIKey.user_id.in_(admin_ids))
        .values(is_active=False)
    )
    key.is_active = True
    db.commit()
    db.refresh(key)
    return key


def create_key(
    db: Session, admin_id: int, data: AIKeyCreate, activate: bool = True
) -> AIKey:
    key = AIKey(
        user_id=admin_id,
        provider=data.provider,
        label=data.label,
        key_hint=mask_key(data.api_key),
        encrypted_key=encrypt_secret(data.api_key),
    )
    db.add(key)
    db.commit()
    db.refresh(key)
    return activate_key(db, key) if activate else key


def delete_key(db: Session, key: AIKey) -> None:
    db.delete(key)
    db.commit()
