"""
Generate sample_data/support_tickets.xlsx, the dataset for the live Ollama
verification (P2-24).

The Sprint 14 live run used Test_data.xlsx, a real-world file that was never
tracked, so nobody else could repeat it. This dataset is synthetic, seeded,
and committed: it has the same shape of problem (customer-support tickets
with categories, priorities, resolution times, refunds and satisfaction
scores), a few missing values so cleaning has work to do, and one personal
data column (on reserved example.com addresses) so PII masking is exercised.

    python scripts/make_live_sample.py            # rewrite the file
    python scripts/make_live_sample.py --check    # exit 1 if the content differs

The content is reproducible from the seed; the .xlsx bytes are not (the
workbook records its creation time), so --check compares cell values.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[1]
TARGET = REPO / "sample_data" / "support_tickets.xlsx"
SEED = 20261014
ROWS = 400


def build() -> pd.DataFrame:
    rng = np.random.default_rng(SEED)
    regions = rng.choice(["North America", "Europe", "Asia Pacific", "Latin America"], ROWS, p=[0.4, 0.3, 0.2, 0.1])
    products = rng.choice(["Analytics Suite", "Data Connector", "Mobile App", "Billing Portal"], ROWS)
    channels = rng.choice(["Email", "Chat", "Phone", "Web Form"], ROWS, p=[0.35, 0.3, 0.2, 0.15])
    priority = rng.choice(["Low", "Medium", "High", "Critical"], ROWS, p=[0.3, 0.4, 0.22, 0.08])
    category = rng.choice(
        ["Login issue", "Data sync failure", "Billing dispute", "Feature request", "Performance", "Bug report"], ROWS
    )

    base_hours = {"Low": 40.0, "Medium": 24.0, "High": 10.0, "Critical": 4.0}
    resolution = np.array([rng.gamma(2.0, base_hours[p] / 2.0) for p in priority]).round(1)
    # Slow resolutions and billing disputes cost satisfaction; that is the signal to find.
    satisfaction = 5.0 - resolution / 25.0 - (category == "Billing dispute") * 0.8 + rng.normal(0, 0.5, ROWS)
    satisfaction = np.clip(satisfaction, 1, 5).round(1)
    refund = np.where(category == "Billing dispute", rng.gamma(2.0, 60.0, ROWS), 0.0).round(2)

    created = pd.Timestamp("2026-07-01") + pd.to_timedelta(rng.integers(0, 92 * 24, ROWS), unit="h")
    frame = pd.DataFrame(
        {
            "ticket_id": [f"TCK-{10000 + i}" for i in range(ROWS)],
            "created_at": created.strftime("%Y-%m-%d %H:%M"),
            "region": regions,
            "product": products,
            "channel": channels,
            "priority": priority,
            "category": category,
            "resolution_hours": resolution,
            "satisfaction_score": satisfaction,
            "refund_amount": refund,
            "customer_email": [f"customer{int(n)}@example.com" for n in rng.integers(1000, 9999, ROWS)],
        }
    )
    # ~4% gaps in two measures, so the cleaning policy matters.
    for column in ("resolution_hours", "satisfaction_score"):
        frame.loc[rng.random(ROWS) < 0.04, column] = np.nan
    return frame


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--check", action="store_true", help="fail if the committed file's content differs")
    args = parser.parse_args(argv)

    frame = build()
    if args.check:
        committed = pd.read_excel(TARGET, engine="openpyxl")
        if not committed.equals(frame):
            print(f"{TARGET.relative_to(REPO)} differs from the seeded content", file=sys.stderr)
            return 1
        return 0
    frame.to_excel(TARGET, index=False, engine="openpyxl")
    print(f"wrote {TARGET.relative_to(REPO)} ({len(frame)} rows)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
