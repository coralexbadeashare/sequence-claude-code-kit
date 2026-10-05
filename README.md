# Sequence × Claude Code

Automate your money with [Sequence](https://www.getsequence.io) by talking to Claude Code.
Open this folder in Claude Code and it already knows how to connect to Sequence's official MCP server,
walk you through sign-up, and design money rules **with you** — split paychecks, sweep balances,
keep bills topped up — previewing every rule with a dry run before anything is real.

No custom server, no code to install, no API key needed for chat.

## Quick start (about 3 minutes)

```bash
git clone <this repo> && cd <repo>
claude
```

1. Claude Code asks to approve the project MCP server **sequence** → approve.
2. Say **"set me up"**. Claude checks the connection and guides you:
   - no Sequence account yet → it opens https://app.getsequence.io/agentic; you sign up
     (at "How do you want to run your money?" pick **Connect via MCP**)
   - then `/mcp` → **sequence** → **Authenticate** → sign in in the browser
3. Say what you want, e.g. *"put 10% of every paycheck into savings"*. Claude proposes the rule,
   creates it after you agree, dry-runs it with example amounts, and tells you where to switch it on.

If the [Claude in Chrome](https://claude.ai/chrome) extension is installed, Claude can click through the
non-sensitive dashboard steps for you. Sign-in, identity verification and approving real transfers
are always yours.

## Requirements

- [Claude Code](https://claude.com/claude-code)
- A Sequence account with completed identity verification. **Sequence requires a valid US Social
  Security Number** (accounts are held at Thread Bank, Member FDIC). Without it you can sign up and
  connect, but can't create pods or rules.

## Safety model

- Claude connects over **OAuth**: every real money movement comes back `APPROVAL_PENDING` and waits for
  you to approve it in the Sequence app. Rules are created **disabled**; only you can enable them.
- Read-only tools are pre-allowed in `.claude/settings.json`; creating accounts/rules and triggering
  money movement always prompt you in Claude Code.
- Dry runs (`simulation: true`) move nothing and need no approval — Claude uses them for every preview.
- Sequence's terms allow use for your own, personal, non-commercial purposes.

## What's inside

| Path | Purpose |
|---|---|
| `CLAUDE.md` | Instructions Claude follows: setup, rule-design loop, dry runs, guardrails |
| `.mcp.json` | Sequence MCP server (OAuth) |
| `.claude/settings.json` | Permission defaults (reads allowed, writes ask) |
| `.claude/skills/` | `/sequence-setup`, `/sequence-design-rule`, `/sequence-status` |
| `docs/sequence-api.md` | Condensed API reference |
| `docs/rules-cookbook.md` | Ready-made rule JSON |
| `examples/five-percent-sp500/` | Worked example: 5% of salary → Invest pod → paper S&P 500 buys + monthly report |
| `scripts/fetch-openapi.sh` | Downloads the full official OpenAPI spec |

## Things to try

- "What accounts do I have and how much is in each?"
- "Split my paycheck: 20% taxes, 10% savings, rest to spending. Simulate a $4,000 paycheck."
- "Every month leave $1,500 in Spending and move the rest to Savings."
- "Monthly report: what did my rules move in September?"

Not affiliated with Sequence. Not financial advice.
