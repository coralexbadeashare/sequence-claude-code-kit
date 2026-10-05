"""Mirror money arriving in a Sequence "Invest" pod as paper buys of an S&P 500 ETF.

Reads completed transfers into the Invest pod from the Sequence REST API and, for each one not yet
seen, places a notional market buy on Alpaca *paper* trading (fake money). Everything is logged to
a CSV. Without Alpaca keys it only logs what it would have bought (dry run).

Needs only the Python standard library. Configure via environment or a .env file next to the repo root:
  SEQUENCE_API_KEY       read-only key (READ_ACCOUNTS + READ_TRANSFERS on the Invest pod)
  SEQUENCE_INVEST_POD_ID id of the Invest pod (from listAccounts)
  ALPACA_KEY_ID / ALPACA_SECRET_KEY   optional, paper-trading keys
  INVEST_SYMBOL          optional, default SPY

Usage:
  python paper_invest.py                    # live Sequence transfers only
  python paper_invest.py --include-simulations   # also mirror dry-run transfers (handy for demos)
"""

import argparse
import csv
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
STATE_FILE = HERE / "state.json"
LOG_FILE = HERE / "investments.csv"
SEQUENCE_BASE = "https://api.getsequence.io/platform/v1"
ALPACA_BASE = "https://paper-api.alpaca.markets/v2"


def load_dotenv(path):
    if not path.exists():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            key, value = line.split("=", 1)
            os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


def http_json(method, url, headers, body=None):
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(url, data=data, method=method, headers={**headers, "Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read() or b"{}")
    except urllib.error.HTTPError as e:
        detail = e.read().decode(errors="replace")
        raise SystemExit(f"{method} {url} -> HTTP {e.code}: {detail}")


def invest_transfers(api_key, pod_id, execution_mode):
    headers = {"Authorization": f"Bearer {api_key}"}
    page = 1
    while True:
        query = urllib.parse.urlencode({
            "accountRole": "destination",
            "status": "COMPLETE",
            "executionMode": execution_mode,
            "page": page,
            "pageSize": 100,
        })
        data = http_json("GET", f"{SEQUENCE_BASE}/accounts/{pod_id}/transfers?{query}", headers)["data"]
        yield from data["items"]
        if not data["pagination"]["hasNextPage"]:
            return
        page += 1


def paper_buy(symbol, dollars):
    headers = {
        "APCA-API-KEY-ID": os.environ["ALPACA_KEY_ID"],
        "APCA-API-SECRET-KEY": os.environ["ALPACA_SECRET_KEY"],
    }
    order = {"symbol": symbol, "notional": f"{dollars:.2f}", "side": "buy", "type": "market", "time_in_force": "day"}
    return http_json("POST", f"{ALPACA_BASE}/orders", headers, order)


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--include-simulations", action="store_true", help="also mirror simulated (dry-run) transfers")
    args = parser.parse_args()

    load_dotenv(ROOT / ".env")
    api_key = os.environ.get("SEQUENCE_API_KEY")
    pod_id = os.environ.get("SEQUENCE_INVEST_POD_ID")
    if not api_key or not pod_id:
        sys.exit("Set SEQUENCE_API_KEY and SEQUENCE_INVEST_POD_ID (see .env.example).")
    symbol = os.environ.get("INVEST_SYMBOL", "SPY")
    have_alpaca = bool(os.environ.get("ALPACA_KEY_ID") and os.environ.get("ALPACA_SECRET_KEY"))

    seen = set(json.loads(STATE_FILE.read_text())) if STATE_FILE.exists() else set()
    new_log = not LOG_FILE.exists()
    mode = "ALL" if args.include_simulations else "LIVE"

    placed = 0
    with LOG_FILE.open("a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        if new_log:
            writer.writerow(["logged_at", "transfer_id", "transfer_completed_at", "execution_mode", "from_account", "amount_usd", "symbol", "order_status", "order_id"])
        for t in invest_transfers(api_key, pod_id, mode):
            if t["id"] in seen:
                continue
            dollars = t["amountInCents"] / 100
            if have_alpaca:
                order = paper_buy(symbol, dollars)
                status, order_id = order.get("status", "submitted"), order.get("id", "")
            else:
                status, order_id = "dry_run", ""
            source = (t.get("source") or {}).get("name", "")
            writer.writerow([datetime.now(timezone.utc).isoformat(), t["id"], t.get("completedAt"), t.get("executionMode"), source, f"{dollars:.2f}", symbol, status, order_id])
            seen.add(t["id"])
            placed += 1
            print(f"{status}: ${dollars:.2f} of {symbol} for transfer {t['id']} ({t.get('executionMode')})")

    STATE_FILE.write_text(json.dumps(sorted(seen)))
    print(f"Done. {placed} new transfer(s) mirrored. Log: {LOG_FILE}")


if __name__ == "__main__":
    main()
