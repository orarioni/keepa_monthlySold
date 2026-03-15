from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
import os
from pathlib import Path
from typing import Any

import pandas as pd

CACHE_COLUMNS = [
    "asin",
    "last_fetched_at",
    "last_success_at",
    "last_failure_at",
    "keepa_title",
    "keepa_lastSoldUpdate",
    "keepa_monthlySold",
    "keepa_salesRankDrops30",
    "estimate_source",
    "estimate_confidence",
    "estimate_note",
    "failure_type",
    "rows_seen_in_input",
    "fetch_priority",
    "next_fetch_after",
    "consecutive_errors",
    "consecutive_failures",
    "last_error",
    "last_result_status",
    "last_change_at",
]

DEFAULT_REFRESH_POLICY = {
    "active_high_days": 1,
    "active_medium_days": 3,
    "active_low_days": 7,
    "inactive_days": 30,
    "max_retry_backoff_days": 30,
    "inactive_unchanged_days": 30,
}


@dataclass
class QueueDecision:
    asin: str
    queued: bool
    decision: str
    priority: str
    reason: str


def safe_float(value: Any) -> float | None:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    if pd.isna(number):
        return None
    return number


def parse_dt(value: Any) -> datetime | None:
    if value is None:
        return None
    text = str(value).strip()
    if not text:
        return None
    try:
        return pd.to_datetime(text).to_pydatetime()
    except Exception:  # noqa: BLE001
        return None


def read_consecutive_errors(row: Any) -> int:
    """Backward compatibility: prefer consecutive_errors, fallback to consecutive_failures."""
    return int(safe_float(row.get("consecutive_errors")) or safe_float(row.get("consecutive_failures")) or 0)


def normalize_result_status(value: Any) -> str:
    if value is None:
        return ""
    text = str(value).strip().lower()
    if not text or text == "nan":
        return ""
    return text


def load_cache(cache_path: Path) -> pd.DataFrame:
    if not cache_path.exists():
        return pd.DataFrame(columns=CACHE_COLUMNS)

    cache = pd.read_csv(cache_path, dtype={"asin": str})
    for col in CACHE_COLUMNS:
        if col not in cache.columns:
            cache[col] = None
    return cache[CACHE_COLUMNS]


def save_cache(cache: pd.DataFrame, cache_path: Path, logger: Any = None) -> None:
    ordered = cache.copy()
    for col in CACHE_COLUMNS:
        if col not in ordered.columns:
            ordered[col] = None

    tmp_path = cache_path.with_name(f"{cache_path.name}.tmp")
    try:
        ordered[CACHE_COLUMNS].to_csv(tmp_path, index=False, encoding="utf-8")
        os.replace(tmp_path, cache_path)
    except Exception:
        if tmp_path.exists():
            tmp_path.unlink(missing_ok=True)
        if logger is not None:
            logger.exception("cache_save_failed path=%s", cache_path)
        raise


def _get_refresh_days(monthly_sold: Any, refresh_policy: dict[str, int] | None = None) -> int:
    policy = {**DEFAULT_REFRESH_POLICY, **(refresh_policy or {})}
    monthly = safe_float(monthly_sold)
    if monthly is not None and monthly >= 100:
        return int(policy["active_high_days"])
    if monthly is not None and monthly >= 30:
        return int(policy["active_medium_days"])
    if monthly is not None and monthly >= 1:
        return int(policy["active_low_days"])
    return int(policy["inactive_days"])


def _get_priority(monthly_sold: Any) -> str:
    monthly = safe_float(monthly_sold)
    if monthly is not None and monthly >= 100:
        return "high"
    if monthly is not None and monthly >= 30:
        return "medium"
    return "low"


def compute_next_fetch_after(
    now: datetime,
    monthly_sold: Any,
    consecutive_errors: int = 0,
    refresh_policy: dict[str, int] | None = None,
) -> datetime:
    policy = {**DEFAULT_REFRESH_POLICY, **(refresh_policy or {})}

    if consecutive_errors >= 1:
        backoff_days = min(int(policy["max_retry_backoff_days"]), 2 ** consecutive_errors)
        return now + timedelta(days=backoff_days)

    refresh_days = _get_refresh_days(monthly_sold=monthly_sold, refresh_policy=policy)
    return now + timedelta(days=refresh_days)


