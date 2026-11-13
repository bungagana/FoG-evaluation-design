"""Final evaluation of the controlled leakage experiment.

Design decisions:
  * Every statistic is the mean over seeds of the per-seed metric, both for the
    point estimate and inside the bootstrap, so point estimates and CIs refer to
    the same estimand.
  * Paired subject-level cluster bootstrap: the 10 participants are resampled with
    replacement (one draw shared by all models/designs/seeds, so contrasts are
    paired); on each resample every seed's metric is recomputed for the design
    and its reference, averaged over seeds, and differenced.
    Pooled AUROC on a resample is computed exactly from a 10x10 matrix of
    between-subject concordance counts (duplicated subjects = integer weights).
  * Correct references: D4 for all designs except D6 (reference D6r).
  * D8 correction: run_experiment.py selects grid[0] / CNN epoch 1 for the two
    participants without FoG (test AUROC undefined); the intended behaviour is the
    default configuration, i.e. the D4 scores. 'D8_loso_hparam_test' below is the
    corrected version; the as-run scores are reported as 'D8_asrun'.
  * Event metrics: positive windows are merged into one alarm only if they are
    contiguous in time.
    False alarms per hour use the non-FoG time actually covered by analysed windows.
  * Paired per-subject test: Wilcoxon signed-rank (two-sided, exact) on per-subject
    AUROC averaged over seeds (n = 8 participants with FoG); for D7, whose AUROC is
    identical to D4 by construction, the test uses per-subject balanced accuracy.
    Holm adjustment across the primary contrasts within each model.

Usage: python evaluate_final.py --cache cache --res results [--boot 5000]
"""
import argparse
import glob
import os
import re

import warnings

import numpy as np
import pandas as pd
from scipy.stats import wilcoxon

from prepare import FS, WIN
from run_experiment import DESIGNS, load

REFS = {k: "D4_loso_clean" for k in DESIGNS if k != "D4_loso_clean"}
REFS["D6_loso_select_all"] = "D6r_loso_select_train"
REFS.pop("D6r_loso_select_train")
REFS["D8_asrun"] = "D4_loso_clean"
PRIMARY = ["D1_random_overlap", "D2_random_purged", "D3_within_subject_blocks", "D5_loso_norm_all",
           "D6_loso_select_all", "D7_loso_threshold_test", "D8_loso_hparam_test",
           "S1_placement_thigh", "S2_rotation_45", "S3_rotation_90"]
# Secondary (not Holm-adjusted) contrasts that isolate single mechanisms.
SECONDARY = {"D1_random_overlap": "D2_random_purged",       # L1: overlapping windows
             "D2_random_purged": "D3_within_subject_blocks"}  # random vs chronological within-subject
METRICS = ["auroc_pooled", "auroc_subject_mean", "balanced_accuracy", "f1", "sensitivity",
           "specificity", "precision", "episode_sensitivity", "false_alarms_per_h"]


# ----------------------------------------------------------------------------
# Per-subject sufficient statistics for one score vector
# ----------------------------------------------------------------------------


