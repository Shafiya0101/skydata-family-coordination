"""
stats_tests.py — reproduces every quantitative claim in the paper.

Runs the same engine (skydata_core.py) used throughout the project, over a fixed
number of paired seeds, and prints:
  * Table I   — strategy comparison (dispersion / worst family / collisions)
  * Table II  — candidate-count (d) sweep with paired t-tests
  * Sec. V-C  — federated-learning discovery time (rounds to reach an error threshold)
  * Table III — cost of coordination (migration cost / SKW messages)

Every number printed here is the number that should appear in the paper.
Run:  python stats_tests.py
Requires: numpy, scipy   (pip install numpy scipy)
"""

import numpy as np
from scipy import stats
from skydata_core import (SkyWorld, RandomStrategy, SelfishPoC, NaivePoC,
                          CoordinatedPoC, metrics)

# ---- fixed experimental configuration (matches the paper's setup) ----
SEEDS  = 60
ROUNDS = 80
REACH  = 0.65


def run_final(make_strategy, seed, d=4):
    """Run one strategy on one seeded world; return the final-round metrics."""
    world = SkyWorld(seed=seed)
    strat = make_strategy()
    for _ in range(ROUNDS):
        strat.step(world, reach_prob=REACH, d=d)
    return metrics(world)


def run_tracked(make_strategy, seed, d=4):
    """Run one strategy; return the per-round metric history (for FL curves)."""
    world = SkyWorld(seed=seed)
    strat = make_strategy()
    hist = []
    for _ in range(ROUNDS):
        strat.step(world, reach_prob=REACH, d=d)
        hist.append(metrics(world))
    return hist


def collect(make_strategy, key, d=4):
    return np.array([run_final(make_strategy, s, d)[key] for s in range(SEEDS)])


def sep():
    print("=" * 68)


# ============================================================= TABLE I
sep(); print(f"TABLE I  —  strategy comparison  (n={SEEDS} seeds, d=4, reach={REACH})"); sep()
strategies = [
    ("Random",             lambda: RandomStrategy()),
    ("Selfish",            lambda: SelfishPoC()),
    ("Naive family-aware", lambda: NaivePoC()),
    ("SKW-coordinated",    lambda: CoordinatedPoC()),
]
print(f"{'Strategy':<20}{'Dispersion':>12}{'Worst fam.':>12}{'Collisions':>12}")
for name, mk in strategies:
    disp  = collect(mk, "mean_dispersion").mean()
    worst = collect(mk, "worst_family_dispersion").mean()
    coll  = collect(mk, "collisions").mean()
    print(f"{name:<20}{disp:>12.3f}{worst:>12.3f}{coll:>12.2f}")

# ============================================================= TABLE II
sep(); print(f"TABLE II  —  candidate-count (d) sweep  (n={SEEDS} paired seeds)"); sep()
print(f"{'d':>4}{'Naive disp':>12}{'Naive coll':>12}{'Coord disp':>12}"
      f"{'Coord coll':>12}{'Coord wins':>12}{'t':>8}{'p':>10}")
for d in [2, 4, 8, 25]:
    nd = collect(lambda: NaivePoC(),       "mean_dispersion", d)
    nc = collect(lambda: NaivePoC(),       "collisions",      d)
    cd = collect(lambda: CoordinatedPoC(), "mean_dispersion", d)
    cc = collect(lambda: CoordinatedPoC(), "collisions",      d)
    wins = int((cd > nd).sum())
    t, p = stats.ttest_rel(cd, nd)
    label = "all" if d == 25 else str(d)
    print(f"{label:>4}{nd.mean():>12.3f}{nc.mean():>12.2f}{cd.mean():>12.3f}"
          f"{cc.mean():>12.2f}{f'{wins}/{SEEDS}':>12}{t:>8.2f}{p:>10.2e}")

# ============================================================= FL (Sec. V-C)
sep(); print(f"SECTION V-C  —  federated learning discovery time  (n={SEEDS} seeds)"); sep()

def error_curve(mode):
    """Mean estimation-error curve over rounds for a knowledge mode."""
    curves = np.zeros((SEEDS, ROUNDS))
    for s in range(SEEDS):
        hist = run_tracked(lambda: CoordinatedPoC(learning_mode=mode), s)
        curves[s] = [h["estimation_error"] for h in hist]
    return curves.mean(axis=0)

def rounds_to(curve, thresh):
    idx = np.where(curve < thresh)[0]
    return (idx[0] + 1) if len(idx) else None

local = error_curve("local")
fed   = error_curve("federated")
for th in (0.05, 0.04):
    print(f"error < {th}: federated = {rounds_to(fed, th)} rounds, "
          f"local-only = {rounds_to(local, th)} rounds")

# placement quality (final round) per mode
print("\nFinal placement quality (green of occupied harbours):")
for mode, label in [(None, "oracle"), ("none", "no learning"),
                    ("local", "local"), ("federated", "federated")]:
    pl = collect(lambda: CoordinatedPoC(learning_mode=mode), "placement_green").mean()
    print(f"  {label:<12}: {pl:.3f}")

# advantage at round 10
adv = []
for s in range(SEEDS):
    l = run_tracked(lambda: CoordinatedPoC(learning_mode="local"), s)[9]["estimation_error"]
    f = run_tracked(lambda: CoordinatedPoC(learning_mode="federated"), s)[9]["estimation_error"]
    adv.append(l - f)   # positive => federated has lower error
adv = np.array(adv)
print(f"\nRound-10 error advantage (local - federated): mean {adv.mean():+.3f}, "
      f"federated better on {int((adv > 0).sum())}/{SEEDS} seeds")

# ============================================================= TABLE III
sep(); print(f"TABLE III  —  cost of coordination  (n={SEEDS} seeds, d=4)"); sep()
cost_rows = [
    ("Naive family-aware",      lambda: NaivePoC()),
    ("SKW-coordinated",         lambda: CoordinatedPoC()),
    ("SKW-coordinated + fed.",  lambda: CoordinatedPoC(learning_mode="federated")),
]
print(f"{'Strategy':<24}{'Dispersion':>12}{'Migr. cost':>12}{'SKW msgs':>12}")
for name, mk in cost_rows:
    disp = collect(mk, "mean_dispersion").mean()
    cost = collect(mk, "migration_cost").mean()
    msgs = collect(mk, "skw_messages").mean()
    print(f"{name:<24}{disp:>12.3f}{cost:>12.1f}{msgs:>12.0f}")

sep(); print("Done. Every value above is what should appear in the paper."); sep()
