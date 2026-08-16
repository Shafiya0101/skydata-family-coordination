"""Experiences completes v2.
E1  Strategies (cap corrige, fw egalise) : Random / Selfish / Naive / Coordinated(oracle)
E2  Federated Learning : none vs local vs federated vs oracle (la question FL)
E3  Ablation d : quand la coordination paie-t-elle vs Naive ?
E4  Couts : migration et messages SKW
"""
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from skydata_core import (SkyWorld, RandomStrategy, SelfishPoC, NaivePoC,
                          CoordinatedPoC, metrics)

plt.rcParams.update({"figure.dpi": 120, "font.size": 10, "axes.spines.top": False,
                     "axes.spines.right": False, "axes.grid": True,
                     "grid.alpha": 0.25})

SEEDS = 20
ROUNDS = 80
REACH = 0.65


def run(mk, seed, reach=REACH, rounds=ROUNDS, d=4, track=False):
    world = SkyWorld(seed=seed)
    strat = mk()
    hist = []
    for _ in range(rounds):
        strat.step(world, reach_prob=reach, d=d)
        if track:
            hist.append(metrics(world))
    return (hist if track else metrics(world))


def table(rows, keys=("mean_dispersion", "worst_family_dispersion", "collisions")):
    hdr = {"mean_dispersion": "disp", "worst_family_dispersion": "pire",
           "collisions": "coll", "estimation_error": "err.est",
           "placement_green": "green", "migration_cost": "cout.migr",
           "skw_messages": "msgs"}
    print(f"{'Config':<34}" + "".join(f"{hdr[k]:>10}" for k in keys))
    for name, res in rows:
        vals = "".join(f"{np.mean([r[k] for r in res]):>10.3f}" for k in keys)
        print(f"{name:<34}{vals}")


# ------------------------------------------------------------------ E1
print("=" * 70)
print("E1 - Strategies (cap corrige, fw = 0.70 partout)")
print("=" * 70)
E1 = []
for name, mk in [("Random", RandomStrategy),
                 ("Selfish PoC", SelfishPoC),
                 ("Naive family-aware", NaivePoC),
                 ("SKW-coordinated (oracle)", lambda: CoordinatedPoC(None))]:
    E1.append((name, [run(mk, s) for s in range(SEEDS)]))
table(E1)

# ------------------------------------------------------------------ E2
print()
print("=" * 70)
print("E2 - Federated Learning : la connaissance partagee paie-t-elle ?")
print("    (green inconnu ; none = prior fixe, local = famille seule,")
print("     federated = agregation SKW, oracle = borne superieure)")
print("=" * 70)
modes = [("none", "Sans apprentissage"), ("local", "Local seul"),
         ("federated", "Federe (SKW)"), (None, "Oracle (borne sup.)")]
E2_hist = {}
for mode, label in modes:
    E2_hist[label] = [run(lambda: CoordinatedPoC(mode), s, track=True)
                      for s in range(SEEDS)]
rows = [(label, [h[-1] for h in E2_hist[label]]) for _, label in
        [(m, l) for m, l in modes]]
# erreur d'estimation : significative seulement pour les modes qui apprennent
print(f"{'Config':<34}{'disp':>10}{'green':>10}{'err.est':>10}")
for name, res in rows:
    d = np.mean([r["mean_dispersion"] for r in res])
    g = np.mean([r["placement_green"] for r in res])
    if name in ("Local seul", "Federe (SKW)"):
        e = f"{np.mean([r['estimation_error'] for r in res]):>10.3f}"
    else:
        e = f"{'n/a':>10}"   # prior fixe / valeurs vraies : pas d'estimation apprise
    print(f"{name:<34}{d:>10.3f}{g:>10.3f}{e}")

# figure : erreur d'estimation au fil des tours + qualite de placement
COL = {"Sans apprentissage": "#9aa0a6", "Local seul": "#e8710a",
       "Federe (SKW)": "#1a73e8", "Oracle (borne sup.)": "#137333"}
