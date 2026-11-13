"""Review figures regenerated from the extraction workbook (npj style)."""
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

WB = sys.argv[1]
OUT = sys.argv[2]
HEADLINE = sys.argv[3]

plt.rcParams.update({
    "font.family": "Arial", "font.size": 7.5, "axes.titlesize": 7.5,
    "axes.labelsize": 7, "xtick.labelsize": 6.5, "ytick.labelsize": 6.5,
    "legend.fontsize": 6.5, "axes.linewidth": 1.0, "xtick.major.width": 1.0,
    "ytick.major.width": 1.0, "axes.spines.top": False, "axes.spines.right": False,
    "pdf.fonttype": 42, "savefig.dpi": 600,
})
INK, MUTED, GRID = "#0b0b0b", "#52514e", "#e4e3df"
WS, SI, EXT, NR = "#D55E00", "#0072B2", "#CC79A7", "#BBBBBB"
GOOD, MID, BAD = "#0072B2", "#BBBBBB", "#D55E00"
TIERS = [("Within-subject or record-wise", "Within-subject", WS), ("Subject-independent", "Subject-independent", SI),
         ("External or cross-dataset", "External", EXT), ("Not reported", "Not reported", NR)]
MM = 1 / 25.4

a = pd.read_excel(WB, sheet_name="05_INCLUDED_DATA", header=1)
a["Year"] = a["Year"].astype(int)


def label(ax, txt):
    ax.text(-0.02, 1.06, txt, transform=ax.transAxes, fontweight="bold", fontsize=9, va="bottom", ha="right")


def stacked_h(ax, rows, cats, colors, title):
    y = np.arange(len(rows))[::-1]
    for (name, counts), yy in zip(rows, y):
        left = 0
        for c, col in zip(cats, colors):
            v = counts.get(c, 0)
            if v:
                ax.barh(yy, v, left=left, color=col, height=0.62, edgecolor="white", linewidth=1)
                if v >= 3:
                    ax.text(left + v / 2, yy, str(v), ha="center", va="center", fontsize=6.5,
                            color="white" if col != MID else INK)
                left += v
    ax.set_yticks(y, [r[0] for r in rows])
    ax.set_xlim(0, 83)
    ax.set_xticks([0, 20, 40, 60, 83])
    ax.set_xlabel("Studies (n = 83)")
    ax.set_title(title, loc="left", fontweight="bold", pad=13)
    ax.tick_params(axis="y", length=0)
    ax.legend(handles=[plt.Rectangle((0, 0), 1, 1, color=c) for c in colors], labels=cats, frameon=False, ncol=3,
              loc="lower left", bbox_to_anchor=(-0.01, 0.99), handlelength=1, borderaxespad=0.2)


# ---------------------------------------------------------------- Figure: RQ1
fig = plt.figure(figsize=(180 * MM, 70 * MM))
gs = fig.add_gridspec(2, 2, width_ratios=[1.05, 1], hspace=0.95, wspace=0.55)
ax = fig.add_subplot(gs[:, 0])
years = range(2018, 2027)
bottom = np.zeros(len(years))
for key, lab, col in TIERS:
    v = np.array([((a.Year == y) & (a["Strictest tier"] == key)).sum() for y in years])
    ax.bar(list(years), v, bottom=bottom, color=col, width=0.72, edgecolor="white", linewidth=1, label=lab)
    for x, b, h in zip(years, bottom, v):
        if h >= 2:
            ax.text(x, b + h / 2, str(h), ha="center", va="center", fontsize=6.5, color="white" if col != NR else INK)
    bottom += v
for x, t in zip(years, bottom):
    ax.text(x, t + 0.3, str(int(t)), ha="center", va="bottom", fontsize=6.5, color=MUTED)
