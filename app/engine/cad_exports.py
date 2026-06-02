from __future__ import annotations

import csv
from io import StringIO
from typing import Any, Dict, Iterable, List


def rows_to_csv(rows: Iterable[Dict[str, Any]]) -> str:
    rows = list(rows)
    out = StringIO()
    if not rows:
        return ""
    writer = csv.DictWriter(out, fieldnames=list(rows[0].keys()))
    writer.writeheader()
    for row in rows:
        writer.writerow(row)
    return out.getvalue()
