from typing import Any

from ..schemas.miniapp import (
    MiniAppSubscriptionPurchasePreviewRequest,
    MiniAppSubscriptionPurchaseRequest,
)


def merge_purchase_selection_from_request(
    payload: MiniAppSubscriptionPurchasePreviewRequest | MiniAppSubscriptionPurchaseRequest,
) -> dict[str, Any]:
    base: dict[str, Any] = {}
    if payload.selection:
        base.update(payload.selection)

    def _maybe_set(key: str, value: Any) -> None:
        if value is None:
            return
        if key not in base:
            base[key] = value

    _maybe_set('period_id', getattr(payload, 'period_id', None))
    _maybe_set('period_days', getattr(payload, 'period_days', None))

    _maybe_set('traffic_value', getattr(payload, 'traffic_value', None))
    _maybe_set('traffic', getattr(payload, 'traffic', None))
    _maybe_set('traffic_gb', getattr(payload, 'traffic_gb', None))

    servers = getattr(payload, 'servers', None)
    if servers is not None and 'servers' not in base:
        base['servers'] = servers
    countries = getattr(payload, 'countries', None)
    if countries is not None and 'countries' not in base:
        base['countries'] = countries
    server_uuids = getattr(payload, 'server_uuids', None)
    if server_uuids is not None and 'server_uuids' not in base:
        base['server_uuids'] = server_uuids

    _maybe_set('devices', getattr(payload, 'devices', None))
    _maybe_set('device_limit', getattr(payload, 'device_limit', None))

    return base
