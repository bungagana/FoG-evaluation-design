"""Controlled leakage ablation on the Daphnet FoG dataset.

The same windows, features, and models are evaluated under evaluation designs
that differ in a single leakage mechanism (L1-L4) or acquisition condition.
Every design yields exactly one out-of-fold score per window, so all designs
are compared on identical data.
"""
import argparse
import json
import os
import time

import numpy as np
import pandas as pd
import torch
import torch.nn as nn
from sklearn.ensemble import RandomForestClassifier
from sklearn.feature_selection import SelectKBest, f_classif
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score, roc_curve
from sklearn.model_selection import KFold

from prepare import FS, WIN, features

torch.set_num_threads(4)

# ----------------------------------------------------------------------------
# Data
# ----------------------------------------------------------------------------


def load(cache):
    z = np.load(os.path.join(cache, "windows_ov50.npz"))
    d = {k: z[k] for k in z.files}
    d["end"] = d["start"] + WIN
    return d


def rotation(deg, rng):
    """Rotation by `deg` degrees about a random unit axis (Rodrigues)."""
    axis = rng.normal(size=3)
    axis /= np.linalg.norm(axis)
    t = np.deg2rad(deg)
    k = np.array([[0, -axis[2], axis[1]], [axis[2], 0, -axis[0]], [-axis[1], axis[0], 0]])
    return np.eye(3) + np.sin(t) * k + (1 - np.cos(t)) * k @ k


# ----------------------------------------------------------------------------
# Partitions
# ----------------------------------------------------------------------------


def purge(train, test, d):
    """Drop training windows that overlap a test window of the same run."""
    keep = np.ones(len(train), bool)
    for run in np.unique(d["run"][test]):
        te = test[d["run"][test] == run]
        tr_m = d["run"][train] == run
        if not tr_m.any():
            continue
        s_te, e_te = d["start"][te], d["end"][te]
        s_tr, e_tr = d["start"][train[tr_m]], d["end"][train[tr_m]]
        order = np.argsort(s_te)
        s_te, e_te = s_te[order], e_te[order]
        # overlap if any test window starts before the training window ends and ends after it starts
        idx = np.searchsorted(s_te, e_tr, side="left")
        ov = np.zeros(len(s_tr), bool)
        for j in range(len(s_tr)):
            lo = np.searchsorted(e_te, s_tr[j], side="right")
            ov[j] = lo < idx[j]
        keep[np.where(tr_m)[0][ov]] = False
    return train[keep]


def random_folds(d, seed, purge_overlap):
    kf = KFold(5, shuffle=True, random_state=seed)
    idx = np.arange(len(d["y"]))
    for tr, te in kf.split(idx):
        yield (purge(tr, te, d) if purge_overlap else tr), te


