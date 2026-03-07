"""Admin routes for Ultima-specific pages."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models import User
from app.services.ultima_agreement_service import (
    get_ultima_agreement,
    set_ultima_agreement,
)

from ..dependencies import get_cabinet_db, require_permission


router = APIRouter(prefix='/admin/ultima-pages', tags=['Admin Ultima Pages'])


class UltimaAgreementResponse(BaseModel):
    requested_language: str
    language: str
    content: str
    updated_at: str | None = None


class UltimaAgreementUpdateRequest(BaseModel):
    language: str = Field(default='ru', min_length=2, max_length=10)
    content: str = Field(default='', max_length=20000)


@router.get('/agreement', response_model=UltimaAgreementResponse)
async def get_ultima_agreement_page(
    language: str = Query(default='ru', min_length=2, max_length=10),
    admin: User = Depends(require_permission('settings:read')),
    db: AsyncSession = Depends(get_cabinet_db),
) -> UltimaAgreementResponse:
    _ = admin
    agreement = await get_ultima_agreement(db, language)
    return UltimaAgreementResponse(
        requested_language=agreement.requested_language,
        language=agreement.language,
        content=agreement.content,
        updated_at=agreement.updated_at,
    )


@router.put('/agreement', response_model=UltimaAgreementResponse)
async def update_ultima_agreement_page(
    payload: UltimaAgreementUpdateRequest,
    admin: User = Depends(require_permission('settings:edit')),
    db: AsyncSession = Depends(get_cabinet_db),
) -> UltimaAgreementResponse:
    _ = admin
    agreement = await set_ultima_agreement(db, payload.language, payload.content)
    await db.commit()
    return UltimaAgreementResponse(
        requested_language=agreement.requested_language,
        language=agreement.language,
        content=agreement.content,
        updated_at=agreement.updated_at,
    )
