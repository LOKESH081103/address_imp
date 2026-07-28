"""
zone_mapping.py - Branch -> Zone/Sub Zone/Region hierarchy lookup.

Source of truth: the "Overall Base" sheet of the company's zone master
workbook (zone_ye.xlsb), which has one clean row per branch mapping it to
its Area / Sub Region / Main Region / Sub Zone / Zone. That sheet is
re-extracted (deduplicated, ~910 unique branches, verified 1 hierarchy per
branch - no conflicting rows) into branch_zone_map.csv, a small file shipped
alongside this module - so the app doesn't need to carry the original 10MB
.xlsb around or depend on pyxlsb at runtime just to read nine columns.

To refresh this mapping later (branches renamed/added/re-zoned), re-run:
    python zone_mapping.py rebuild path/to/new_zone_master.xlsb
which re-extracts and overwrites branch_zone_map.csv from that workbook's
"Overall Base" sheet (requires `pip install pyxlsb`, only for the rebuild).
"""

import os

import pandas as pd

MAP_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "branch_zone_map.csv")

HIERARCHY_LEVELS = ["Zone", "Sub Zone", "Main Region", "Sub Region", "Area", "Branch"]


def _normalize_branch(name: str) -> str:
    return " ".join(str(name).strip().upper().split())


_map_df = None
_lookup = None


def _load():
    global _map_df, _lookup
    if _map_df is not None:
        return
    if os.path.exists(MAP_FILE):
        _map_df = pd.read_csv(MAP_FILE, keep_default_na=False, na_values=[])
    else:
        _map_df = pd.DataFrame(columns=HIERARCHY_LEVELS)
    _lookup = {
        _normalize_branch(row["Branch"]): row.to_dict()
        for _, row in _map_df.iterrows()
    }


def is_available() -> bool:
    """Whether a branch->zone map is actually loaded (file present, non-empty)."""
    _load()
    return len(_map_df) > 0


def known_branch_count() -> int:
    _load()
    return len(_map_df)


def lookup_branch(branch_name: str) -> dict:
    """
    Returns {"Zone": ..., "Sub Zone": ..., "Main Region": ..., "Sub Region": ...,
    "Area": ..., "Branch": ...} for a branch name, or all "Unknown" if the
    branch isn't in the map (e.g. a typo, a new/closed branch not yet in the
    master, or the file simply wasn't in scope for a rebuild).
    """
    _load()
    hit = _lookup.get(_normalize_branch(branch_name))
    if hit:
        return {level: hit.get(level, "Unknown") or "Unknown" for level in HIERARCHY_LEVELS}
    return {level: "Unknown" for level in HIERARCHY_LEVELS}


def add_zone_columns(df: pd.DataFrame, branch_col: str, levels=("Zone", "Sub Zone")) -> pd.DataFrame:
    """
    Returns a copy of df with one new column per requested hierarchy level,
    looked up from branch_col. Unmapped/missing branches get "Unknown"
    rather than raising - a few unmapped rows shouldn't block the report.
    """
    _load()
    out = df.copy()
    if branch_col not in out.columns:
        for level in levels:
            out[level] = "Unknown"
        return out
    resolved = out[branch_col].map(lambda b: lookup_branch(b))
    for level in levels:
        out[level] = resolved.map(lambda d: d[level])
    return out


def rebuild_from_xlsb(xlsb_path: str, out_path: str = MAP_FILE) -> pd.DataFrame:
    """
    Re-extract the branch->zone map from a zone master workbook's
    "Overall Base" sheet. Requires `pip install pyxlsb`. Run this whenever
    the company reshuffles branches/zones and you get a new master file.
    """
    df = pd.read_excel(xlsb_path, sheet_name="Overall Base ", engine="pyxlsb")
    combo = df[["BRANCH NAME", "NEW AREA", "SUB REGION", "MAIN REGION", "Sub Zone", "ZONE NEW"]].drop_duplicates()
    combo.columns = ["Branch", "Area", "Sub Region", "Main Region", "Sub Zone", "Zone"]
    combo = combo[HIERARCHY_LEVELS]
    for c in combo.columns:
        combo[c] = combo[c].astype(str).str.strip()

    dupe_check = combo.groupby("Branch").size()
    inconsistent = dupe_check[dupe_check > 1]
    if len(inconsistent):
        raise ValueError(
            f"{len(inconsistent)} branch(es) map to more than one zone hierarchy in this workbook - "
            f"resolve before rebuilding: {list(inconsistent.index[:10])}"
        )

    combo.to_csv(out_path, index=False)
    global _map_df, _lookup
    _map_df = None
    _lookup = None
    return combo


if __name__ == "__main__":
    import sys
    if len(sys.argv) >= 3 and sys.argv[1] == "rebuild":
        result = rebuild_from_xlsb(sys.argv[2])
        print(f"Rebuilt {MAP_FILE}: {len(result)} branches mapped.")
    else:
        print(f"Usage: python {sys.argv[0]} rebuild path/to/zone_master.xlsb")
