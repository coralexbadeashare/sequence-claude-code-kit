# Sequence API — condensed reference

Summarized from the official OpenAPI spec (`https://api.getsequence.io/platform/v1/openapi`, checked 2026-10-04).
Run `scripts/fetch-openapi.sh` for the full, current spec. When this file and the spec disagree, the spec wins.

## Connecting

| | MCP over OAuth (default in this repo) | API key |
|---|---|---|
| Setup | `.mcp.json` → `/mcp` → Authenticate → sign in | Dashboard → Settings → API Keys → `Authorization: Bearer <key>` |
| Permissions | Built in from your role. Owner/co-owner: full read, create accounts & rules (rules land inactive), money movement **always needs in-app approval** | Per key: scoped to accounts/rules, optional `max_amount`, approval on by default (can be turned off) |
| Used for | Everything Claude does in chat | Scripts/automations (e.g. `examples/five-percent-sp500`) |

- MCP server: `https://app.getsequence.io/api/mcp` (Streamable HTTP). REST base: `https://api.getsequence.io/platform/v1`.
- One key per agent/automation; name like `<tool>-<purpose>`. Never commit keys.
- `tools/list` is filtered to what the caller may do.

## MCP tools

**Accounts:** `listAccounts`, `getAccount`, `createAccount`, `listBeneficiaries`, `listAccountTransfers`
**Rules:** `listRules`, `getRule`, `createRule`, `updateRule`, `triggerRule`, `listRuleExecutions`, `getRuleExecution`
**Transfers & transactions:** `createTransfer`, `listTransfers`, `getTransfer`, `listExternalTransactions`, `listTransactions`, `listAuditLog`
**Guided setup (point to the dashboard):** `createRule` (when not permitted directly), `connectExternalAccount`, `issueCard`, `addUser`, `addBusinessBeneficiary`, `contactSupport`

## Accounts

- Types: `INCOME_SOURCE` (where outside money lands; rules distribute it), `POD` (bucket/goal, optional `savingsTargetInCents`), `EXTERNAL_ACCOUNT` (linked bank/card/loan via Plaid/Finicity, not managed by Sequence).
- `createAccount`: `{ "type": "POD" | "INCOME_SOURCE", "name": "Tax Reserve", "icon": "💰"?, "beneficiaryId"?, "savingsTargetInCents"? }`.
  Name: letters, digits, spaces, hyphens; unique per type. Both types are real bank accounts.
- Requires completed identity verification, otherwise `403 KYC_REQUIRED`.

## Rules

A rule = **trigger** + ordered **steps**. Each step has optional **conditions** and one or more **actions**.
Steps are first-match-wins; a step with `conditions: null` is a catch-all. New rules are **DISABLED**;
a human enables them in the dashboard. A disabled rule can still be dry-run.

**Triggers**
- `{ "type": "ON_FUNDS_TRANSFERRED", "accountId": "<id>" }` — when money arrives in that account.
- `{ "type": "SCHEDULED", "scheduleType": "MONTHLY", "startDate": "2026-11-01T14:00:00Z", "accountId": "<source id>" }`
  — `ONE_TIME | DAILY | WEEKLY | BI_WEEKLY (1st & 15th) | MONTHLY | EVERY_OTHER_WEEK`, times in UTC.
- `{ "type": "MANUAL", "accountId": "<id>" }` — only when triggered via the API.

**Actions** (all need `source`, `destination` as `{ "id", "type" }`, and `groupIndex`)
- `FIXED` — `amountInCents`.
- `PERCENTAGE` — `percentageValue` 0–100 + `percentageTarget`: `INCOMING_AMOUNT` (% of the triggering deposit) or `SOURCE_ACCOUNT` (% of source balance at run time).
- `TOP_UP` — bring destination up to a target: exactly one of `amountInCents`, `currentBalanceAccount`, `nextPaymentMinimumAccount`, `lastStatementBalanceAccount` non-null.
- `ROUND_DOWN` — move everything above `amountInCents` out of the source.
- Liability payments: `NEXT_PAYMENT_MINIMUM`, `TOTAL_AMOUNT_DUE`, `LAST_STATEMENT_BALANCE`, `PERCENTAGE_LIABILITY_BALANCE`.
- Optional: `upToEnabled` (partial transfer if short), `limit` (cap; shared across actions with the same `groupIndex`), `achDescription`, `isDirectDeposit`.

