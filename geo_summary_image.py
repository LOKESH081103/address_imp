"""
geo_summary_image.py - render a state/zone-wise Critical vs Clean breakdown
as a single presentation-ready PNG (stacked horizontal bars, sorted worst
first), so it can be dropped into an email/Slack/slide without opening the
app or Excel.

Pure presentation layer: takes the DataFrame from geo_summary.breakdown_by_group()
and draws it. No analysis logic lives here.
"""

import io

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

CRITICAL_COLOR = "#e74c3c"
CLEAN_COLOR = "#2ecc71"

MAX_BARS = 25  # beyond this, chart gets unreadable - smallest groups get folded into "Other"


def build_geo_breakdown_png(breakdown_df, group_label: str, title: str = None,
                             source_name: str = "") -> bytes:
    """
    breakdown_df: output of geo_summary.breakdown_by_group() - columns
    Group / Total / Critical / Clean / Critical %.
    group_label: what the groups represent, e.g. "State" or "Zone" - used
    in the title and axis.
    """
    if breakdown_df is None or breakdown_df.empty:
        df = breakdown_df
    else:
        df = breakdown_df.sort_values("Critical", ascending=False).reset_index(drop=True)
        if len(df) > MAX_BARS:
            head = df.iloc[:MAX_BARS - 1]
            tail = df.iloc[MAX_BARS - 1:]
            other_total = int(tail["Total"].sum())
            other_critical = int(tail["Critical"].sum())
            other_row = pd.DataFrame([{
                "Group": f"Other ({len(tail)} more)",
                "Total": other_total,
                "Critical": other_critical,
                "Clean": other_total - other_critical,
                "Critical %": round(100 * other_critical / max(other_total, 1), 1),
            }])
            df = pd.concat([head, other_row], ignore_index=True)

    title = title or f"Address Quality by {group_label}"
    n = len(df) if df is not None else 0
    fig_h = max(3.5, 0.42 * n + 1.8)
    fig, ax = plt.subplots(figsize=(11, fig_h), dpi=300)
    fig.patch.set_facecolor("white")

    if n == 0:
        ax.text(0.5, 0.5, "No data", ha="center", va="center", fontsize=14, color="#999")
        ax.axis("off")
    else:
        # worst (highest Critical) at the TOP of the chart
        df = df.iloc[::-1].reset_index(drop=True)
        y = range(n)
        ax.barh(y, df["Critical"], color=CRITICAL_COLOR, label="Critical")
        ax.barh(y, df["Clean"], left=df["Critical"], color=CLEAN_COLOR, label="Clean")

        ax.set_yticks(list(y))
        ax.set_yticklabels(df["Group"], fontsize=10)
        ax.set_xlabel("Number of addresses", fontsize=10, color="#444")
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
        ax.spines["left"].set_visible(False)
        ax.tick_params(axis="y", length=0)
        ax.grid(axis="x", color="#ececec", linewidth=0.8, zorder=0)
        ax.set_axisbelow(True)

        max_total = df["Total"].max()
        for i, row in df.iterrows():
            ax.text(row["Total"] + max_total * 0.01, i, f"{int(row['Total']):,} ({row['Critical %']:.0f}% critical)",
                     va="center", fontsize=8.5, color="#333")

        ax.set_xlim(0, max_total * 1.22)
        ax.legend(loc="lower right", frameon=False, fontsize=10, ncol=2)

    subtitle = f"{n} {group_label.lower()}(s)"
    if source_name:
        subtitle += f"  •  {source_name}"
    fig.suptitle(title, fontsize=16, fontweight="bold", color="#1a1a1a", y=0.99 if n else 0.6)
    fig.text(0.5, 0.955 if n else 0.5, subtitle, ha="center", fontsize=10, color="#666666")

    fig.tight_layout(rect=[0, 0, 1, 0.94] if n else [0, 0, 1, 1])

    buf = io.BytesIO()
    fig.savefig(buf, format="png", facecolor="white", bbox_inches="tight")
    plt.close(fig)
    buf.seek(0)
    return buf.getvalue()
