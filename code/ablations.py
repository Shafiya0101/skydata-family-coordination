"""Ablations demandees par la relecture interne :
A) cap = saturation  vs  cap = 1 - saturation (le point 3a)
B) poids familial egalise : Naive(fw=0.70) vs Coordinated(fw=0.70) (le point 1)
Memes seeds partout pour une comparaison appariee.
"""
import numpy as np
import skydata_core as sc
from skydata_core import (SkyWorld, SelfishPoC, NaivePoC,
                          CoordinatedPoC, metrics)

SEEDS = 20
ROUNDS = 80
REACH = 0.65


def run(strategy, seed, cap_mode):
    # patch du terme cap selon le mode teste
    orig = sc.candidate_score
    def patched(world, skd, cand, family_future, family_weight, green_estimate=None, learn_family=None):
        h = world.harbours[cand]
        if h.free <= 0 and cand != skd.harbour:
            return -1e9
        cap = h.saturation if cap_mode == "saturation" else (1.0 - h.saturation)
        green = h.green
        move = world.dist[skd.harbour, cand] / world.max_dist
        if family_future:
            fam_disp = float(np.mean([world.dist[cand, p] / world.max_dist for p in family_future]))
            too_close = sum(1 for p in family_future if world.dist[cand, p] / world.max_dist < 0.20)
        else:
            fam_disp, too_close = 0.5, 0
        return 0.30 * cap + 0.25 * green + family_weight * fam_disp - 0.20 * move - 0.35 * too_close
    sc.candidate_score = patched
    try:
        world = SkyWorld(seed=seed)
        for _ in range(ROUNDS):
            strategy.step(world, reach_prob=REACH, d=4)
        return metrics(world)
    finally:
        sc.candidate_score = orig


class NaiveFW(NaivePoC):
    """Naive avec un poids familial parametrable (pour l'ablation matched-fw)."""
    def __init__(self, fw):
        self.fw = fw
        self.name = f"Naive (fw={fw})"

    def step(self, world, reach_prob, d=4):
        from skydata_core import family_positions, candidate_score
        proposals = {}
        snap = {fam.family_id: family_positions(fam) for fam in world.families}
        skds = world.all_skds()
        world.rng.shuffle(skds)
        for skd in skds:
            fam_pos = list(snap[skd.family_id])
            if skd.harbour in fam_pos:
                fam_pos.remove(skd.harbour)
            best = max(self._sample_candidates(world, skd, reach_prob, d),
                       key=lambda c: sc.candidate_score(world, skd, c, fam_pos, self.fw))
            proposals[skd.sid] = int(best)
        for skd in skds:
            world.move(skd, proposals[skd.sid])


def table(rows):
    print(f"{'Config':<38}{'disp':>7}{'pire':>8}{'coll':>7}")
    for name, res in rows:
        d = np.mean([r['mean_dispersion'] for r in res])
        w = np.mean([r['worst_family_dispersion'] for r in res])
        c = np.mean([r['collisions'] for r in res])
        print(f"{name:<38}{d:>7.3f}{w:>8.3f}{c:>7.2f}")


print("=" * 62)
print("ABLATION A - le terme cap : saturation vs (1 - saturation)")
print("=" * 62)
for mode in ["saturation", "inverse"]:
    label = "cap = saturation (actuel)" if mode == "saturation" else "cap = 1 - saturation (corrige)"
    print(f"\n--- {label} ---")
    rows = []
    for name, mk in [("Selfish", lambda: SelfishPoC()),
                     ("Naive fw=0.55", lambda: NaiveFW(0.55)),
                     ("Coordinated fw=0.70", lambda: CoordinatedPoC())]:
        res = [run(mk(), seed, mode) for seed in range(SEEDS)]
        rows.append((name, res))
    table(rows)

print()
print("=" * 62)
print("ABLATION B - poids egalise (cap corrige) : la coordination seule")
print("=" * 62)
rows = []
for name, mk in [("Naive fw=0.70 (matched)", lambda: NaiveFW(0.70)),
                 ("Coordinated fw=0.70", lambda: CoordinatedPoC())]:
    res = [run(mk(), seed, "inverse") for seed in range(SEEDS)]
    rows.append((name, res))
table(rows)

# difference appariee par seed pour etre rigoureux
print("\nDifference appariee (Coordinated - Naive matched), par seed :")
n_res = [run(NaiveFW(0.70), s, "inverse") for s in range(SEEDS)]
c_res = [run(CoordinatedPoC(), s, "inverse") for s in range(SEEDS)]
diffs = [c['mean_dispersion'] - n['mean_dispersion'] for c, n in zip(c_res, n_res)]
w_diffs = [c['worst_family_dispersion'] - n['worst_family_dispersion'] for c, n in zip(c_res, n_res)]
print(f"  dispersion : moyenne {np.mean(diffs):+.4f}, ecart-type {np.std(diffs):.4f}, "
      f"positif sur {sum(d>0 for d in diffs)}/{SEEDS} seeds")
print(f"  pire fam.  : moyenne {np.mean(w_diffs):+.4f}, positif sur {sum(d>0 for d in w_diffs)}/{SEEDS} seeds")
