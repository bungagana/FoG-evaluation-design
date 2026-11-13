# FoG evaluation design

Code and data for the manuscript **"Evaluation Design of Artificial Intelligence Models for Freezing of Gait in Parkinson's Disease: A Systematic Review and Controlled Experiment"** (Muna, Fajar, Sarno, Hitam and Sungkono).

The repository reproduces three parts of the manuscript:

| Part | Folder | Reproduces |
|---|---|---|
| Controlled leakage experiment on the Daphnet Freezing of Gait dataset | [`1_controlled_experiment/`](1_controlled_experiment) | Experiment results, Fig. 7, Supplementary Tables 5 and 6 |
| Between-study analyses of the 83 included studies | [`2_between_study_analysis/`](2_between_study_analysis) | Between-study tests, Supplementary Table 4 |
| Figures | [`3_figures/`](3_figures) | Figs. 1 to 7 |

## Repository structure

```
data/
  coded_studies.xlsx            Final codes of the 83 included studies (sheet 05_INCLUDED_DATA)
                                and within-study paired contrasts (sheet 07_RQ2_PERFORMANCE)
  headline_values.csv           Headline value per study used in the between-study analyses
1_controlled_experiment/
  prepare.py                    Segments Daphnet into 4 s windows and computes features
  run_experiment.py             Trains LR, RF and CNN under 12 evaluation designs with seeds 0, 1 and 2
  evaluate_final.py             Window, participant and episode metrics, paired cluster bootstrap
                                (5,000 resamples), exact Wilcoxon signed-rank tests with Holm adjustment
  results/                      Out-of-fold scores (scores_*.npz) and the outputs used in the manuscript
2_between_study_analysis/
  between_study.py              The 19 between-study tests with Holm adjustment
  expected_output/              Output used in the manuscript
3_figures/
  fig1_mechanisms/              Fig. 1 (SVG), rendered to PDF and PNG with render.js
  fig2_prisma/                  Fig. 2, PRISMA 2020 flow diagram (SVG), rendered with render.js
  fig3_to_fig7/                 Figs. 3 to 6 from the coded studies, and Fig. 7 from the experiment results
```

The complete coded dataset of the review, with supporting quotations, risk-of-bias judgements, search strings and screening decisions, is Additional file 1 of the article. The two files in `data/` are the subsets that the scripts read.

## Installation

Python 3.10 or later. The results were produced with the versions in [`requirements.txt`](requirements.txt).

```bash
git clone https://github.com/bungagana/FoG-evaluation-design.git
cd FoG-evaluation-design
pip install -r requirements.txt
```

Figures 1 and 2 are written as SVG files. Converting them to PDF and PNG requires Node.js and Playwright (`npm install playwright`, then `npx playwright install chromium`). The figure scripts use Arial and fall back to Liberation Sans.

## Reproducing the results

### 1. Controlled experiment

Download the Daphnet Freezing of Gait dataset from the UCI Machine Learning Repository (https://doi.org/10.24432/C56K78) and extract it. The scripts read the `S*R*.txt` files in `dataset_fog_release/dataset`.

```bash
cd 1_controlled_experiment
mkdir cache results_new
python prepare.py <path>/dataset_fog_release/dataset cache
python run_experiment.py --cache cache --out results_new --models lr,rf,cnn --seeds 0,1,2
python evaluate_final.py --cache cache --res results_new
```

`run_experiment.py` takes about 1 to 1.5 hours on a CPU, mostly for the CNN. The evaluation can also be recomputed from the scores used in the manuscript without retraining. Run `prepare.py` and then:

```bash
python evaluate_final.py --cache cache --res results
```

This overwrites the CSV files in `results/` with identical values.

### 2. Between-study analyses

```bash
cd 2_between_study_analysis
python between_study.py ../data/coded_studies.xlsx ../data/headline_values.csv between_study_tests.csv
```

### 3. Figures

```bash
cd 3_figures/fig3_to_fig7
mkdir figures_out
python make_fig3_to_fig6.py ../../data/coded_studies.xlsx figures_out ../../data/headline_values.csv
python make_fig7.py ../../1_controlled_experiment/results figures_out

cd ../fig1_mechanisms
python make_fig1.py
node render.js fig1_mechanisms.svg fig1_mechanisms 180 120

cd ../fig2_prisma
python make_fig2.py
node render.js fig2_prisma.svg fig2_prisma 130 129.8
```

## Verification

The repository was checked on 13 November 2026 with Python 3.11 on Windows 11, using the package versions in `requirements.txt`:

- `between_study.py` reproduces `expected_output/between_study_tests.csv` exactly.
- Figures 3 to 7 are pixel-identical to the figures in the manuscript.
- `prepare.py` followed by `evaluate_final.py` on the saved scores reproduces `final_deltas.csv`, `final_summary.csv` and `final_per_subject.csv`.
- Retraining logistic regression with seed 0 gives scores that correlate at 0.999 or higher with the saved scores. The change in pooled AUROC from the reference differs by at most 0.001 in every design. The remaining differences arise from floating-point differences between platforms and library builds, so the saved scores in `results/` are the reference for the reported values.

## Notes on the experiment

- The leakage-free reference is leave-one-subject-out evaluation with every step fitted on the training participants (`D4_loso_clean`). Design D6 is compared with D6r, which selects features on the training participants only.
- Two Daphnet participants have no freezing episodes, so their test AUROC is undefined. Under design D8, `run_experiment.py` selects the first grid configuration for these two participants. `evaluate_final.py` replaces these with the default configuration (the D4 scores) and reports the as-run version as `D8_asrun`.
- Holm adjustment is applied across the primary contrasts within each model.

## Licence

The code is released under the MIT Licence ([`LICENSE`](LICENSE)). The data files in `data/` and `1_controlled_experiment/results/` are released under CC BY 4.0. The Daphnet dataset is not included and is subject to its own licence.

## Citation

Please cite the article when using this code or data. Citation metadata for the repository is in [`CITATION.cff`](CITATION.cff), and GitHub shows it under "Cite this repository".

## Contact

Riyanarto Sarno, Department of Informatics, Institut Teknologi Sepuluh Nopember, Surabaya, Indonesia (riyanarto@its.ac.id).
