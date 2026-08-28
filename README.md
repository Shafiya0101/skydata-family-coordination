# SkyData — Family-Aware Federated Coordination of Autonomous Data Replicas

How do the replicas of one datum (a *family*) spread across hosts in
[SkyData](https://hal.science/hal-04040588) — with no permanent central
authority, no guaranteed communication between agents — and what does
federated learning genuinely contribute?

**Live demo:** https://skydata-family-coordination.netlify.app/interface_demo
*(click any replica to see its partial view of the network)*

## Findings (v2 — after internal review and corrections)

1. **Family-awareness is the decisive factor.** Selfish replicas cluster and
   collide (dispersion 0.305, 2.13 collisions/family); any family-aware
   strategy doubles dispersion (~0.62) and eliminates collisions.
2. **SkyWorker coordination is a stability guarantee whose value grows with
   the agents' view.** At d = 4 sampled candidates it is indistinguishable
   from naive simultaneous decisions (a null result we report plainly); at
   d = 8 it wins **52/60 paired seeds**, and with a full view the naive
   strategy collapses (collisions return) while coordination stays flat and
   collision-free. It also cuts migration cost ~4x (36 vs 154) at the price
   of ~2,500 SkyWorker messages.
3. **Federated learning halves discovery time.** Harbour quality is unknown a
   priori; families estimate it from noisy local observations; a SkyWorker
   aggregates estimates across reached families (federated averaging weighted
   by observation counts — no raw data centralised). Federation reaches
   estimation error < 0.05 in **8 rounds vs 14** for local-only learning
   (better on 60/60 paired seeds at round 10); final placement matches
   local-only, near the oracle bound. The value of federation is the **speed
   of collective discovery**.

Full numbers: [`RESULTS_v2.md`](RESULTS_v2.md).

## What changed in v2 (methodological note)

An internal review of v1 found: (a) the family-dispersion weight differed
between strategies, confounding the coordination comparison; (b) the capacity
term rewarded congested harbours; (c) the first learning layer was circular
(the update contained its own target). All three are fixed: weights equalised
(fw = 0.70), `cap = 1 - saturation`, and the learning layer rebuilt as
federated estimation of unknown harbour quality. All experiments re-run with
paired seeds. Where v1's reading was wrong, we say so.

## Repository layout

```
code/skydata_core.py     # simulator v2 (strategies + federated layer)
code/run_all.py          # experiments (writes the figures; quick 20-seed pass)
code/stats_tests.py      # >>> authoritative numbers: 60 seeds + paired t-tests <<<
code/ablations.py        # review follow-up: cap term + matched-weight ablation
code/ablation_d.py       # review follow-up: candidate-count sweep
notebook/SkyData_Notebook_Complet.ipynb   # simulator + experiments + demo
demo/Interface_demo.html # interactive map (works offline, double-click)
RESULTS_v2.md            # all corrected results (60-seed)
FICHE_SOUTENANCE.md      # defense cheat-sheet (FR)
```

## Reproduce

```bash
pip install numpy scipy matplotlib
cd code
python stats_tests.py    # authoritative: reproduces every number in the paper/report
                         # (60 paired seeds, with paired t-tests)
python run_all.py        # writes the figures; quicker 20-seed pass, numbers slightly differ
python ablations.py      # review follow-up: cap term + matched-weight ablation
python ablation_d.py     # review follow-up: candidate-count sweep
```

> **Which script for which numbers?** The paper and report use the **60-seed** output of
> `stats_tests.py`. `run_all.py` runs a quicker 20-seed pass and is used mainly to
> regenerate the figures, so its numbers differ slightly from the reported values.

## Positioning (short version)

- **vs gossip learning** (Ormándi et al.; Hegedűs, Danner & Jelasity): gossip
  averages peer-to-peer along a graph and needs peers to reach one another;
  SkyData guarantees no path between agents. The SkyWorker is a *mobile
  aggregation point*, native to SkyData, that works even when families never
  meet.
- **vs FL with partial participation** (Wang & Ji, NeurIPS 2022; Cho, Wang &
  Joshi 2020): there, participation is a sampling/availability matter; here it
  is a property of the environment — participants are mobile and never
  guaranteed to return.

## Scope

Proof of concept in our own simulator. The message layer is coarse; harbour
quality is static. Next steps: port to JADE/Jason; dynamic harbour conditions
(where federated discovery speed should matter most).

## Team

AIVANCITY research project, supervised by Dr. Etienne Mauffret.
Habiba Djigo · Ketsia Talotsing · Lucrece Leckat · Maheni Soumah · Shafiya Kausar
