# Experiments Log

This is the running record of every model/feature/threshold change that was
tried, what the backtest showed, and what was decided — including negative
results (brief Section 27: "if a model performs badly, show it; if an edge
disappears out-of-sample, remove it").

## Format

Each entry is one experiment:

```
## EXP-000N — <short title>
Date: YYYY-MM-DD
Hypothesis: <what we expected to improve and why>
Change: <exact model/feature/threshold change>
Method: walk-forward fold(s) used, dataset version
Result: <metrics, out-of-sample only>
Decision: SHIP | REJECT | INCONCLUSIVE (needs more data)
Reasoning: <why>
```

## Ablation testing (brief Section 14)

Ablation runs compare nested feature sets to find out which variables
actually help, e.g.:

```
Model A: Elo + goals
Model B: Elo + goals + xG
Model C: Elo + goals + xG + injuries
Model D: everything available
```

Each ablation run is logged here as an experiment with `Method: ablation`
and reports the metric delta per added feature group, out-of-sample. A
feature group that does not improve Brier Score/Log Loss out-of-sample
(within noise, assessed across folds) is a candidate for removal — logged
as `Decision: REJECT` with the feature group named, and removed from the
production feature set.

## Log

No experiments have been run yet — Phase 0-4 (research, architecture, data,
feature engineering) must exist before there is anything to backtest. This
file is scaffolded now so Phase 5 onward has nowhere else to put results and
no way to quietly skip logging a negative one.