fig, (a1, a2) = plt.subplots(1, 2, figsize=(11.5, 4.3))
for label in E2_hist:
    if label == "Oracle (borne sup.)":
        pass  # l'oracle n'apprend pas ; on le trace quand meme pour reference
    arr = np.array([[h["estimation_error"] for h in run_] for run_ in E2_hist[label]])
    m = arr.mean(0)
    a1.plot(m, label=label, color=COL[label], lw=2)
    a1.fill_between(range(len(m)), m - arr.std(0), m + arr.std(0),
                    color=COL[label], alpha=0.10)
    arr2 = np.array([[h["placement_green"] for h in run_] for run_ in E2_hist[label]])
    m2 = arr2.mean(0)
    a2.plot(m2, label=label, color=COL[label], lw=2)
    a2.fill_between(range(len(m2)), m2 - arr2.std(0), m2 + arr2.std(0),
                    color=COL[label], alpha=0.10)
a1.set_xlabel("Tours"); a1.set_ylabel("Erreur d'estimation (bas = mieux)")
a1.set_title("Decouverte de la qualite des harbours")
a2.set_xlabel("Tours"); a2.set_ylabel("Qualite reelle des emplacements (haut = mieux)")
a2.set_title("Effet sur le placement")
a1.legend(frameon=False, fontsize=8); a2.legend(frameon=False, fontsize=8)
fig.tight_layout()
fig.savefig("fig_fl_learning.png", bbox_inches="tight"); plt.close(fig)
print("figure : fig_fl_learning.png")

# ------------------------------------------------------------------ E3
print()
print("=" * 70)
print("E3 - Quand la coordination paie-t-elle ? (vs Naive, fw egalise)")
print("=" * 70)
for d in [2, 4, 8, "all"]:
    n = [run(NaivePoC, s, d=d) for s in range(SEEDS)]
    c = [run(lambda: CoordinatedPoC(None), s, d=d) for s in range(SEEDS)]
    diffs = [ci["mean_dispersion"] - ni["mean_dispersion"] for ci, ni in zip(c, n)]
    print(f"d={str(d):>4} | Naive disp {np.mean([r['mean_dispersion'] for r in n]):.3f} "
          f"coll {np.mean([r['collisions'] for r in n]):.2f}  ||  "
          f"Coord disp {np.mean([r['mean_dispersion'] for r in c]):.3f} "
          f"coll {np.mean([r['collisions'] for r in c]):.2f}  ||  "
          f"delta {np.mean(diffs):+.3f}, Coord gagne {sum(x>0 for x in diffs)}/{SEEDS}")

fig, ax = plt.subplots(figsize=(7.4, 4.2))
ds = [2, 4, 8, 16, 25]
nd, cd = [], []
for d in ds:
    dd = d if d < 25 else "all"
    nd.append(np.mean([run(NaivePoC, s, d=dd)["mean_dispersion"] for s in range(12)]))
    cd.append(np.mean([run(lambda: CoordinatedPoC(None), s, d=dd)["mean_dispersion"]
                       for s in range(12)]))
ax.plot(ds, nd, "-o", label="Naive (simultane)", color="#e8710a", lw=2)
ax.plot(ds, cd, "-o", label="SKW-coordinated", color="#137333", lw=2)
ax.set_xlabel("Nombre de harbours consideres par decision (d)")
ax.set_ylabel("Dispersion finale (haut = mieux)")
ax.set_title("La coordination paie quand la vue s'elargit")
ax.legend(frameon=False, fontsize=9)
fig.tight_layout(); fig.savefig("fig_ablation_d.png", bbox_inches="tight")
plt.close(fig)
print("figure : fig_ablation_d.png")

# ------------------------------------------------------------------ E4
print()
print("=" * 70)
print("E4 - Le prix de la coordination (couts, reach=0.65, d=4)")
print("=" * 70)
E4 = []
for name, mk in [("Naive family-aware", NaivePoC),
                 ("SKW-coordinated (oracle)", lambda: CoordinatedPoC(None)),
                 ("SKW-coordinated (federated)", lambda: CoordinatedPoC("federated"))]:
    E4.append((name, [run(mk, s) for s in range(SEEDS)]))
table(E4, keys=("mean_dispersion", "migration_cost", "skw_messages"))

print()
print("Termine. Figures : fig_fl_learning.png, fig_ablation_d.png")