ax.set_xticks(list(years), [str(y) if y < 2026 else "2026*" for y in years])
ax.set_ylabel("Included studies")
ax.set_ylim(0, 19.5)
ax.set_yticks(range(0, 17, 4))
ax.set_title("Strictest validation tier by year", loc="left", fontweight="bold")
ax.legend(frameon=False, loc="upper left", ncol=2, handlelength=1, columnspacing=0.8, borderaxespad=0)
ax.text(1, -0.16, "*January to 25 September 2026", transform=ax.transAxes, ha="right", fontsize=6.5, color=MUTED)
label(ax, "a")

ax = fig.add_subplot(gs[0, 1])
rob = [("Participants", "D1 Participants"), ("Predictors", "D2 Predictors"), ("Outcome", "D3 Outcome"),
       ("Analysis", "D4 Analysis"), ("Overall", "Overall RoB")]
stacked_h(ax, [(n, a[c].value_counts().to_dict()) for n, c in rob], ["Low", "Unclear", "High"],
          [GOOD, MID, BAD], "Risk of bias (PROBAST+AI)")
label(ax, "b")
ax.texts[-1].set_position((-0.02, 1.2))

ax = fig.add_subplot(gs[1, 1])
leak = [("L1 window overlap", "L1 Window split at random"), ("L2 preprocessing", "L2 Normalised on all data"),
        ("L3 test-data tuning", "L3 Tuned on test data"), ("L4 participant overlap", "L4 Same person in train & test")]
stacked_h(ax, [(n, a[c].value_counts().to_dict()) for n, c in leak], ["Absent", "Unclear", "Present"],
          [GOOD, MID, BAD], "Data-leakage indicators")
label(ax, "c")
ax.texts[-1].set_position((-0.02, 1.2))
fig.savefig(f"{OUT}/fig3_validation_rob_leakage.pdf", bbox_inches="tight")
fig.savefig(f"{OUT}/fig3_validation_rob_leakage.png", bbox_inches="tight", dpi=200)
plt.close(fig)

# ---------------------------------------------------------- Figure: paired
pc = pd.read_excel(WB, sheet_name="07_RQ2_PERFORMANCE", header=None)
start = pc.index[pc[0].astype(str).str.strip() == "#"][0]
pc.columns = pc.iloc[start]
pc = pc.iloc[start + 1:start + 17].copy()
pc["Looser"], pc["Stricter"] = pc["Looser"].astype(float), pc["Stricter"].astype(float)
pc["Change"] = pc["Stricter"] - pc["Looser"]
short = {"Balanced accuracy*": "Bal. acc.", "AUROC": "AUROC", "Accuracy": "Acc.", "F1": "F1",
         "Geometric mean": "GM", "ICC for percent time frozen": "ICC"}
fig, axes = plt.subplots(2, 1, figsize=(120 * MM, 105 * MM), gridspec_kw=dict(height_ratios=[10, 6], hspace=0.55))
for ax, (typ, col, title, lab) in zip(axes, [("WS → SI", SI, "Within-subject or record-wise → subject-independent", "a"),
                                            ("Internal → External", EXT, "Internal → external or cross-dataset", "b")]):
    s = pc[pc["Contrast type"] == typ].sort_values("Change")
    y = np.arange(len(s))[::-1]
    for yy, (_, r) in zip(y, s.iterrows()):
        ax.plot([r.Looser, r.Stricter], [yy, yy], color=GRID, lw=2, zorder=1, solid_capstyle="round")
        ax.scatter(r.Looser, yy, s=22, color="#8a8984", zorder=2, edgecolor="white", linewidth=0.6)
        ax.scatter(r.Stricter, yy, s=22, color=col, zorder=3, edgecolor="white", linewidth=0.6)
        ax.text(1.035, yy, f"{r.Change:+.3f}".replace("-", "−"), va="center", fontsize=6.5, color=INK,
                transform=ax.get_yaxis_transform())
    ax.set_yticks(y, [f"{r.Study} ({short.get(r.Metric, r.Metric)})" for _, r in s.iterrows()])
    ax.set_xlim(0.5, 1.0)
    ax.tick_params(axis="y", length=0)
    ax.grid(axis="x", color=GRID, lw=0.5)
    ax.set_axisbelow(True)
    dec = (s.Change < 0).sum()
    from decimal import Decimal, ROUND_HALF_UP
    med = Decimal(str(round(float(np.median(s.Change)), 6))).quantize(Decimal("0.001"), ROUND_HALF_UP)
    ax.set_title(f"{title}\n{dec} of {len(s)} declined; median change {med:+}".replace("-0", "−0"),
                 loc="left", fontweight="bold", fontsize=7)
    ax.text(1.035, 1.0, "Change", transform=ax.transAxes, fontsize=6.5, color=MUTED, va="bottom")
    label(ax, lab)
