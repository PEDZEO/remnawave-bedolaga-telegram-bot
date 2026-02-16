# Account Linking Implementation Plan

## Goal

Provide a single user account (`users.id`) with shared subscription access across Telegram, Yandex, and VK logins.

## Principles

- One source of truth for subscription: only `subscriptions.user_id`.
- Login providers are authentication methods, not separate subscriptions.
- No implicit account merge by email.
- Any merge/linking must be explicit, auditable, and rate-limited.

## Phase 1 (Current)

Implement secure linking by one-time code without risky full data merges.

### Backend changes

1. Add link-code service in cabinet domain:
   - Generate short one-time code with TTL.
   - Store only code hash in Redis payload key.
   - Add brute-force protection (attempt limit).
   - Enforce single active code per source account.
2. Add account-linking API routes:
   - `POST /cabinet/auth/link-code/create`
   - `POST /cabinet/auth/link-code/preview`
   - `POST /cabinet/auth/link-code/confirm`
   - `GET /cabinet/auth/identities`
3. Add safe auto-link operation:
   - Transfer login identifiers from target to source account.
   - Allow only if target account is "clean" (no subscription, no balance, no transactions, no remnawave UUID).
   - On success deactivate target account login identifiers.
4. Disable OAuth auto-link by email in callback flow.

### Security controls

- One-time code, limited TTL.
- Maximum attempts per code/target pair.
- Explicit conflict checks for all provider identifiers.
- Reject merge for non-clean target accounts (manual support flow).
- Structured logs for create/preview/confirm/error events.

## Phase 2

Add explicit persistent identity model:

- New table `auth_identities(user_id, provider, provider_user_id, ...)`.
- Migrate existing provider columns to identity rows.
- Keep old columns for backward compatibility until full cutover.

## Phase 3

Support full account merge transactions for non-clean accounts:

- Controlled migration of balance/subscription/history with strict conflict policy.
- Audit table for merge operations.
- Admin tooling for manual conflict resolution.

## Validation checklist

1. OAuth login still works for Yandex/VK.
2. Link code can merge Telegram + OAuth identities for clean secondary account.
3. After linking, login via any linked provider resolves to same account/subscription.
4. Invalid/expired/reused code cases return clear 4xx responses.
5. Brute-force attempt limit works.
