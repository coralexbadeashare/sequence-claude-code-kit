---
name: sequence-design-rule
description: Design a Sequence money rule together with the user (e.g. split each paycheck, monthly sweep, keep a pod topped up), create the needed pods and the rule, dry-run it, and guide activation. Use when the user wants to automate moving money in Sequence.
---

# Design a Sequence rule with the user

The user owns the decisions. You translate their intent into a rule, show exactly what it would do, and
only create things after they agree. Reference: `docs/rules-cookbook.md`, `docs/sequence-api.md`.

## 1. Understand the goal

Ask (briefly, only what's missing):
- **When** should money move? On arrival into an account (`ON_FUNDS_TRANSFERRED`), on a schedule
  (`SCHEDULED`: DAILY / WEEKLY / BI_WEEKLY = 1st & 15th / MONTHLY / EVERY_OTHER_WEEK / ONE_TIME),
  or only when asked (`MANUAL`).
- **From where to where?** Existing accounts (`listAccounts`) or new pods.
- **How much?** Fixed amount, % of the incoming amount, % of the source balance, top up to a target,
  or round the source down to a floor.
- Any **conditions** (e.g. only if balance > $X) or **caps**.

## 2. Propose — before creating anything

Show:
1. A table: step → action → source → destination → amount/percentage.
2. A worked example in dollars (e.g. "a $3,000 paycheck → $150 Invest, $600 Tax, $2,250 Spending").
3. The exact `createRule` JSON you'll send.
List every assumption explicitly. Percentages on the same incoming amount should add up to ≤ 100.
Wait for the user's OK or edits.

## 3. Create

1. Missing accounts → `createAccount` (`POD` for buckets, `INCOME_SOURCE` for where outside money lands;
   names: letters, digits, spaces, hyphens; unique per type).
2. `createRule` with the agreed JSON. It's created **DISABLED**.
   If the tool replies with a dashboard link instead (guided setup over OAuth), build it in the
   dashboard's Rule Management with the user — via Chrome if available — using the same table.
3. `getRule` to confirm what Sequence stored; show it back in the table format.

## 4. Dry-run

`triggerRule` `{ "simulation": true, ... }` with realistic numbers:
- arrival rules: `simulatedIncomingFunds` (cents)
- balance rules: `simulatedSourceBalance` (cents)

Poll `getRuleExecution` (retry briefly on 404) → `getTransfer` per id in `transferIds`.
Present a table of the resulting transfers and compare with the worked example. If it differs,
explain why (rounding, $1 minimum, conditions not met, caps) and offer to adjust (`updateRule`).
Run 2–3 scenarios if useful (small paycheck, large paycheck, empty balance).

## 5. Activate (user)

Rules can only be switched on by a human. Point the user to https://app.getsequence.io → Rule Management
(open it in Chrome if available) and let **them** flip the toggle. Live runs over OAuth still need
in-app approval for each money movement.

## 6. Wrap up

Summarize: accounts created, rule id + name, trigger, what one run moves, and where to see/approve it.
Optionally append the rule to `my-rules.md` (gitignored) so future sessions know the setup.
