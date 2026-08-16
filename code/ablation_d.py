"""Ablation C - le nombre de candidats d comme axe experimental.
Hypothese (relecture interne) : avec d petit, le tirage aleatoire desynchronise
deja les replicas ; la coordination sequentielle paie surtout quand la vue est
large (d grand), car c'est la que les decisions simultanees se percutent.
Tout est a poids egalise (fw=0.70) et cap corrige (1 - saturation).
"""
import numpy as np
import skydata_core as sc
from skydata_core import SkyWorld, CoordinatedFamilyAwarePoC, metrics, family_positions

SEEDS = 20
ROUNDS = 80
REACH = 0.65
FW = 0.70


def patched_score(world, skd, cand, family_future, family_weight):
    h = world.harbours[cand]
    if h.free <= 0 and cand != skd.harbour:
        return -1e9
    cap = 1.0 - h.saturation
    green = h.green
    move = world.dist[skd.harbour, cand] / world.max_dist
    if family_future:
        fam_disp = float(np.mean([world.dist[cand, p] / world.max_dist for p in family_future]))
        too_close = sum(1 for p in family_future if world.dist[cand, p] / world.max_dist < 0.20)
    else:
        fam_disp, too_close = 0.5, 0
    return 0.30 * cap + 0.25 * green + family_weight * fam_disp - 0.20 * move - 0.35 * too_close

sc.candidate_score = patched_score


def sample_cands(world, skd, reach_prob, d):
    reachable = world.reachable_harbours(skd.harbour, reach_prob)
    if not reachable:
        return [skd.harbour]
    if d == "all":
        cand = list(reachable)
    else:
        cand = list(world.rng.choice(reachable, size=min(d, len(reachable)), replace=False))
    if skd.harbour not in cand:
        cand.append(skd.harbour)
    return cand


def step_naive(world, reach_prob, d):
    proposals = {}
    snap = {fam.family_id: family_positions(fam) for fam in world.families}
    skds = world.all_skds()
    world.rng.shuffle(skds)
    for skd in skds:
        fam_pos = list(snap[skd.family_id])
        if skd.harbour in fam_pos:
            fam_pos.remove(skd.harbour)
        best = max(sample_cands(world, skd, reach_prob, d),
                   key=lambda c: sc.candidate_score(world, skd, c, fam_pos, FW))
        proposals[skd.sid] = int(best)
    for skd in skds:
        world.move(skd, proposals[skd.sid])


def step_coord(world, reach_prob, d):
    fams = list(world.families)
    world.rng.shuffle(fams)
    for fam in fams:
        reached = [m for m in fam.members if world.rng.random() < reach_prob]
        if not reached:
            continue
        reached.sort(key=lambda m: world.harbours[m.harbour].load, reverse=True)
        reserved = [m.harbour for m in fam.members if m not in reached]
        for skd in reached:
            ff = reserved + [m.harbour for m in reached
                             if m.sid != skd.sid and m.harbour != skd.harbour]
            best = max(sample_cands(world, skd, reach_prob, d),
                       key=lambda c: sc.candidate_score(world, skd, c, ff, FW))
            world.move(skd, int(best))
            reserved.append(skd.harbour)


def run(step_fn, seed, d):
    world = SkyWorld(seed=seed)
    for _ in range(ROUNDS):
        step_fn(world, REACH, d)
    return metrics(world)


print("=" * 66)
print("ABLATION C - effet du nombre de candidats d (fw=0.70, cap corrige)")
print("=" * 66)
for d in [2, 4, 8, "all"]:
    n_res = [run(step_naive, s, d) for s in range(SEEDS)]
    c_res = [run(step_coord, s, d) for s in range(SEEDS)]
    nd = np.mean([r['mean_dispersion'] for r in n_res])
    cd = np.mean([r['mean_dispersion'] for r in c_res])
    nw = np.mean([r['worst_family_dispersion'] for r in n_res])
    cw = np.mean([r['worst_family_dispersion'] for r in c_res])
    nc = np.mean([r['collisions'] for r in n_res])
    cc = np.mean([r['collisions'] for r in c_res])
    diffs = [c['mean_dispersion'] - n['mean_dispersion'] for c, n in zip(c_res, n_res)]
    wins = sum(x > 0 for x in diffs)
    print(f"\nd = {d}")
    print(f"  {'':<14}{'disp':>7}{'pire':>8}{'coll':>7}")
    print(f"  {'Naive':<14}{nd:>7.3f}{nw:>8.3f}{nc:>7.2f}")
    print(f"  {'Coordinated':<14}{cd:>7.3f}{cw:>8.3f}{cc:>7.2f}")
    print(f"  delta disp (appariee) : {np.mean(diffs):+.4f} | Coordinated gagne {wins}/{SEEDS} seeds")