`updateRule` replaces `trigger` / `steps` atomically when provided. `422 INVALID_RULE` = shape not representable in this API version.

## Running rules and transfers

- `triggerRule` → `202` + `executionId` (async). Body: `executeAmount`, `simulation`, `simulatedSourceBalance`, `simulatedIncomingFunds`, `reasonForApproval`.
  Dry-run base = `(simulatedSourceBalance ?? executeAmount ?? realBalance) + (simulatedIncomingFunds ?? 0)`.
- `getRuleExecution` → status, `stepIndexMatched` / `conditionsNotMet`, `transfersAttempted`, `transferIds` (no amounts) → `getTransfer` per id.
- `createTransfer` → `{ sourceAccountId, destinationAccountId, amountInCents, description?, simulation?, simulatedSourceBalance?, reasonForApproval? }`.
  `description` is the ACH label: ≤ 10 chars, letters/digits/spaces.
- Dry runs (`simulation: true`) are never approval-gated; results have `executionMode: SIMULATION`; list endpoints hide them unless `executionMode=SIMULATION|ALL`.
- Live calls with approval → `status: APPROVAL_PENDING` + `approvalUrl`. Outcome: proceeds, or `APPROVAL_DENIED` (denied or 24h timeout).

**Transfer statuses:** `APPROVAL_PENDING → PROCESSING → PENDING → COMPLETE`, or `INCOMPLETE` (insufficient funds), `ERROR`, `CANCELLED`, `APPROVAL_DENIED`.
**Transfer fields:** `id, amountInCents, direction (MONEY_IN|MONEY_OUT|INTERNAL), origin, source, destination, status, executionMode, ruleId, ruleExecutionId, errorCode, createdAt, completedAt`.

## Conventions

- Amounts: integer cents. Minimum transfer $1.00. IDs: UUIDs. Times: ISO 8601 UTC.
- Responses: `{ "data": ..., "requestId": ... }`. Errors: `{ "error": { "code", "message" } }`.
- `idempotency-key` header (UUID v4) on writes; remembered 24h; same key + different body → `400 IDEMPOTENCY_KEY_MISMATCH`; in-flight → `409 *_IN_PROGRESS`.
- Fresh ids can 404 briefly (eventual consistency) — retry with backoff.
- Pagination: `page`, `pageSize` (≤ 100), `pagination.hasNextPage`.
- Rate limit 100 req/min per token (`429` + `Retry-After`). Balances refresh ~daily: poll ≤ every 6h; transfers ≤ hourly.

## Errors worth knowing

`KYC_REQUIRED` (finish verification in the app) · `ACCESS_DENIED` (permission/scope) · `MAXIMUM_AMOUNT_EXCEEDED` · `RULE_DEACTIVATED` (enable it in the dashboard) · `INVALID_RULE` · `*_NOT_FOUND` · `RATE_LIMIT_EXCEEDED` · `UNEXPECTED_ERROR` (report with `requestId`).

## Webhooks

Register in Settings → Webhooks. Events: `transfer.changed`, `card_transaction.changed`, `external_transaction.changed`.
Payloads carry ids only — fetch current state with the GET endpoints. Verify `X-Sequence-Signature: t=<unix>,v1=<hex>`
= HMAC-SHA256(secret, `"{t}.{rawBody}"`), reject if `t` is > 5 min off. At-least-once delivery; dedupe on `X-Sequence-Event-Id`.

## Testing without risk

No sandbox with fake money. Use, in combination: dry runs; real transfers at $1; a closed system (no external accounts reachable);
approval on everything.
