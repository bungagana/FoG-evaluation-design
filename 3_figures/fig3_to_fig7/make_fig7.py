"""Figure 7: controlled leakage experiment on Daphnet (reads results/final_*.csv)."""
import os
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

RES = sys.argv[1] if len(sys.argv) > 1 else "results"
OUT = sys.argv[2] if len(sys.argv) > 2 else "figures_out"
MM = 1 / 25.4
plt.rcParams.update({
    "font.family": "Arial", "font.size": 7.5, "axes.titlesize": 7.5, "axes.labelsize": 7,
    "xtick.labelsize": 6.5, "ytick.labelsize": 6.5, "legend.fontsize": 6.5, "axes.linewidth": 1.0,
    "xtick.major.width": 1.0, "ytick.major.width": 1.0, "xtick.major.size": 2.5, "ytick.major.size": 2.5,
    "axes.spines.top": False, "axes.spines.right": False, "pdf.fonttype": 42, "ps.fonttype": 42,
    "svg.fonttype": "none",
})
INK, MUTED, GREY = "#0b0b0b", "#52514e", "#8a8984"
MODELS = [("lr", "Logistic regression", "#0072B2", "o"), ("rf", "Random forest", "#D55E00", "s"),
          ("cnn", "CNN", "#CC79A7", "D")]
GROUPS = [("Leakage (inflation)", [
    ("D1_random_overlap", "Random window split (L1 + L4)"),
    ("D2_random_purged", "Random split, overlap removed (L4)"),
    ("D3_within_subject_blocks", "Within-subject chronological blocks (L4)"),
    ("D5_loso_norm_all", "Normalisation fitted on all data (L2)"),
    ("D6_loso_select_all", "Feature selection on all data (L2)†"),
    ("D8_loso_hparam_test", "Hyperparameters tuned on test (L3)")]),
    ("Acquisition shift", [
        ("S1_placement_thigh", "Tested on thigh sensor (placement)"),
        ("S2_rotation_45", "Test signals rotated 45°"),
        ("S3_rotation_90", "Test signals rotated 90°")])]

D = pd.read_csv(os.path.join(RES, "final_deltas.csv"))
S = pd.read_csv(os.path.join(RES, "final_summary.csv"))
D = D[D.contrast == "primary"]
present = [m for m in MODELS if m[0] in set(S.model)]

fig = plt.figure(figsize=(180 * MM, 74 * MM))
axa = fig.add_axes([0.262, 0.115, 0.468, 0.80])
axb = fig.add_axes([0.825, 0.235, 0.15, 0.68])

# ---------------------------------------------------------------- panel a
ypos, labels, y = [], [], 0.0
heads = []
for g, rows in GROUPS:
    heads.append((g, y))
    y -= 0.85
    for key, lab in rows:
        ypos.append((key, y))
        labels.append(lab)
        y -= 1.0
    y -= 0.35
off = {m[0]: o for m, o in zip(present, np.linspace(0.22, -0.22, len(present)) if len(present) > 1 else [0])}
for key, yy in ypos:
    for kind, name, col, mk in present:
        r = D[(D.model == kind) & (D.design == key)]
        if r.empty:
            continue
        r = r.iloc[0]
        x, lo, hi = r.delta_auroc_pooled, r.delta_auroc_pooled_ci_lo, r.delta_auroc_pooled_ci_hi
        axa.plot([lo, hi], [yy + off[kind]] * 2, color=col, lw=0.9, solid_capstyle="butt", zorder=2)
        axa.plot(x, yy + off[kind], marker=mk, ms=3.6, color=col, mec="white", mew=0.4, ls="none", zorder=3)
axa.axvline(0, color=GREY, lw=0.7, ls=(0, (3, 2)), zorder=1)
axa.set_yticks([p for _, p in ypos], labels)
axa.tick_params(axis="y", length=0, pad=3)
axa.set_ylim(y + 0.55, 0.45)
lo_all = min(D.delta_auroc_pooled_ci_lo.min(), -0.05)
hi_all = max(D.delta_auroc_pooled_ci_hi.max(), 0.05)
axa.set_xlim(np.floor(lo_all * 20) / 20 - 0.01, np.ceil(hi_all * 20) / 20 + 0.005)
axa.set_xlabel("Δ pooled window AUROC vs. leakage-free reference (95% CI)")
for g, yy in heads:
    axa.text(-0.008, yy - 0.1, g, transform=axa.get_yaxis_transform(), ha="right", va="center",
             fontweight="bold", fontsize=7, color=INK)
