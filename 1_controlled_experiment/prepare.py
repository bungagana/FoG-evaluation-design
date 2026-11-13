"""Segment the Daphnet recordings into windows and compute features.

Daphnet columns: time (ms), ankle xyz, thigh xyz, trunk xyz (mg), annotation
(0 = outside experiment, 1 = no freeze, 2 = freeze). Sampling rate 64 Hz.
"""
import glob
import os
import sys

import numpy as np

FS = 64
WIN = 4 * FS            # 4 s windows
SENSORS = {"ankle": slice(1, 4), "thigh": slice(4, 7), "trunk": slice(7, 10)}


def load_recordings(root):
    recs = []
    for path in sorted(glob.glob(os.path.join(root, "S*R*.txt"))):
        name = os.path.basename(path)[:-4]
        data = np.loadtxt(path)
        recs.append({"subject": name[:3], "run": name, "data": data})
    return recs


def episodes(annot):
    """Contiguous freeze episodes as (start, end) sample indices."""
    fog = (annot == 2).astype(int)
    edges = np.diff(np.r_[0, fog, 0])
    return list(zip(np.where(edges == 1)[0], np.where(edges == -1)[0]))


def band_power(f, p, lo, hi):
    m = (f >= lo) & (f < hi)
    return p[m].sum()


def features(seg):
    """Hand-crafted features for one window of shape (WIN, 3)."""
    sig = np.column_stack([seg, np.linalg.norm(seg, axis=1)])
    out = []
    f = np.fft.rfftfreq(WIN, 1 / FS)
    for x in sig.T:
        xc = x - x.mean()
        p = np.abs(np.fft.rfft(xc * np.hanning(WIN))) ** 2
        loco = band_power(f, p, 0.5, 3)
        frz = band_power(f, p, 3, 8)
        tot = loco + frz + 1e-9
        pn = p[(f >= 0.5) & (f < 8)]
        pn = pn / (pn.sum() + 1e-9)
        out += [x.mean(), xc.std(), np.sqrt((x ** 2).mean()), x.max() - x.min(),
                np.log(loco + 1), np.log(frz + 1), frz / (loco + 1e-9), np.log(tot),
                f[np.argmax(p * ((f >= 0.5) & (f < 8)))],
                -(pn * np.log(pn + 1e-12)).sum()]
    return np.asarray(out, dtype=np.float32)


FEATURE_NAMES = [f"{ax}_{n}" for ax in ["x", "y", "z", "mag"] for n in
                 ["mean", "std", "rms", "range", "loco_pow", "freeze_pow",
                  "freeze_index", "total_pow", "dom_freq", "spec_entropy"]]


def segment(recs, step):
    """Return windows, raw signals, labels, and bookkeeping for a given step."""
    rows = []
    for ri, r in enumerate(recs):
        d = r["data"]
        ann = d[:, 10]
        for s in range(0, len(d) - WIN + 1, step):
            a = ann[s:s + WIN]
            if (a == 0).mean() > 0.5:
                continue
            rows.append((ri, s, int((a == 2).mean() >= 0.5)))
    return rows


def build(root, out):
    recs = load_recordings(root)
    for step, tag in [(WIN // 2, "ov50"), (WIN, "ov0")]:
        rows = segment(recs, step)
        y = np.array([r[2] for r in rows], dtype=np.int8)
        subj = np.array([recs[r[0]]["subject"] for r in rows])
        run = np.array([recs[r[0]]["run"] for r in rows])
        start = np.array([r[1] for r in rows])
        payload = {"y": y, "subject": subj, "run": run, "start": start}
        for sname, sl in SENSORS.items():
            raw = np.stack([recs[ri]["data"][s:s + WIN, sl] for ri, s, _ in rows]).astype(np.float32)
            payload[f"raw_{sname}"] = raw
            payload[f"X_{sname}"] = np.stack([features(w) for w in raw])
        np.savez_compressed(os.path.join(out, f"windows_{tag}.npz"), **payload)
        print(tag, "windows", len(y), "FoG", int(y.sum()), "subjects", sorted(set(subj)))
    # episode table for event-level metrics
    ep = []
    for r in recs:
        for s, e in episodes(r["data"][:, 10]):
            ep.append((r["subject"], r["run"], s, e))
    np.save(os.path.join(out, "episodes.npy"), np.array(ep, dtype=object), allow_pickle=True)
    nonfog_s = sum(((r["data"][:, 10] == 1).sum()) for r in recs) / FS
    print("episodes", len(ep), "non-FoG hours", round(nonfog_s / 3600, 2))


if __name__ == "__main__":
    build(sys.argv[1], sys.argv[2])