def block_folds(d):
    """Within-subject chronological split: block k of every run is tested."""
    blk = np.zeros(len(d["y"]), int)
    for run in np.unique(d["run"]):
        m = np.where(d["run"] == run)[0]
        order = m[np.argsort(d["start"][m])]
        blk[order] = np.minimum(np.arange(len(order)) * 5 // len(order), 4)
    for k in range(5):
        te = np.where(blk == k)[0]
        tr = np.where(blk != k)[0]
        yield purge(tr, te, d), te


def loso_folds(d):
    for s in np.unique(d["subject"]):
        yield np.where(d["subject"] != s)[0], np.where(d["subject"] == s)[0]


# ----------------------------------------------------------------------------
# Models
# ----------------------------------------------------------------------------


class CNN(nn.Module):
    def __init__(self):
        super().__init__()
        self.net = nn.Sequential(
            nn.Conv1d(3, 32, 7, padding=3), nn.BatchNorm1d(32), nn.ReLU(), nn.MaxPool1d(2),
            nn.Conv1d(32, 64, 5, padding=2), nn.BatchNorm1d(64), nn.ReLU(), nn.MaxPool1d(2),
            nn.Conv1d(64, 64, 5, padding=2), nn.BatchNorm1d(64), nn.ReLU(),
            nn.AdaptiveAvgPool1d(1), nn.Flatten(), nn.Dropout(0.3), nn.Linear(64, 1))

    def forward(self, x):
        return self.net(x).squeeze(1)


CNN_EPOCHS = 15


def cnn_fit(Xtr, ytr, seed, evals=()):
    """Train the CNN; return final model and scores of `evals` after every epoch."""
    torch.manual_seed(seed)
    model = CNN()
    opt = torch.optim.Adam(model.parameters(), 1e-3)
    pw = torch.tensor((1 - ytr.mean()) / max(ytr.mean(), 1e-3))
    lossf = nn.BCEWithLogitsLoss(pos_weight=pw)
    Xt = torch.from_numpy(Xtr)
    yt = torch.from_numpy(ytr.astype(np.float32))
    g = torch.Generator().manual_seed(seed)
    history = []
    for _ in range(CNN_EPOCHS):
        model.train()
        perm = torch.randperm(len(Xt), generator=g)
        for i in range(0, len(Xt), 128):
            b = perm[i:i + 128]
            opt.zero_grad()
            lossf(model(Xt[b]), yt[b]).backward()
            opt.step()
        if evals:
            history.append([cnn_predict(model, e) for e in evals])
    return model, history


def cnn_predict(model, X):
    model.eval()
    with torch.no_grad():
        return torch.sigmoid(torch.cat([model(torch.from_numpy(X[i:i + 1024]))
                                        for i in range(0, len(X), 1024)])).numpy()


RF_GRID = [dict(max_depth=None, min_samples_leaf=1), dict(max_depth=None, min_samples_leaf=5),
           dict(max_depth=12, min_samples_leaf=1), dict(max_depth=6, min_samples_leaf=1),
           dict(max_depth=3, min_samples_leaf=1), dict(max_depth=None, min_samples_leaf=20)]
LR_GRID = [0.001, 0.01, 0.1, 1.0, 10.0, 100.0]
RF_DEFAULT, LR_DEFAULT = RF_GRID[1], 1.0


def tab_model(kind, seed, hp=None):
    if kind == "rf":
        hp = hp or RF_DEFAULT
        return RandomForestClassifier(n_estimators=300, class_weight="balanced_subsample",
                                      n_jobs=4, random_state=seed, **hp)
    return LogisticRegression(C=hp if hp is not None else LR_DEFAULT, class_weight="balanced",
                              max_iter=2000)


def zstats(X):
    axes = (0, 2) if X.ndim == 3 else 0
    mu = X.mean(axis=axes, keepdims=X.ndim == 3)
    sd = X.std(axis=axes, keepdims=X.ndim == 3) + 1e-6
    return mu, sd


# ----------------------------------------------------------------------------
# One fold
# ----------------------------------------------------------------------------


def inputs(d, kind, sensor, idx, R=None):
    """Feature matrix or raw tensor for windows `idx`, optionally rotated."""
    raw = d[f"raw_{sensor}"][idx]
    if R is not None:
        raw = raw @ R.T
    if kind == "cnn":
        return np.ascontiguousarray(raw.transpose(0, 2, 1)).astype(np.float32)
    if R is None:
        return d[f"X_{sensor}"][idx]
    return np.stack([features(w) for w in raw])


def youden(y, s):
    fpr, tpr, thr = roc_curve(y, s)
    return thr[np.argmax(tpr - fpr)]


def inner_threshold(d, kind, tr, seed, grouped, prep):
    """Threshold chosen on an inner split of the training data only."""
    rng = np.random.default_rng(seed)
    if grouped:
        subs = np.unique(d["subject"][tr])
        val_s = rng.choice(subs, size=max(2, len(subs) // 4), replace=False)
        val = tr[np.isin(d["subject"][tr], val_s)]
        fit = tr[~np.isin(d["subject"][tr], val_s)]
    else:
        perm = rng.permutation(tr)
        val, fit = perm[: len(tr) // 5], perm[len(tr) // 5:]
    if d["y"][val].sum() == 0 or d["y"][fit].sum() == 0:
        return 0.5
    s = fit_score(d, kind, fit, [val], seed, prep)[0]
    return youden(d["y"][val], s)


def fit_score(d, kind, tr, tests, seed, prep, hp=None, epoch_history=False):
    """Fit on `tr`, return scores for each element of `tests` (list of index arrays
    or (index array, sensor, rotation) tuples)."""
    sensor = prep.get("sensor", "ankle")
    Xtr = inputs(d, kind, sensor, tr)
    norm_pool = Xtr if prep.get("norm") != "all" else inputs(d, kind, sensor, np.arange(len(d["y"])))
    mu, sd = zstats(norm_pool)
    Xtr = (Xtr - mu) / sd
    sel = None
    if prep.get("select") and kind != "cnn":
        pool = np.arange(len(d["y"])) if prep["select"] == "all" else tr
        Xp = (inputs(d, kind, sensor, pool) - mu) / sd
        sel = SelectKBest(f_classif, k=10).fit(Xp, d["y"][pool]).get_support()
        Xtr = Xtr[:, sel]
    Xte = []
    for t in tests:
        idx, s_te, R = (t, sensor, None) if isinstance(t, np.ndarray) else t
        x = (inputs(d, kind, s_te, idx, R) - mu) / sd
        Xte.append(x[:, sel] if sel is not None else x)
    ytr = d["y"][tr]
    if kind == "cnn":
        model, hist = cnn_fit(Xtr.astype(np.float32), ytr, seed,
                              evals=[x.astype(np.float32) for x in Xte] if epoch_history else ())
        out = [cnn_predict(model, x.astype(np.float32)) for x in Xte]
        return (out, hist) if epoch_history else out
    m = tab_model(kind, seed, hp).fit(Xtr, ytr)
    return [m.predict_proba(x)[:, 1] for x in Xte]


# ----------------------------------------------------------------------------
# Designs
# ----------------------------------------------------------------------------

DESIGNS = {
    "D1_random_overlap": "Random window split, overlapping windows across partitions (L1+L4)",
    "D2_random_purged": "Random window split, overlapping windows purged (L4)",
    "D3_within_subject_blocks": "Within-subject chronological blocks (L4, temporally separated)",
    "D4_loso_clean": "Leave-one-subject-out, all steps fitted on training data (reference)",
    "D5_loso_norm_all": "LOSO, normalisation fitted on all data (L2)",
    "D6_loso_select_all": "LOSO, supervised feature selection on all data (L2)",
    "D6r_loso_select_train": "LOSO, supervised feature selection on training data (reference for D6)",
    "D7_loso_threshold_test": "LOSO, decision threshold tuned on the test subject (L3)",
    "D8_loso_hparam_test": "LOSO, hyperparameters or epochs selected on the test subject (L3)",
    "S1_placement_thigh": "LOSO, trained on ankle, tested on thigh sensor (placement shift)",
    "S2_rotation_45": "LOSO, test signals rotated 45 degrees (orientation shift)",
    "S3_rotation_90": "LOSO, test signals rotated 90 degrees (orientation shift)",
}


def run(d, kind, seed, log):
    n = len(d["y"])
    S = {k: np.full(n, np.nan) for k in DESIGNS}
    T = {k: np.full(n, np.nan) for k in DESIGNS}  # threshold applied to each window

    def partition(name, folds, grouped, prep=None):
        prep = prep or {}
        for tr, te in folds:
            thr = inner_threshold(d, kind, tr, seed, grouped, prep)
            S[name][te] = fit_score(d, kind, tr, [te], seed, prep)[0]
            T[name][te] = thr
        log(f"  {kind} seed{seed} {name} done")

    partition("D1_random_overlap", random_folds(d, seed, False), False)
    partition("D2_random_purged", random_folds(d, seed, True), False)
    partition("D3_within_subject_blocks", block_folds(d), False)
    partition("D5_loso_norm_all", loso_folds(d), True, {"norm": "all"})
    if kind != "cnn":
        partition("D6_loso_select_all", loso_folds(d), True, {"select": "all"})
        partition("D6r_loso_select_train", loso_folds(d), True, {"select": "train"})

    # Reference LOSO model, reused for L3 and acquisition-shift evaluations.
    rng = np.random.default_rng(1000 + seed)
    for tr, te in loso_folds(d):
        R45, R90 = rotation(45, rng), rotation(90, rng)
        tests = [te, (te, "thigh", None), (te, "ankle", R45), (te, "ankle", R90)]
        thr = inner_threshold(d, kind, tr, seed, True, {})
        if kind == "cnn":
            outs, hist = fit_score(d, kind, tr, tests, seed, {}, epoch_history=True)
            ep_auc = [roc_auc_score(d["y"][te], h[0]) if d["y"][te].any() else -1 for h in hist]
            S["D8_loso_hparam_test"][te] = hist[int(np.argmax(ep_auc))][0]
        else:
            outs = fit_score(d, kind, tr, tests, seed, {})
            grid = RF_GRID if kind == "rf" else LR_GRID
            best, best_s = -1, None
            for hp in grid:
                s = fit_score(d, kind, tr, [te], seed, {}, hp=hp)[0]
                a = roc_auc_score(d["y"][te], s) if d["y"][te].any() else 0
                if a > best:
                    best, best_s = a, s
            S["D8_loso_hparam_test"][te] = best_s
        T["D8_loso_hparam_test"][te] = thr
        for name, o in zip(["D4_loso_clean", "S1_placement_thigh", "S2_rotation_45", "S3_rotation_90"], outs):
            S[name][te] = o
            T[name][te] = thr
        S["D7_loso_threshold_test"][te] = outs[0]
        T["D7_loso_threshold_test"][te] = youden(d["y"][te], outs[0]) if d["y"][te].any() else thr
    log(f"  {kind} seed{seed} LOSO family done")
    return S, T


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--cache", default="cache")
    ap.add_argument("--out", default="results")
    ap.add_argument("--models", default="lr,rf,cnn")
    ap.add_argument("--seeds", default="0,1,2")
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    d = load(a.cache)
    logf = open(os.path.join(a.out, "log.txt"), "a")

    def log(msg):
        line = f"{time.strftime('%H:%M:%S')} {msg}"
        print(line, flush=True)
        logf.write(line + "\n")
        logf.flush()

    for kind in a.models.split(","):
        for seed in map(int, a.seeds.split(",")):
            path = os.path.join(a.out, f"scores_{kind}_seed{seed}.npz")
            if os.path.exists(path):
                continue
            t0 = time.time()
            S, T = run(d, kind, seed, log)
            np.savez_compressed(path, **{f"score__{k}": v for k, v in S.items()},
                                **{f"thr__{k}": v for k, v in T.items()})
            log(f"{kind} seed{seed} saved in {time.time() - t0:.0f}s")
    json.dump(DESIGNS, open(os.path.join(a.out, "designs.json"), "w"), indent=1)
