"""Exploratory between-study analyses of reported headline performance and
evaluation features, with Holm adjustment across all tests."""
import re
import sys

import numpy as np
import pandas as pd
from scipy import stats

WB, HEADLINE, OUT = sys.argv[1:4]
a = pd.read_excel(WB, sheet_name="05_INCLUDED_DATA", header=1)
h = pd.read_csv(HEADLINE)[["Study_ID", "hv"]]
d = a.merge(h, on="Study_ID", how="left")
T = d["Strictest tier"]
indep = T.isin(["Subject-independent", "External or cross-dataset"])


def family(s):
    s = s.lower()
    if re.search(r"threshold|rule", s):
        return "Threshold"
    if re.search(r"transformer|attention|cnn|lstm|recurrent|deep|convolution|neural|autoencoder|gan|dae|tcnn|bilstm|gru|mlp", s):
        return "Deep learning"
    if "not reported" in s:
        return "Not reported"
    return "Classical ML"


d["family"] = d["Model family"].apply(family)
d["daphnet"] = d["Dataset"].str.contains("Daphnet", case=False, na=False)
rows = []


def mw(name, m1, m2, l1, l2):
    x, y = d.loc[m1, "hv"].dropna(), d.loc[m2, "hv"].dropna()
    p = stats.mannwhitneyu(x, y, alternative="two-sided").pvalue
    rows.append(dict(test=name, kind="Mann-Whitney U (headline value)", group1=l1, n1=len(x), est1=f"median {x.median():.3f}",
                     group2=l2, n2=len(y), est2=f"median {y.median():.3f}", p=p))


def fx(name, m1, m2, l1, l2, outcome, olabel):
    a1, n1 = (outcome & m1).sum(), m1.sum()
    a2, n2 = (outcome & m2).sum(), m2.sum()
    p = stats.fisher_exact([[a1, n1 - a1], [a2, n2 - a2]]).pvalue
    rows.append(dict(test=name, kind=f"Fisher exact ({olabel})", group1=l1, n1=int(n1), est1=f"{a1}/{n1} ({100 * a1 / n1:.1f}%)",
                     group2=l2, n2=int(n2), est2=f"{a2}/{n2} ({100 * a2 / n2:.1f}%)", p=p))


has = d["hv"].notna()
hi = d["hv"] >= 0.95
k = has & (T != "Not reported")
rho, p = stats.spearmanr(T[k].map({"Within-subject or record-wise": 0, "Subject-independent": 1,
                                    "External or cross-dataset": 2}), d.loc[k, "hv"])
rows.append(dict(test="Validation tier trend", kind="Spearman rho", group1="WS<SI<External", n1=int(k.sum()),
                 est1=f"rho {rho:.2f}", group2="", n2=None, est2="", p=p))
ws = T == "Within-subject or record-wise"
mw("Within-subject vs independent", ws, indep, "Within-subject", "Subject-independent or external")
fx("Within-subject vs independent", ws & has, indep & has, "Within-subject", "Subject-independent or external", hi, "headline >= 0.95")
leak = d["Any leakage"] == "Yes"
mw("Any leakage", leak, d["Any leakage"] == "No", "Yes", "No")
fx("Any leakage", leak & has, (d["Any leakage"] == "No") & has, "Yes", "No", hi, "headline >= 0.95")
for code, col in [("L1", "L1 Window split at random"), ("L2", "L2 Normalised on all data"),
                  ("L3", "L3 Tuned on test data"), ("L4", "L4 Same person in train & test")]:
    mw(f"{code} present vs absent", d[col] == "Present", d[col] == "Absent", "Present", "Absent")
for code, col in [("L1", "L1 Window split at random"), ("L4", "L4 Same person in train & test")]:
    fx(f"{code} present vs absent", (d[col] == "Present") & has, (d[col] == "Absent") & has, "Present", "Absent", hi,
       "headline >= 0.95")
fx("Daphnet vs other data", d.daphnet, ~d.daphnet, "Daphnet", "Other", leak, "any leakage")
fx("Daphnet vs other data", d.daphnet, ~d.daphnet, "Daphnet", "Other", ws, "within-subject tier")
mw("Daphnet vs other data", d.daphnet, ~d.daphnet, "Daphnet", "Other")
code = d["Code released?"] == "Yes"
fx("Code released vs not", code, ~code, "Released", "Not released", leak, "any leakage")
dl, ml = d.family == "Deep learning", d.family == "Classical ML"
mw("Deep learning vs classical ML", dl, ml, "Deep learning", "Classical ML")
fx("Deep learning vs classical ML", dl, ml, "Deep learning", "Classical ML", leak, "any leakage")
fx("Deep learning vs classical ML", dl, ml, "Deep learning", "Classical ML", d["L3 Tuned on test data"] == "Present", "L3 present")
per = pd.cut(d.Year.astype(int), [2017, 2023, 2026], labels=["2018-2023", "2024-2026"])
fx("Publication period", per == "2024-2026", per == "2018-2023", "2024-2026", "2018-2023", leak, "any leakage")

r = pd.DataFrame(rows)
order = np.argsort(r.p.values)
m = len(r)
adj = np.empty(m)
running = 0
for rank, i in enumerate(order):
    running = max(running, min(1, (m - rank) * r.p.values[i]))
    adj[i] = running
r["p_holm"] = adj
r.to_csv(OUT, index=False)
pd.set_option("display.width", 250)
print(r[["test", "kind", "est1", "est2", "p", "p_holm"]].round(4).to_string())
low = d[(d["Overall RoB"] == "Low") & has]
print("low RoB headline n", len(low), "max", low.hv.max())
print("family counts", d.family.value_counts().to_dict())
