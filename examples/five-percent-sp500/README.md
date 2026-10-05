# Example: "5% to the S&P 500, run by Claude"

A worked example of the kit. Salary lands → 5% goes to an Invest pod → each arrival is mirrored as a
**paper** buy of an S&P 500 ETF on Alpaca (fake money) → Claude writes a monthly report.

## 1. Accounts and rules (in Claude Code)

Ask Claude: *"Set up the 5% S&P example from examples/five-percent-sp500."* It will use
`/sequence-design-rule` to propose, then (after you agree) create:

| Account | Type |
|---|---|
| Salary | INCOME_SOURCE |
| Invest, Tax, Spending | POD |

- **Rule A — Paycheck split** (`ON_FUNDS_TRANSFERRED` on Salary): 5% → Invest, 20% → Tax, 75% → Spending.
- **Rule B — Monthly sweep** (`SCHEDULED`, `MONTHLY`, on the 1st): 5% of the Spending balance → Invest.

JSON for both is in `docs/rules-cookbook.md`. Then Claude dry-runs them, e.g.
*"simulate a $3,000 salary"* → $150 Invest / $600 Tax / $2,250 Spending, and
*"run Rule B against a $1,200 balance"* → $60. You enable the rules in the dashboard yourself.

## 2. Paper investing (optional script)

This part runs outside chat, so it uses an API key instead of OAuth:

1. Sequence dashboard → **Agents → API Keys → Create key**, named e.g. `paper-invest-readonly`, with only
   `READ_ACCOUNTS` and `READ_TRANSFERS` on the Invest pod. No money-movement permissions.
2. (Optional) Free Alpaca paper account → paper API keys. Without them the script logs a dry run.
3. Copy `.env.example` → `.env` at the repo root and fill in the values (`.env` is gitignored).
4. Run:

```bash
python examples/five-percent-sp500/paper_invest.py                       # real (live) transfers
python examples/five-percent-sp500/paper_invest.py --include-simulations # also mirror dry runs
```

Every new completed transfer into Invest becomes one notional market buy of `INVEST_SYMBOL` (default `SPY`),
logged in `investments.csv`. Already-processed transfer ids are kept in `state.json`, so re-runs are safe.
Schedule it daily (Task Scheduler / cron) if you like.

## 3. Monthly report

Ask Claude: *"/sequence-status monthly report, include examples/five-percent-sp500/investments.csv"*.
It summarizes balances, what each rule moved, the paper portfolio's contributions, and may suggest a
different percentage — you decide whether to change anything.

Paper trading only. Nothing here is investment advice.