def subject_stats(d, s, thr, episodes, subs):
    """Return dict of per-subject arrays from which every metric (and every
    subject-bootstrap resample of it) can be computed exactly."""
    y, sub = d["y"], d["subject"]
    K = len(subs)
    pos = [np.sort(s[(sub == u) & (y == 1)]) for u in subs]
    neg = [np.sort(s[(sub == u) & (y == 0)]) for u in subs]
    A = np.zeros((K, K))  # A[i, j]: concordant pairs (pos of i, neg of j), ties = 0.5
    for i in range(K):
        if len(pos[i]) == 0:
            continue
        for j in range(K):
            lo = np.searchsorted(neg[j], pos[i], "left")
            hi = np.searchsorted(neg[j], pos[i], "right")
            A[i, j] = lo.sum() + 0.5 * (hi - lo).sum()
    P = np.array([len(p) for p in pos], float)
    N = np.array([len(n) for n in neg], float)
    pred = s >= thr
    st = {"A": A, "P": P, "N": N}
    for name, m in [("tp", pred & (y == 1)), ("fp", pred & (y == 0)),
                    ("fn", ~pred & (y == 1)), ("tn", ~pred & (y == 0))]:
        st[name] = np.array([m[sub == u].sum() for u in subs], float)
    det, tot, fa, nonfog = (np.zeros(K) for _ in range(4))
    for run in np.unique(d["run"]):
        k = subs.index(run[:3])
        m = np.where(d["run"] == run)[0]
        order = m[np.argsort(d["start"][m])]
        a0, b0, p = d["start"][order], d["end"][order], pred[order]
        eps = [(a, b) for (_, r, a, b) in episodes if r == run]
        tot[k] += len(eps)
        for a, b in eps:
            det[k] += bool(np.any(p & (a0 < b) & (b0 > a)))
        # alarms = maximal runs of consecutive positive decisions (windows that overlap in
        # time); runs are NOT merged across annotation gaps or across a negative decision
        cur = None
        alarms = []
        for i in np.where(p)[0]:
            if cur is not None and a0[i] < cur[1]:  # overlapping = consecutive decisions
                cur[1] = b0[i]
            else:
                if cur is not None:
                    alarms.append(cur)
                cur = [a0[i], b0[i]]
        if cur is not None:
            alarms.append(cur)
        fa[k] += sum(not any(x < b and y_ > a for a, b in eps) for x, y_ in alarms)
        # non-FoG time covered by analysed windows
        L = int(b0.max())
        cov = np.zeros(L, bool)
        for a, b in zip(a0, b0):
            cov[a:b] = True
        for a, b in eps:
            cov[int(a):int(b)] = False
        nonfog[k] += cov.sum() / FS / 3600
    st.update(det=det, tot=tot, fa=fa, nonfog_h=nonfog)
    return st


def metrics_from_stats(st, C):
    """Metrics for count vectors C (shape (B, K)); C = ones gives the full data."""
    C = np.atleast_2d(C).astype(float)
    with np.errstate(invalid="ignore", divide="ignore"):
        Pc, Nc = C @ st["P"], C @ st["N"]
        auc = np.einsum("bi,ij,bj->b", C, st["A"], C) / (Pc * Nc)
        has = st["P"] > 0
        auc_s = np.where(has, np.diag(st["A"]) / np.maximum(st["P"] * st["N"], 1), 0.0)
        auc_sub = (C @ auc_s) / (C @ has.astype(float))
        tp, fp, fn, tn = (C @ st[k] for k in ["tp", "fp", "fn", "tn"])
        sens, spec = tp / (tp + fn), tn / (tn + fp)
        prec = np.where(tp + fp > 0, tp / (tp + fp), 0.0)
        f1 = np.where(prec + sens > 0, 2 * prec * sens / (prec + sens), 0.0)
        ev = (C @ st["det"]) / (C @ st["tot"])
        fah = (C @ st["fa"]) / (C @ st["nonfog_h"])
    return dict(auroc_pooled=auc, auroc_subject_mean=auc_sub, balanced_accuracy=(sens + spec) / 2,
                f1=f1, sensitivity=sens, specificity=spec, precision=prec,
                episode_sensitivity=ev, false_alarms_per_h=fah)


def per_subject(st):
    """Per-subject AUROC and balanced accuracy (NaN for subjects without FoG)."""
    has = st["P"] > 0
    with np.errstate(invalid="ignore", divide="ignore"):
        auc = np.where(has, np.diag(st["A"]) / (st["P"] * st["N"]), np.nan)
        ba = np.where(has, (st["tp"] / (st["tp"] + st["fn"]) + st["tn"] / (st["tn"] + st["fp"])) / 2, np.nan)
    return auc, ba


def holm(p):
    p = np.asarray(p, float)
    out = np.full_like(p, np.nan)
    ok = ~np.isnan(p)
    pv = p[ok]
    order = np.argsort(pv)
    m = len(pv)
    adj = np.empty(m)
    run = 0.0
    for r, i in enumerate(order):
        run = max(run, (m - r) * pv[i])
        adj[i] = min(1.0, run)
    out[ok] = adj
    return out


