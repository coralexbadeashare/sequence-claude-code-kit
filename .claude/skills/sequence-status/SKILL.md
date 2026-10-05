---
name: sequence-status
description: Summarize the user's Sequence setup — accounts and balances, rules (enabled or not), recent transfers, pending approvals — and optionally write a short monthly report. Use when the user asks "how are my accounts", "what moved", "monthly report", or at the start of a session.
---

# Sequence status / report

All read-only; no approvals needed.

1. `listAccounts` → for pods/income sources, `getAccount` for balances. Note
   `balance.balanceLastUpdatedAt` (balances refresh ~once per banking day).
2. `listRules` → name, trigger, enabled/disabled. Flag rules that are still disabled.
3. `listTransfers` (or `listAccountTransfers` per account) for the period the user asks about
   (default: last 30 days). Group by rule (`ruleId`). Flag `APPROVAL_PENDING` items with their
   approval link, and any `INCOMPLETE` / `ERROR` with the `errorCode`.
4. Present:
   - Accounts table: name · type · balance · last updated
   - Rules table: name · trigger · status · last execution
   - Money moved this period, per destination
   - Things needing the user: pending approvals, disabled rules, failed transfers
5. **Monthly report** (if asked): add a few plain observations (e.g. "Tax pod received 20% of $6,000
   income = $1,200") and at most one or two suggestions (e.g. change a percentage). Suggestions only —
   the user decides; any change goes through `/sequence-design-rule`.

Pagination: `pageSize` up to 100; follow `hasNextPage`. Don't poll faster than the cadence in CLAUDE.md.