axes[1].set_xlabel("Reported performance on each study's own metric")
h = [plt.Line2D([], [], marker="o", ls="", color=c, markersize=4.5) for c in ["#8a8984", SI, EXT]]
axes[1].legend(h, ["Less strict design", "Subject-independent", "External"], frameon=False, ncol=3,
               loc="upper center", bbox_to_anchor=(0.45, -0.32))
fig.savefig(f"{OUT}/fig4_paired_contrasts.pdf", bbox_inches="tight")
fig.savefig(f"{OUT}/fig4_paired_contrasts.png", bbox_inches="tight", dpi=200)
plt.close(fig)

# ------------------------------------------------- Figure: optimism (headline)
h = pd.read_csv(HEADLINE).dropna(subset=["hv"])
h = h.merge(a[["Study_ID", "L1 Window split at random", "L4 Same person in train & test", "Overall RoB"]], on="Study_ID")
rng = np.random.default_rng(3)
fig, axes = plt.subplots(1, 3, figsize=(180 * MM, 62 * MM), gridspec_kw=dict(width_ratios=[1.35, 1, 1], wspace=0.35))


def strip(ax, groups, title, lab):
    for i, (name, vals, col) in enumerate(groups):
        from scipy.stats import gaussian_kde
        vals = np.asarray(vals, float)
        grid = np.linspace(max(0.35, vals.min() - 0.03), min(1.0, vals.max() + 0.02), 200)
        dens = gaussian_kde(vals, bw_method=0.35)(grid)
        dens = dens / dens.max() * 0.32
        ax.fill_betweenx(grid, i - 0.04 - dens, i - 0.04, color=col, alpha=0.28, lw=0, zorder=2)
        q1, med, q3 = np.percentile(vals, [25, 50, 75])
        ax.add_patch(plt.Rectangle((i - 0.035, q1), 0.07, q3 - q1, fc="white", ec=INK, lw=0.7, zorder=4))
        ax.plot([i - 0.035, i + 0.035], [med, med], color=INK, lw=1.4, zorder=5)
        x = i + 0.1 + rng.uniform(0, 0.2, len(vals))
        ax.scatter(x, vals, s=11, color=col, alpha=0.9, edgecolor="white", linewidth=0.4, zorder=3)
        ax.text(i + 0.33, med, f"{med:.3f}", va="center", fontsize=6.5, color=INK)
        hi = (np.asarray(vals) >= 0.95).sum()
        ax.text(i, 1.035, f"≥0.95\n{hi}/{len(vals)} ({100 * hi / len(vals):.0f}%)", ha="center", va="bottom",
                fontsize=6.5, color=MUTED)
    ax.axhline(0.95, color=MUTED, lw=0.7, ls=(0, (3, 2)), zorder=1)
    ax.set_xticks(range(len(groups)), [f"{g[0]}\nn = {len(g[1])}" for g in groups])
    ax.set_xlim(-0.55, len(groups) - 0.35)
    ax.set_ylim(0.35, 1.10)
    ax.set_yticks(np.arange(0.4, 1.01, 0.1))
    ax.grid(axis="y", color=GRID, lw=0.5)
    ax.set_axisbelow(True)
    ax.set_title(title, loc="left", fontweight="bold", pad=16)
    ax.tick_params(axis="x", length=0)
    label(ax, lab)


tier_groups = [(lab.replace("Subject-independent", "Subject-\nindependent").replace("Within-subject", "Within-\nsubject"),
                h[h["Strictest tier"] == k].hv.values, c) for k, lab, c in TIERS[:3]]