def wilcox(a, b):
    diff = a - b
    diff = diff[~np.isnan(diff)]
    if len(diff) == 0 or np.allclose(diff, 0):
        return np.nan, 1.0
    has_zero = np.any(np.isclose(diff, 0))
    r = wilcoxon(diff, alternative="two-sided", zero_method="wilcox",
                 method="approx" if has_zero else "exact")
    return float(r.statistic), float(r.pvalue)


# ----------------------------------------------------------------------------


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--cache", default="cache")
    ap.add_argument("--res", default="results")
    ap.add_argument("--boot", type=int, default=5000)
    ap.add_argument("--seed", type=int, default=20261024)
    a = ap.parse_args()
    warnings.filterwarnings("ignore", "Mean of empty slice")
    d = load(a.cache)
    episodes = np.load(os.path.join(a.cache, "episodes.npy"), allow_pickle=True)
    subs = sorted(map(str, np.unique(d["subject"])))
    K = len(subs)
    fog_subs = [u for u in subs if d["y"][d["subject"] == u].any()]

    runs = {}
    for f in sorted(glob.glob(os.path.join(a.res, "scores_*_seed*.npz"))):
        kind, seed = re.match(r".*scores_(\w+?)_seed(\d+)\.npz", f).groups()
        runs.setdefault(kind, {})[int(seed)] = np.load(f)
    order = [m for m in ["lr", "rf", "cnn"] if m in runs]

    rng = np.random.default_rng(a.seed)
    Cb = rng.multinomial(K, np.ones(K) / K, size=a.boot)  # shared, paired resamples
    ones = np.ones((1, K))
    sub_idx = {u: d["subject"] == u for u in subs}

    stats = {}  # (model, design) -> list over seeds of subject stats
    for kind in order:
        for seed, z in sorted(runs[kind].items()):
            for name in list(DESIGNS) + ["D8_asrun"]:
                key = "D8_loso_hparam_test" if name == "D8_asrun" else name
                s = z[f"score__{key}"].copy()
                t = z[f"thr__{key}"]
                if np.isnan(s).all():
                    continue
                if name == "D8_loso_hparam_test":
                    # intended behaviour: default configuration where test AUROC is undefined
                    ref = z["score__D4_loso_clean"]
                    for u in subs:
                        if u not in fog_subs:
                            s[sub_idx[u]] = ref[sub_idx[u]]
                stats.setdefault((kind, name), []).append(stats_for(d, s, t, episodes, subs))

    summary, deltas, subj_rows = [], [], []
    boot_cache = {}

    def seed_avg_boot(kind, name):
        if (kind, name) not in boot_cache:
            boot_cache[(kind, name)] = {m: np.mean([metrics_from_stats(st, Cb)[m] for st in stats[(kind, name)]], axis=0)
                                        for m in METRICS}
        return boot_cache[(kind, name)]

    for kind in order:
        for name in list(DESIGNS) + ["D8_asrun"]:
            if (kind, name) not in stats:
                continue
            sts = stats[(kind, name)]
            per_seed = [metrics_from_stats(st, ones) for st in sts]
            bt = seed_avg_boot(kind, name)
            row = dict(model=kind, design=name, n_seeds=len(sts))
            for m in METRICS:
                v = np.array([ps[m][0] for ps in per_seed])
                row[m] = v.mean()
                row[m + "_sd"] = v.std(ddof=1) if len(v) > 1 else np.nan
                ok = ~np.isnan(bt[m])
                row[m + "_ci_lo"], row[m + "_ci_hi"] = np.percentile(bt[m][ok], [2.5, 97.5])
            aucs = np.array([per_subject(st)[0] for st in sts])
            row["auroc_subject_sd_between"] = np.nanmean(np.nanstd(aucs, axis=1))
            summary.append(row)
            for si, st in enumerate(sts):
                auc, ba = per_subject(st)
                for k, u in enumerate(subs):
                    subj_rows.append(dict(model=kind, design=name, seed_index=si, subject=u,
                                          auroc=auc[k], balanced_accuracy=ba[k]))

        # contrasts
        for name, ref in list(REFS.items()) + [(k, v) for k, v in SECONDARY.items()]:
            if (kind, name) not in stats or (kind, ref) not in stats:
                continue
            secondary = (name, ref) in SECONDARY.items()
            sa, sr = stats[(kind, name)], stats[(kind, ref)]
            n = min(len(sa), len(sr))
            ba_, br_ = seed_avg_boot(kind, name), seed_avg_boot(kind, ref)
            row = dict(model=kind, design=name, reference=ref, n_seeds=n,
                       contrast="secondary" if secondary else ("primary" if name in PRIMARY else "sensitivity"))
            for m in METRICS:
                full = [metrics_from_stats(sa[i], ones)[m][0] - metrics_from_stats(sr[i], ones)[m][0] for i in range(n)]
                db = ba_[m] - br_[m]
                ok = ~np.isnan(db)
                row["delta_" + m] = np.mean(full)
                row["delta_" + m + "_seed_sd"] = np.std(full, ddof=1) if n > 1 else np.nan
                row["delta_" + m + "_ci_lo"], row["delta_" + m + "_ci_hi"] = np.percentile(db[ok], [2.5, 97.5])
            # paired per-subject test (seed-averaged per-subject values, FoG subjects only)
            use_ba = name == "D7_loso_threshold_test"
            j = 1 if use_ba else 0
            va = np.nanmean([per_subject(st)[j] for st in sa[:n]], axis=0)
            vr = np.nanmean([per_subject(st)[j] for st in sr[:n]], axis=0)
            fog = ~np.isnan(va)
            W, p = wilcox(va[fog], vr[fog])
            row.update(wilcoxon_metric="per-subject balanced accuracy" if use_ba else "per-subject AUROC",
                       wilcoxon_n=int(fog.sum()), wilcoxon_W=W, wilcoxon_p=p,
                       n_subjects_improved=int((va[fog] - vr[fog] > 1e-12).sum()),
                       n_subjects_worse=int((va[fog] - vr[fog] < -1e-12).sum()),
                       n_boot_valid=int((~np.isnan(ba_["auroc_pooled"] - br_["auroc_pooled"])).sum()))
            deltas.append(row)

    S = pd.DataFrame(summary)
    D = pd.DataFrame(deltas)
    D["wilcoxon_p_holm"] = np.nan
    for kind in order:
        m = (D.model == kind) & (D.contrast == "primary")
        D.loc[m, "wilcoxon_p_holm"] = holm(D.loc[m, "wilcoxon_p"].values)
    S.to_csv(os.path.join(a.res, "final_summary.csv"), index=False)
    D.to_csv(os.path.join(a.res, "final_deltas.csv"), index=False)
    pd.DataFrame(subj_rows).to_csv(os.path.join(a.res, "final_per_subject.csv"), index=False)

    pd.set_option("display.width", 250)
    pd.set_option("display.max_columns", 30)
    print(f"bootstrap resamples: {a.boot}; models: {', '.join(f'{k} ({len(runs[k])} seeds)' for k in order)}")
    print(S[["model", "design", "n_seeds", "auroc_pooled", "auroc_pooled_sd", "auroc_pooled_ci_lo", "auroc_pooled_ci_hi",
             "auroc_subject_mean", "balanced_accuracy", "f1", "sensitivity", "specificity",
             "episode_sensitivity", "false_alarms_per_h"]].round(3).to_string())
    print(D[["model", "design", "reference", "contrast", "delta_auroc_pooled", "delta_auroc_pooled_ci_lo",
             "delta_auroc_pooled_ci_hi", "delta_auroc_subject_mean", "delta_balanced_accuracy",
             "delta_balanced_accuracy_ci_lo", "delta_balanced_accuracy_ci_hi", "wilcoxon_metric", "wilcoxon_p",
             "wilcoxon_p_holm"]].round(4).to_string())


stats_for = subject_stats

if __name__ == "__main__":
    main()
