"""Admin routes for xray-balancer middleware control."""

from typing import Any

import httpx
import structlog
from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.config import settings
from app.database.models import User

from ..dependencies import get_current_admin_user


logger = structlog.get_logger(__name__)

router = APIRouter(prefix='/admin/balancer', tags=['Cabinet Admin Balancer'])


def _get_balancer_base_url() -> str:
    base_url = (settings.BALANCER_API_URL or '').strip().rstrip('/')
    if not base_url:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail='Balancer API is not configured',
        )
    return base_url


def _get_balancer_admin_token() -> str:
    token = (settings.BALANCER_ADMIN_TOKEN or '').strip()
    if not token:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail='Balancer admin token is not configured',
        )
    return token


async def _proxy_balancer_json(
    method: str,
    path: str,
    *,
    requires_admin: bool = False,
    params: dict[str, Any] | None = None,
) -> Any:
    base_url = _get_balancer_base_url()
    headers: dict[str, str] = {'Accept': 'application/json'}

    if requires_admin:
        headers['x-admin-token'] = _get_balancer_admin_token()

    timeout = max(1, int(settings.BALANCER_REQUEST_TIMEOUT))
    target_url = f'{base_url}{path}'

    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.request(method=method, url=target_url, headers=headers, params=params)
    except httpx.TimeoutException as exc:
        logger.warning('Balancer request timed out', path=path, method=method)
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail='Balancer request timed out',
        ) from exc
    except httpx.RequestError as exc:
        logger.warning('Balancer request failed', path=path, method=method, error=str(exc))
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail='Balancer is unreachable',
        ) from exc

    try:
        payload = response.json()
    except ValueError:
        payload = {'raw': response.text}

    if response.status_code >= 400:
        detail: Any = payload if isinstance(payload, dict | list) else {'detail': str(payload)}
        raise HTTPException(status_code=response.status_code, detail=detail)

    return payload


@router.get('/status')
async def get_balancer_status(
    admin: User = Depends(get_current_admin_user),
) -> dict[str, Any]:
    """Return local balancer integration status."""
    return {
        'configured': bool((settings.BALANCER_API_URL or '').strip()),
        'base_url': (settings.BALANCER_API_URL or '').strip() or None,
        'has_admin_token': bool((settings.BALANCER_ADMIN_TOKEN or '').strip()),
        'request_timeout_sec': int(settings.BALANCER_REQUEST_TIMEOUT),
    }


@router.get('/health')
async def get_balancer_health(
    admin: User = Depends(get_current_admin_user),
) -> Any:
    """Proxy balancer /health."""
    return await _proxy_balancer_json('GET', '/health')


@router.get('/ready')
async def get_balancer_ready(
    admin: User = Depends(get_current_admin_user),
) -> Any:
    """Proxy balancer /ready."""
    return await _proxy_balancer_json('GET', '/ready')


@router.get('/debug/stats')
async def get_balancer_debug_stats(
    admin: User = Depends(get_current_admin_user),
) -> Any:
    """Proxy balancer /debug/stats (admin token required)."""
    return await _proxy_balancer_json('GET', '/debug/stats', requires_admin=True)


@router.get('/node-stats')
async def get_balancer_node_stats(
    admin: User = Depends(get_current_admin_user),
) -> Any:
    """Proxy balancer /node-stats (admin token required)."""
    return await _proxy_balancer_json('GET', '/node-stats', requires_admin=True)


@router.get('/debug/token')
async def get_balancer_token_debug(
    token: str = Query(min_length=3, max_length=256),
    admin: User = Depends(get_current_admin_user),
) -> Any:
    """Proxy balancer /debug/token/{token} (admin token required)."""
    safe_token = token.strip().lstrip('/')
    if not safe_token:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='Token is required')
    return await _proxy_balancer_json('GET', f'/debug/token/{safe_token}', requires_admin=True)


@router.post('/refresh-groups')
async def refresh_balancer_groups(
    admin: User = Depends(get_current_admin_user),
) -> Any:
    """Proxy balancer /refresh-groups (admin token required)."""
    return await _proxy_balancer_json('GET', '/refresh-groups', requires_admin=True)


@router.post('/refresh-stats')
async def refresh_balancer_stats(
    admin: User = Depends(get_current_admin_user),
) -> Any:
    """Proxy balancer /refresh-stats (admin token required)."""
    return await _proxy_balancer_json('GET', '/refresh-stats', requires_admin=True)
