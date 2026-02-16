"""OAuth 2.0 authentication routes for cabinet."""

from datetime import UTC, datetime

import structlog
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database.crud.user import (
    create_user_by_oauth,
    get_user_by_oauth_provider,
)
from app.database.models import User

from ..auth.oauth_providers import (
    OAuthUserInfo,
    build_vk_pkce_payload,
    consume_oauth_state,
    generate_oauth_state,
    get_provider,
)
from ..dependencies import get_cabinet_db
from ..schemas.auth import AuthResponse
from .auth import _create_auth_response, _store_refresh_token


logger = structlog.get_logger(__name__)

router = APIRouter(prefix='/auth/oauth', tags=['Cabinet OAuth'])


async def _finalize_oauth_login(db: AsyncSession, user: User, provider: str) -> AuthResponse:
    """Update last login, create tokens, store refresh token."""
    user.cabinet_last_login = datetime.now(UTC).replace(tzinfo=None)
    await db.commit()
    auth_response = _create_auth_response(user)
    await _store_refresh_token(db, user.id, auth_response.refresh_token, device_info=f'oauth:{provider}')
    return auth_response


def _fill_missing_profile_fields(user: User, user_info: OAuthUserInfo) -> bool:
    """Backfill missing profile fields from OAuth provider payload."""
    updated = False

    if not user.first_name and user_info.first_name:
        user.first_name = user_info.first_name
        updated = True
    if not user.last_name and user_info.last_name:
        user.last_name = user_info.last_name
        updated = True
    if not user.username and user_info.username:
        user.username = user_info.username
        updated = True
    if not user.email and user_info.email and user_info.email_verified:
        user.email = user_info.email
        user.email_verified = True
        user.email_verified_at = datetime.now(UTC).replace(tzinfo=None)
        updated = True

    if updated:
        user.updated_at = datetime.now(UTC).replace(tzinfo=None)
    return updated


# --- Schemas ---


class OAuthProviderInfo(BaseModel):
    name: str
    display_name: str


class OAuthProvidersResponse(BaseModel):
    providers: list[OAuthProviderInfo]


class OAuthAuthorizeResponse(BaseModel):
    authorize_url: str
    state: str


class OAuthCallbackRequest(BaseModel):
    code: str = Field(..., description='Authorization code from provider')
    state: str = Field(..., description='CSRF state token')
    device_id: str | None = Field(None, description='Device id returned by VK ID callback')
    type: str | None = Field(None, description='OAuth response type from provider callback')


# --- Endpoints ---


@router.get('/providers', response_model=OAuthProvidersResponse)
async def get_oauth_providers():
    """Get list of enabled OAuth providers."""
    providers_config = settings.get_oauth_providers_config()
    providers = [
        OAuthProviderInfo(name=name, display_name=cfg['display_name'])
        for name, cfg in providers_config.items()
        if cfg['enabled']
    ]
    return OAuthProvidersResponse(providers=providers)


@router.get('/{provider}/authorize', response_model=OAuthAuthorizeResponse)
async def get_oauth_authorize_url(provider: str):
    """Get authorization URL for an OAuth provider."""
    oauth_provider = get_provider(provider)
    if not oauth_provider:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f'OAuth provider "{provider}" is not enabled',
        )

    if provider == 'vk':
        vk_payload, code_challenge = build_vk_pkce_payload()
        state = await generate_oauth_state(provider, payload=vk_payload)
        authorize_url = oauth_provider.get_authorization_url(state, code_challenge=code_challenge)
    else:
        state = await generate_oauth_state(provider)
        authorize_url = oauth_provider.get_authorization_url(state)

    return OAuthAuthorizeResponse(authorize_url=authorize_url, state=state)


@router.post('/{provider}/callback', response_model=AuthResponse)
async def oauth_callback(
    provider: str,
    request: OAuthCallbackRequest,
    db: AsyncSession = Depends(get_cabinet_db),
):
    """Handle OAuth callback: exchange code, find/create user, return JWT."""
    # 1. Validate CSRF state
    state_payload = await consume_oauth_state(request.state, provider)
    if not state_payload:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail='Invalid or expired OAuth state',
        )

    # 2. Get provider instance
    oauth_provider = get_provider(provider)
    if not oauth_provider:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f'OAuth provider "{provider}" is not enabled',
        )

    # 3. Exchange code for tokens
    try:
        exchange_kwargs: dict[str, str] = {'state': request.state}
        if provider == 'vk':
            if request.type and request.type != 'code_v2':
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail='Unsupported VK OAuth response type',
                )
            if not request.device_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail='Missing VK device_id in callback',
                )
            code_verifier = state_payload.get('code_verifier')
            if not code_verifier:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail='Missing VK PKCE verifier',
                )
            exchange_kwargs.update(
                {
                    'device_id': request.device_id,
                    'code_verifier': code_verifier,
                },
            )

        token_data = await oauth_provider.exchange_code(request.code, **exchange_kwargs)
    except HTTPException:
        raise
    except Exception as exc:
        logger.error('OAuth code exchange failed for', provider=provider, exc=exc)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail='Failed to exchange authorization code',
        ) from exc

    # 4. Fetch user info from provider
    try:
        user_info: OAuthUserInfo = await oauth_provider.get_user_info(token_data)
    except Exception as exc:
        logger.error('OAuth user info fetch failed for', provider=provider, exc=exc)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail='Failed to fetch user information from provider',
        ) from exc

    # 5. Find user by provider ID
    user = await get_user_by_oauth_provider(db, provider, user_info.provider_id)
    if user:
        if _fill_missing_profile_fields(user, user_info):
            await db.commit()
        logger.info('OAuth login via for existing user', provider=provider, user_id=user.id)
        return await _finalize_oauth_login(db, user, provider)

    # 6. Create new user
    user = await create_user_by_oauth(
        db=db,
        provider=provider,
        provider_id=user_info.provider_id,
        email=user_info.email if user_info.email_verified else None,
        email_verified=user_info.email_verified,
        first_name=user_info.first_name,
        last_name=user_info.last_name,
        username=user_info.username,
    )
    logger.info('OAuth new user created via with id', provider=provider, user_id=user.id)
    return await _finalize_oauth_login(db, user, provider)
