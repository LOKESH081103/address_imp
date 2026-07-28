"""
geo_summary.py - Critical/Clean breakdown by a geography column (State,
Zone, Sub Zone, Main Region, Sub Region, or Area).

Two flavors, same shape:
  - address-level:   breakdown_by_group(result_df, group_col)
  - agreement-level:  breakdown_by_group(agreement_rollup_df, group_col,
                       count_col="Address Count") - counts ADDRESSES within
                       each agreement's bucket, not just agreements, so a
                       state's numbers stay comparable whether you're
                       looking at addresses or the agreements that own them.

Severity is two-tier (Critical / Clean - see rule_engine.severity_for), so
this only ever needs two buckets, not three.
"""

import pandas as pd


def breakdown_by_group(df: pd.DataFrame, group_col: str, severity_col: str = "Severity",
                        count_col: str = None) -> pd.DataFrame:
    """
    One row per distinct value in group_col: Total / Critical / Clean counts
    and Critical %. Rows with a blank/NaN group value are bucketed as
    "Unknown" rather than dropped, so nothing silently disappears from the
    totals.

    If count_col is given, that column's values are SUMMED per group instead
    of counting rows - use this for the agreement-level rollup, where each
    row is one agreement but you want to report on how many addresses that
    represents (agreement_rollup_df's "Address Count" column).
    """
    if df is None or df.empty or group_col not in df.columns:
        return pd.DataFrame(columns=["Group", "Total", "Critical", "Clean", "Critical %"])

    work = df.copy()
    work[group_col] = work[group_col].fillna("Unknown").astype(str).str.strip()
    work.loc[work[group_col] == "", group_col] = "Unknown"

    is_critical = work[severity_col] == "Critical"
    weight = work[count_col] if count_col else 1

    work["_critical_w"] = is_critical * weight if count_col else is_critical.astype(int)
    work["_total_w"] = weight if count_col else 1

    grouped = work.groupby(group_col, sort=False).agg(
        Total=("_total_w", "sum"),
        Critical=("_critical_w", "sum"),
    ).reset_index().rename(columns={group_col: "Group"})

    grouped["Total"] = grouped["Total"].astype(int)
    grouped["Critical"] = grouped["Critical"].astype(int)
    grouped["Clean"] = grouped["Total"] - grouped["Critical"]
    grouped["Critical %"] = (100 * grouped["Critical"] / grouped["Total"].replace(0, pd.NA)).round(1).fillna(0.0)

    return grouped.sort_values("Critical", ascending=False).reset_index(drop=True)