strip(axes[0], tier_groups, "By strictest validation tier", "a")
axes[0].set_ylabel("Reported headline performance")
strip(axes[1], [("Absent", h[h["L1 Window split at random"] == "Absent"].hv.values, GOOD),
                ("Present", h[h["L1 Window split at random"] == "Present"].hv.values, BAD)],
      "Window overlap (L1)", "b")
strip(axes[2], [("Absent", h[h["L4 Same person in train & test"] == "Absent"].hv.values, GOOD),
                ("Present", h[h["L4 Same person in train & test"] == "Present"].hv.values, BAD)],
      "Participant overlap (L4)", "c")
fig.savefig(f"{OUT}/fig5_reported_performance.pdf", bbox_inches="tight")
fig.savefig(f"{OUT}/fig5_reported_performance.png", bbox_inches="tight", dpi=200)
plt.close(fig)

# ------------------------------------------------------ Figure: shift gap map
shifts = [("Laboratory → home", "Lab → home"), ("Medication state", "Medication state"), ("Task protocol", "Task protocol"),
          ("Sensor placement", "Sensor placement"), ("Device or sampling rate", "Device / sampling rate"),
          ("Label definition", "Shift: label definition"), ("Missing modality", "Missing modality"),
          ("Sensor noise or failure", "Shift: sensor noise or failure"), ("Sensor orientation", "Sensor orientation"),
          ("Pose-estimation failure", "Pose-estimation failure"), ("Camera viewpoint", "Camera viewpoint")]
strats = [("Personalisation or fine-tuning", "Fine-tune / personalise"), ("Signal or rotation augmentation", "Signal / rotation augmentation"),
          ("Multi-dataset training", "Multi-dataset training"), ("Self-supervised pre-training", "Self-supervised pretraining"),
          ("Invariant representation", "Invariant representation"), ("Reliability-aware fusion", "Reliability-weighted fusion"),
          ("Other", "Other strategy")]
fig, axes = plt.subplots(2, 1, figsize=(120 * MM, 100 * MM), gridspec_kw=dict(height_ratios=[11, 7], hspace=0.5))
for ax, items, title, lab, none_n in [(axes[0], shifts, "Acquisition shifts named by the authors", "a",
                                       (a["Shifts reported (count, auto)"].astype(int) == 0).sum()),
                                      (axes[1], strats, "Robustness strategies applied", "b",
                                       (a["Any strategy? (auto)"] == "No").sum())]:
    y = np.arange(len(items))[::-1]
    for (name, col), yy in zip(items, y):
        m = a[col].astype(int) == 1
        left = 0
        for key, tl, c in TIERS:
            v = (m & (a["Strictest tier"] == key)).sum()
            if v:
                ax.barh(yy, v, left=left, color=c, height=0.62, edgecolor="white", linewidth=1)
                left += v
        ax.text(left + 0.4, yy, str(int(m.sum())), va="center", fontsize=6.5, color=INK)
    ax.set_yticks(y, [i[0] for i in items])
    ax.tick_params(axis="y", length=0)
    ax.set_xlim(0, 24)
    ax.grid(axis="x", color=GRID, lw=0.5)
    ax.set_axisbelow(True)
    verb = "named" if lab == "a" else "applied"
    ax.set_title(f"{title} ({none_n} of 83 studies {verb} none)", loc="left", fontweight="bold")
    label(ax, lab)
axes[1].set_xlabel("Studies, coloured by strictest validation tier")
axes[1].legend(handles=[plt.Rectangle((0, 0), 1, 1, color=c) for _, _, c in TIERS], labels=[t for _, t, _ in TIERS],
               frameon=False, ncol=4, loc="upper center", bbox_to_anchor=(0.4, -0.35), handlelength=1)
fig.savefig(f"{OUT}/fig6_acquisition_shift.pdf", bbox_inches="tight")
fig.savefig(f"{OUT}/fig6_acquisition_shift.png", bbox_inches="tight", dpi=200)
plt.close(fig)
print("done")
