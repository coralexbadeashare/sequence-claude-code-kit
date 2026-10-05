# Rules cookbook

Starting points for `createRule`. Replace `<...>` ids with real ones from `listAccounts`.
Percentages and amounts are placeholders — always confirm them with the user.

## Split every paycheck by percentage

"When money lands in Salary, send 5% to Invest, 20% to Tax, the rest (75%) to Spending."

```json
{
  "name": "Paycheck split",
  "trigger": { "type": "ON_FUNDS_TRANSFERRED", "accountId": "<salary-income-source-id>" },
  "steps": [
    {
      "conditions": null,
      "actions": [
        { "type": "PERCENTAGE", "percentageValue": 5,  "percentageTarget": "INCOMING_AMOUNT",
          "source": { "id": "<salary-id>", "type": "INCOME_SOURCE" }, "destination": { "id": "<invest-pod-id>", "type": "POD" }, "groupIndex": 0 },
        { "type": "PERCENTAGE", "percentageValue": 20, "percentageTarget": "INCOMING_AMOUNT",
          "source": { "id": "<salary-id>", "type": "INCOME_SOURCE" }, "destination": { "id": "<tax-pod-id>", "type": "POD" }, "groupIndex": 0 },
        { "type": "PERCENTAGE", "percentageValue": 75, "percentageTarget": "INCOMING_AMOUNT",
          "source": { "id": "<salary-id>", "type": "INCOME_SOURCE" }, "destination": { "id": "<spending-pod-id>", "type": "POD" }, "groupIndex": 0 }
      ]
    }
  ]
}
```

Dry run: `triggerRule` `{ "simulation": true, "simulatedIncomingFunds": 300000 }` → expect $150 / $600 / $2,250.

## Monthly sweep: % of a pod's balance

"On the 1st of every month, move 5% of whatever is in Spending to Invest."

```json
{
  "name": "Monthly 5% sweep",
  "trigger": { "type": "SCHEDULED", "scheduleType": "MONTHLY", "startDate": "<YYYY-MM-01>T14:00:00Z", "accountId": "<spending-pod-id>" },
  "steps": [
    {
      "conditions": null,
      "actions": [
        { "type": "PERCENTAGE", "percentageValue": 5, "percentageTarget": "SOURCE_ACCOUNT",
          "source": { "id": "<spending-pod-id>", "type": "POD" }, "destination": { "id": "<invest-pod-id>", "type": "POD" }, "groupIndex": 0 }
      ]
    }
  ]
}
```

Dry run: `{ "simulation": true, "simulatedSourceBalance": 120000 }` → expect $60.
`startDate` sets the day of month; 14:00 UTC is morning in the US.

## Sweep everything above a buffer

"Each month, leave $2,000 in Spending and move the rest to Savings."

```json
{
  "name": "Sweep above buffer",
  "trigger": { "type": "SCHEDULED", "scheduleType": "MONTHLY", "startDate": "<YYYY-MM-28>T14:00:00Z", "accountId": "<spending-pod-id>" },
  "steps": [
    { "conditions": null,
      "actions": [
        { "type": "ROUND_DOWN", "amountInCents": 200000,
          "source": { "id": "<spending-pod-id>", "type": "POD" }, "destination": { "id": "<savings-pod-id>", "type": "POD" }, "groupIndex": 0 }
      ] }
  ]
}
```

## Keep a pod topped up

"When income arrives, top Bills up to $1,500 first; send the remainder's 10% to Savings."
Use two steps only if you need conditions; otherwise put both actions in one step:

```json
{
  "name": "Bills top-up",
  "trigger": { "type": "ON_FUNDS_TRANSFERRED", "accountId": "<income-id>" },
  "steps": [
    { "conditions": null,
      "actions": [
        { "type": "TOP_UP", "amountInCents": 150000, "nextPaymentMinimumAccount": null, "currentBalanceAccount": null, "lastStatementBalanceAccount": null,
          "source": { "id": "<income-id>", "type": "INCOME_SOURCE" }, "destination": { "id": "<bills-pod-id>", "type": "POD" }, "groupIndex": 0, "upToEnabled": true },
        { "type": "PERCENTAGE", "percentageValue": 10, "percentageTarget": "INCOMING_AMOUNT",
          "source": { "id": "<income-id>", "type": "INCOME_SOURCE" }, "destination": { "id": "<savings-pod-id>", "type": "POD" }, "groupIndex": 1 }
      ] }
  ]
}
```

## Fixed amount on a schedule

"Every Friday move $100 from Checking-income to Vacation."
Action: `{ "type": "FIXED", "amountInCents": 10000, ... }`, trigger `SCHEDULED` / `WEEKLY` with a Friday `startDate`.
Note: `executeAmount` never changes a `FIXED` action.

## Tips

- Percentages of the same incoming amount: keep the total ≤ 100.
- Anything under $1.00 isn't transferred (counts in `transfersAttempted`, no transfer id).
- Conditions (e.g. only when balance > X) use `ChainableRuleCondition` — check `docs/openapi.yaml`
  (`RuleCondition`, `RuleConditionFact`, `RuleConditionOperator`) before writing one.
- After creating, `getRule` shows the stored shape; rules are DISABLED until the user enables them.