axa.spines["left"].set_visible(False)
xt = axa.get_xticks()
axa.set_xticks(xt[(xt >= axa.get_xlim()[0]) & (xt <= axa.get_xlim()[1])])
axa.xaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(lambda v, _: f"{v:+.2f}" if abs(v) > 1e-9 else "0"))
axa.annotate("← lower", xy=(0, 1.0), xycoords=("data", "axes fraction"), xytext=(-3, 2),
             textcoords="offset points", ha="right", va="bottom", fontsize=6.5, color=MUTED)
axa.annotate("higher (inflated) →", xy=(0, 1.0), xycoords=("data", "axes fraction"), xytext=(3, 2),
             textcoords="offset points", ha="left", va="bottom", fontsize=6.5, color=MUTED)
handles = [plt.Line2D([], [], color=c, marker=mk, ms=3.6, mec="white", mew=0.4, lw=0.9, label=n)
           for _, n, c, mk in present]
axa.legend(handles=handles, frameon=False, loc="upper left", bbox_to_anchor=(0.0, 0.97), handlelength=1.6,
           borderaxespad=0.2, labelspacing=0.3)
fig.text(0.008, 0.955, "a", fontweight="bold", fontsize=7.5, va="bottom")

# ---------------------------------------------------------------- panel b
xs = np.arange(len(present))
for i, (kind, name, col, mk) in enumerate(present):
    vals = []
    for j, (des, face) in enumerate([("D4_loso_clean", "white"), ("D7_loso_threshold_test", col)]):
        r = S[(S.model == kind) & (S.design == des)].iloc[0]
        xx = i + (j - 0.5) * 0.36
        axb.plot([xx, xx], [r.balanced_accuracy_ci_lo, r.balanced_accuracy_ci_hi], color=col, lw=0.9, zorder=2)
        axb.plot(xx, r.balanced_accuracy, marker=mk, ms=3.8, mfc=face, mec=col, mew=0.9, ls="none", zorder=3)
        vals.append((xx, r.balanced_accuracy))
    axb.plot([vals[0][0], vals[1][0]], [vals[0][1], vals[1][1]], color=col, lw=0.6, zorder=1)
    dr = D[(D.model == kind) & (D.design == "D7_loso_threshold_test")].iloc[0]
    axb.text(i, 0.955, f"{dr.delta_balanced_accuracy:+.2f}", ha="center", va="bottom", fontsize=6.5, color=col)
axb.set_xticks(xs, [{"lr": "LR", "rf": "RF", "cnn": "CNN"}[m[0]] for m in present])
axb.set_xlim(-0.6, len(present) - 0.4)
axb.set_ylim(0.6, 1.0)
axb.set_yticks([0.6, 0.7, 0.8, 0.9, 1.0])
axb.set_ylabel("Balanced accuracy (95% CI)")
axb.text(0.5, 1.035, "Δ (test − training threshold)", transform=axb.transAxes, ha="center", va="bottom", fontsize=6.5,
         color=MUTED)
hb = [plt.Line2D([], [], marker="o", ms=3.8, mfc="white", mec=GREY, mew=0.9, ls="none",
                 label="Threshold from training data"),
      plt.Line2D([], [], marker="o", ms=3.8, mfc=GREY, mec=GREY, mew=0.9, ls="none",
                 label="Threshold tuned on test participant")]
axb.legend(handles=hb, frameon=False, loc="upper left", bbox_to_anchor=(-0.55, -0.09), fontsize=6.5,
           handletextpad=0.3, borderaxespad=0, labelspacing=0.25)
fig.text(0.765, 0.955, "b", fontweight="bold", fontsize=7.5, va="bottom")

os.makedirs(OUT, exist_ok=True)
fig.savefig(os.path.join(OUT, "fig7_experiment.pdf"))
fig.savefig(os.path.join(OUT, "fig7_experiment.png"), dpi=300)
print("saved", OUT)