def decide_fetch_queue(valid_asins: list[str], rows_seen: dict[str, int], cache: pd.DataFrame, now: datetime) -> list[QueueDecision]:
    del rows_seen
    cache_idx = cache.set_index("asin", drop=False) if not cache.empty else pd.DataFrame(columns=CACHE_COLUMNS).set_index("asin", drop=False)
    decisions: list[QueueDecision] = []
    policy = DEFAULT_REFRESH_POLICY
    inactive_unchanged_days = int(policy["inactive_unchanged_days"])

    for asin in valid_asins:
        row = cache_idx.loc[asin] if asin in cache_idx.index else None
        if row is None:
            decisions.append(QueueDecision(asin=asin, queued=True, decision="new", priority="high", reason="cache_missing"))
            continue

        monthly = safe_float(row.get("keepa_monthlySold"))
        next_fetch_after = parse_dt(row.get("next_fetch_after"))
        last_change_at = parse_dt(row.get("last_change_at"))
        consecutive_errors = read_consecutive_errors(row)
        last_result_status = normalize_result_status(row.get("last_result_status"))

        # 1) retry/backoff lane (must be evaluated before refresh)
        if consecutive_errors >= 1:
            if next_fetch_after is None or next_fetch_after <= now:
                decisions.append(QueueDecision(asin=asin, queued=True, decision="retry", priority="high", reason="retry_backoff_due"))
            else:
                decisions.append(QueueDecision(asin=asin, queued=False, decision="skip", priority="low", reason="retry_backoff_active"))
            continue

        if monthly is None and last_result_status and last_result_status != "success":
            if next_fetch_after is None or next_fetch_after <= now:
                decisions.append(QueueDecision(asin=asin, queued=True, decision="retry", priority="high", reason="retry_missing_monthly_sold_after_failure"))
            else:
                decisions.append(QueueDecision(asin=asin, queued=False, decision="skip", priority="low", reason="retry_waiting_after_failure"))
            continue

        # 2) inactive lane (low-frequency monitoring, not permanent stop)
        if monthly is None or monthly <= 0:
            if last_change_at is not None and last_change_at <= (now - timedelta(days=inactive_unchanged_days)):
                inactive_due = next_fetch_after is None or next_fetch_after <= now
                if inactive_due:
                    decisions.append(QueueDecision(asin=asin, queued=True, decision="inactive", priority="low", reason="inactive_monitor_due"))
                else:
                    decisions.append(QueueDecision(asin=asin, queued=False, decision="inactive", priority="low", reason="inactive_monitor_wait"))
                continue

            if next_fetch_after is None:
                decisions.append(QueueDecision(asin=asin, queued=False, decision="inactive", priority="low", reason="inactive_monitor_wait"))
                continue

        # 3) normal freshness lane
        target_priority = _get_priority(monthly)
        if next_fetch_after is None:
            decisions.append(QueueDecision(asin=asin, queued=True, decision="refresh", priority=target_priority, reason="next_fetch_after_missing"))
        elif next_fetch_after <= now:
            decisions.append(QueueDecision(asin=asin, queued=True, decision="refresh", priority=target_priority, reason="next_fetch_after_due"))
        else:
            decisions.append(QueueDecision(asin=asin, queued=False, decision="skip", priority="low", reason="cache_fresh"))

    return decisions


def merge_cache_records(cache: pd.DataFrame, records: list[dict[str, Any]]) -> pd.DataFrame:
    if not records:
        return cache

    updates = pd.DataFrame(records)
    for col in CACHE_COLUMNS:
        if col not in updates.columns:
            updates[col] = None

    if cache.empty:
        return updates[CACHE_COLUMNS]

    cache = cache.set_index("asin", drop=False)
    updates = updates.set_index("asin", drop=False)
    cache.update(updates)

    missing = updates.loc[~updates.index.isin(cache.index)]
    if not missing.empty:
        cache = pd.concat([cache, missing], axis=0)

    return cache.reset_index(drop=True)[CACHE_COLUMNS]
