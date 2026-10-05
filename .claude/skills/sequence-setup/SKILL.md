---
name: sequence-setup
description: Get a user from zero to a connected Sequence account (sign-up, "Connect via MCP", MCP OAuth sign-in, identity verification). Use when the sequence MCP tools are missing, unauthenticated, or return KYC_REQUIRED, or when the user says "set up Sequence".
---

# Sequence setup

Goal: the `sequence` MCP server is authenticated and `listAccounts` succeeds.
The user does every step that involves their identity or credentials; you guide and do the harmless clicks.

## Step 1 — Is MCP already working?

Call `mcp__sequence__listAccounts`.
- Works → setup is done (if it lists accounts, hand off to `/sequence-status`).
- `KYC_REQUIRED` → go to Step 4.
- Tool missing or "Needs authentication" → Step 2.

## Step 2 — Does the user have a Sequence account?

Ask once. If **no**:

1. Tell the user the eligibility up front: Sequence requires a **valid US Social Security Number**
   (accounts are held at Thread Bank, Member FDIC). Non-US users can sign up but can't create pods or rules.
2. Open **https://app.getsequence.io/agentic** — in Chrome via `mcp__claude-in-chrome__*` if available
   (call `tabs_context_mcp` first, open a new tab), otherwise give the user the link.
3. The **user** signs up (email or Google) and confirms their email. Don't type their details.
4. Onboarding screens (you may click these in Chrome, or tell the user):
   - "Connect accounts" → **Skip for now** is fine.
   - Short quiz (4 questions) → ask the user, or pick what matches what they told you.
   - **"How do you want to run your money?" → click "Connect via MCP".**
     Do NOT choose "Set up in Sequence": it leads to a paid plan picker and the account gets stuck there.
   - "Connect your agent using MCP" → choose **Claude Code**, then **Continue**.
   - If a page says "Sequence is best on desktop", widen the browser window (≥ 1100px).

## Step 3 — Connect Claude Code

This repo's `.mcp.json` already declares the server (OAuth, no API key). The user:
1. Approves the project MCP server when Claude Code asks (or runs `/mcp`).
2. In `/mcp` → **sequence** → **Authenticate** → signs in to Sequence in the browser and consents.
3. Restarts Claude Code if the tools don't appear.

Alternative if they're not using this repo's `.mcp.json`:
`claude mcp add --transport http sequence https://app.getsequence.io/api/mcp`

Then retry Step 1.

## Step 4 — Identity verification (KYC)

Pods, income sources and rules all require it. The **user** completes it:
dashboard → Account List → Add account → Create a Pod → "Start verification"
(or https://app.getsequence.io/kyc). It asks for basics, home address, SSN, and a short financial profile;
approval usually takes ~30 minutes.

Never fill in, check the consent box, or submit this form for the user. If the user has no US SSN,
say plainly that Sequence can't hold accounts for them, and stop here.

## Done

Confirm with `listAccounts`, then suggest `/sequence-design-rule` to build their first automation.
