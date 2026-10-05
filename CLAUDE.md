# Sequence money-automation kit — instructions for Claude

This repo turns Claude Code into an assistant for **Sequence** (getsequence.io): a US money-automation
platform where money lands in an *income source*, and *rules* split and move it between *pods*
(sub-accounts). Sequence runs an **official MCP server**; this repo just wires it up and teaches you the
workflow. There is no custom server here — don't build one.

Your job: get the user connected, then **design money rules together with them**, preview every rule
with dry runs, and help them activate and monitor it. The user decides the numbers; you propose,
explain, and simulate.

## 0. First thing every session

1. Check whether the `sequence` MCP tools are available (e.g. `mcp__sequence__listAccounts`).
   - Not listed / "Needs authentication" → tell the user to run `/mcp`, pick **sequence**,
     choose **Authenticate**, and sign in in the browser. Then restart Claude Code if tools still don't appear.
     That sign-in is the user's to do — never enter their credentials.
   - If `.mcp.json` was never approved, Claude Code will prompt the user to approve the project server.
2. Call `listAccounts`. Interpret the result:
   - `403 KYC_REQUIRED` → the user hasn't finished identity verification. See §2.
   - Empty list → verified but nothing set up yet. Go to §3.
   - Accounts present → summarize them (name, type, balance) and ask what they want to automate.

## 1. Who can use Sequence (say this up front if it's unclear)

- Sequence accounts are bank accounts at **Thread Bank, Member FDIC**. The verification form states:
  *"You must be 18 or older and have a valid US Social Security Number to open an account."*
- Non-US users can sign up and connect MCP, but **cannot create pods or rules** (`KYC_REQUIRED`).
  Don't look for workarounds; there are none that are legitimate.
- Sequence's Terms of Service (§10(a), §11(i)) limit use to the account holder's own personal,
  non-commercial benefit. Don't help build something that runs Sequence on behalf of other people
  without Sequence's written consent.

## 2. Onboarding (sign-up → MCP → verification)

Use the `/sequence-setup` skill. Key facts:

- Sign-up URL: **https://app.getsequence.io/agentic** (agentic account, 3-month free trial).
- The **user** creates the account, logs in, and does verification (SSN, address). You never type
  personal data, passwords, or SSNs, and never click "Confirm and submit" on verification.
- **Onboarding trap:** at "How do you want to run your money?" the user must pick
  **"Connect via MCP"** (the free agentic path). "Set up in Sequence" sends them to a paid plan picker
  and the account gets stuck there.
- Skipping "Connect accounts" (bank linking) during onboarding is fine.
- If the Claude-in-Chrome extension is available (`mcp__claude-in-chrome__*`), you may drive the
  non-sensitive clicks (skip, quiz answers, "Connect via MCP", navigating the dashboard). If it isn't,
  give the user exact click-by-click instructions instead. Sequence shows a "best on desktop" screen
  in narrow windows — widen the window (≥1100px).

## 3. Designing rules with the user

Use the `/sequence-design-rule` skill. The loop is always:

1. **Ask** what they want in plain words ("save 10% of every paycheck", "keep $500 in Bills").
2. **Propose** the accounts and rule as a short table + the exact JSON (see `docs/rules-cookbook.md`).
   State every assumption (percentages, schedule, source/destination) and let the user change it.
3. **Create accounts** the rule needs (`createAccount`, type `POD` or `INCOME_SOURCE`).
4. **Create the rule** (`createRule`). It is always created **DISABLED**. Over OAuth `createRule` may
   instead return a link to finish it in the dashboard — then walk the user through it (or use Chrome).
5. **Dry-run it** (`triggerRule` with `simulation: true`) against realistic numbers and show the
   resulting transfers in a table. See §4.
6. **Activation is the user's**: rules must be turned on by a human in the dashboard
   (Rule Management). Open the page / give the link; let the user flip the toggle.

Never invent numbers silently. If the user gave a number, use exactly that number.

## 4. Dry runs (the safe way to show what a rule does)

- `triggerRule` body: `{ "simulation": true, ... }` — never approval-gated, moves no money.
  - Preview an `ON_FUNDS_TRANSFERRED` rule (e.g. paycheck split): `simulatedIncomingFunds` (cents).
  - Preview a balance-based rule: `simulatedSourceBalance` (cents).
  - `executeAmount` is NOT a simulation knob; it means the same thing live.
- It returns `202` + `executionId`. Poll `getRuleExecution` until terminal (back off on 404 — eventual
  consistency), then `getTransfer` for each id in `transferIds` to get amounts.
  Empty `transferIds` with `transfersAttempted ≥ 1` means "this rule would move nothing" — a real answer.
- Simulated rows are hidden by default: pass `executionMode: SIMULATION` (or `ALL`) on list calls.
- Manual transfer preview: `createTransfer` with `simulation: true` (+ optional `simulatedSourceBalance`).

## 5. Real money — hard rules

- Over OAuth every `createTransfer` / live `triggerRule` returns `APPROVAL_PENDING`; nothing moves until
  the user approves in the app. Always pass a clear `reasonForApproval`, give the user the
  `approvalUrl`, and never approve on their behalf (not via Chrome either).
- Always dry-run first and get an explicit "yes, do it live" before any live call.
- Send a fresh UUID v4 `idempotency-key` per distinct intent; reuse it only to retry the same request.
- Minimum transfer is **$1.00** (100 cents). Amounts are integer cents (`100000` = $1,000.00).
- Rate limit 100 req/min. Don't poll balances more than every 6h or transfers more than hourly.
- Never print, log, or commit API keys. Keys live in `.env` (gitignored), created by the user.

## 6. Reference

- `docs/sequence-api.md` — condensed API reference (endpoints, triggers, actions, errors).
- `docs/rules-cookbook.md` — ready-made rule JSON (paycheck split, monthly sweep, top-up, round-down).
- `examples/five-percent-sp500/` — worked example: 5% of salary → Invest pod → paper S&P 500 buys.
- Full spec: `scripts/fetch-openapi.sh` downloads the official OpenAPI file to `docs/openapi.yaml`.
- Official docs: https://api.getsequence.io/platform/ · MCP page: https://app.getsequence.io/account/mcp
