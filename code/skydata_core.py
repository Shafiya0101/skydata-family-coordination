"""Simulateur SkyData v2 - coordination familiale + federated learning reel.

Corrections issues de la revue interne :
- cap = 1 - saturation (on prefere la capacite libre ; l'ancien choix
  "consolidation" reste disponible via score_mode)
- poids familial identique (fw) entre les strategies comparees
- generateurs aleatoires separes pour l'environnement et les strategies
- metriques ajoutees : cout de migration, nombre de messages SKW

Couche Federated Learning (nouvelle, non circulaire) :
- la qualite energetique (green) des harbours est INCONNUE a priori
- un replica ne l'observe (avec bruit) que pour les harbours qu'il evalue
- chaque famille maintient une estimation green_hat[h] + un compteur d'observations
- le score de migration utilise l'estimation, pas la vraie valeur
- modes : "none" (prior fixe), "local" (chaque famille apprend seule),
  "federated" (un SkyWorker agrege les estimations entre familles atteintes,
  moyenne ponderee par les compteurs, puis redistribue)
La question testee : le partage federe accelere-t-il la decouverte des bons
harbours sous vision partielle ? (federe vs local vs sans apprentissage)
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional
import numpy as np


@dataclass
class Harbour:
    hid: int
    pos: np.ndarray
    capacity: int
    green: float          # qualite reelle, cachee aux agents
    load: int = 0

    @property
    def free(self) -> int:
        return max(0, self.capacity - self.load)

    @property
    def saturation(self) -> float:
        return self.load / self.capacity if self.capacity else 1.0


@dataclass
class SKD:
    sid: int
    family_id: int
    harbour: int


@dataclass
class Family:
    family_id: int
    members: List[SKD]
    # modele local : estimation de green par harbour + nb d'observations
    green_hat: np.ndarray = None
    obs_count: np.ndarray = None


class SkyWorld:
    def __init__(self, n_harbours=25, n_families=12, family_size=4, seed=0,
                 obs_noise=0.15):
        self.env_rng = np.random.default_rng(seed)          # environnement
        self.rng = np.random.default_rng(seed + 10_000)     # strategies
        self.obs_noise = obs_noise
        self.harbours = []
        for i in range(n_harbours):
            self.harbours.append(Harbour(
                hid=i, pos=self.env_rng.uniform(0, 100, size=2),
                capacity=int(self.env_rng.integers(5, 18)),
                green=float(self.env_rng.uniform(0.0, 1.0))))
        P = np.stack([h.pos for h in self.harbours])
        diff = P[:, None, :] - P[None, :, :]
        self.dist = np.sqrt((diff ** 2).sum(axis=-1))
        self.max_dist = max(1.0, float(self.dist.max()))

        # familles groupees au depart (il faut migrer pour se disperser)
        self.families = []
        sid = 0
        centers = self.env_rng.choice(n_harbours, size=n_families, replace=True)
        for fid in range(n_families):
            members = []
            near = np.argsort(self.dist[int(centers[fid])])[:3]
            for _ in range(family_size):
                h = int(self.env_rng.choice(near))
                self.harbours[h].load += 1
                members.append(SKD(sid=sid, family_id=fid, harbour=h))
                sid += 1
            fam = Family(fid, members)
            fam.green_hat = np.full(n_harbours, 0.5)   # prior neutre
            fam.obs_count = np.zeros(n_harbours)
            self.families.append(fam)

        # compteurs de couts
        self.migration_cost = 0.0     # distance totale parcourue
        self.skw_messages = 0         # contacts SKW <-> agents / familles

    def all_skds(self):
        return [m for fam in self.families for m in fam.members]

    def reachable_harbours(self, current, reach_prob):
        return [h.hid for h in self.harbours
                if h.hid == current or self.rng.random() < reach_prob]

    def observe_green(self, fam: Family, hid: int):
        # observation bruitee de la qualite reelle -> mise a jour incrementale
        obs = float(np.clip(self.harbours[hid].green
                            + self.env_rng.normal(0, self.obs_noise), 0, 1))
        fam.obs_count[hid] += 1
        n = fam.obs_count[hid]
        fam.green_hat[hid] += (obs - fam.green_hat[hid]) / n

    def move(self, skd, target):
        if target == skd.harbour or self.harbours[target].free <= 0:
            return
        self.migration_cost += self.dist[skd.harbour, target] / self.max_dist
        self.harbours[skd.harbour].load -= 1
        self.harbours[target].load += 1
        skd.harbour = target


def family_positions(fam, exclude_sid=None):
    return [m.harbour for m in fam.members
            if exclude_sid is None or m.sid != exclude_sid]


def dispersion(world, positions):
    if len(positions) < 2:
        return 0.0
    ds = [world.dist[positions[i], positions[j]] / world.max_dist
          for i in range(len(positions)) for j in range(i + 1, len(positions))]
    return float(np.mean(ds)) if ds else 0.0


def collision_count(world, positions, threshold=0.20):
    c = 0
    for i in range(len(positions)):
        for j in range(i + 1, len(positions)):
            d = world.dist[positions[i], positions[j]] / world.max_dist
            if positions[i] == positions[j] or d < threshold:
                c += 1
    return c


def candidate_score(world, skd, cand, family_future, family_weight,
                    green_estimate=None, learn_family: Optional[Family] = None):
    """Score d'un harbour candidat.
    - cap recompense la capacite LIBRE (correction de la revue)
    - green utilise l'estimation de la famille si fournie (couche FL),
      sinon la vraie valeur (borne superieure "oracle")
    - si learn_family est fourni, evaluer un candidat produit une observation
    """
    h = world.harbours[cand]
    if h.free <= 0 and cand != skd.harbour:
        return -1e9
    cap = 1.0 - h.saturation
    if learn_family is not None:
        world.observe_green(learn_family, cand)
    green = h.green if green_estimate is None else green_estimate[cand]
    move = world.dist[skd.harbour, cand] / world.max_dist
    if family_future:
        fam_disp = float(np.mean([world.dist[cand, p] / world.max_dist
                                  for p in family_future]))
        too_close = sum(1 for p in family_future
                        if world.dist[cand, p] / world.max_dist < 0.20)
    else:
        fam_disp, too_close = 0.5, 0
    return (0.30 * cap + 0.25 * green + family_weight * fam_disp
            - 0.20 * move - 0.35 * too_close)


FW = 0.70   # poids familial unique pour toutes les strategies family-aware


class Strategy:
    name = "base"

    def step(self, world, reach_prob, d=4):
        raise NotImplementedError

    def _sample_candidates(self, world, skd, reach_prob, d):
        reachable = world.reachable_harbours(skd.harbour, reach_prob)
        if not reachable:
            return [skd.harbour]
        if d == "all":
            cand = list(reachable)
        else:
            cand = list(world.rng.choice(reachable,
                                         size=min(d, len(reachable)),
                                         replace=False))
        if skd.harbour not in cand:
            cand.append(skd.harbour)
        return cand


class RandomStrategy(Strategy):
    name = "Random"

    def step(self, world, reach_prob, d=4):
        skds = world.all_skds()
        world.rng.shuffle(skds)
        for skd in skds:
            feas = [h for h in world.reachable_harbours(skd.harbour, reach_prob)
                    if world.harbours[h].free > 0]
            if feas:
                world.move(skd, int(world.rng.choice(feas)))


class SelfishPoC(Strategy):
    name = "Selfish PoC"

    def step(self, world, reach_prob, d=4):
        skds = world.all_skds()
        world.rng.shuffle(skds)
        for skd in skds:
            cands = self._sample_candidates(world, skd, reach_prob, d)
            best = max(cands, key=lambda c: candidate_score(
                world, skd, c, None, 0.0))
            world.move(skd, int(best))


class NaivePoC(Strategy):
    name = "Naive family-aware PoC"

    def step(self, world, reach_prob, d=4):
        proposals = {}
        snap = {fam.family_id: family_positions(fam) for fam in world.families}
        skds = world.all_skds()
        world.rng.shuffle(skds)
        for skd in skds:
            fam_pos = list(snap[skd.family_id])
            if skd.harbour in fam_pos:
                fam_pos.remove(skd.harbour)
            best = max(self._sample_candidates(world, skd, reach_prob, d),
                       key=lambda c: candidate_score(world, skd, c, fam_pos, FW))
            proposals[skd.sid] = int(best)
        for skd in skds:
            world.move(skd, proposals[skd.sid])


class CoordinatedPoC(Strategy):
    """Coordination par SkyWorker : reservation sequentielle au sein de la
    famille. learning_mode pilote la couche FL :
      None        -> score avec la vraie valeur green (oracle, pas d'apprentissage)
      "none"      -> estimation figee au prior 0.5 (aucun apprentissage)
      "local"     -> chaque famille apprend de ses observations, sans partage
      "federated" -> apprentissage local + agregation inter-familles par SKW
    """
    def __init__(self, learning_mode=None, agg_every=5):
        self.learning_mode = learning_mode
        self.agg_every = agg_every
        self._round = 0
        base = "SKW-coordinated"
        if learning_mode is None:
            self.name = base + " (oracle)"
        else:
            self.name = base + f" ({learning_mode})"

    def step(self, world, reach_prob, d=4):
        self._round += 1
        fams = list(world.families)
        world.rng.shuffle(fams)
        for fam in fams:
            reached = [m for m in fam.members if world.rng.random() < reach_prob]
            if not reached:
                continue
            world.skw_messages += len(reached)     # contacts SKW <-> replicas
            reached.sort(key=lambda m: world.harbours[m.harbour].load,
                         reverse=True)
            reserved = [m.harbour for m in fam.members if m not in reached]
            est, learner = self._estimates(fam)
            for skd in reached:
                ff = reserved + [m.harbour for m in reached
                                 if m.sid != skd.sid and m.harbour != skd.harbour]
                best = max(self._sample_candidates(world, skd, reach_prob, d),
                           key=lambda c: candidate_score(
                               world, skd, c, ff, FW,
                               green_estimate=est, learn_family=learner))
                world.move(skd, int(best))
                reserved.append(skd.harbour)
        if self.learning_mode == "federated" and self._round % self.agg_every == 0:
            self._skw_aggregate(world, reach_prob)

    def _estimates(self, fam):
        if self.learning_mode is None:
            return None, None                       # vraie valeur (oracle)
        if self.learning_mode == "none":
            return np.full(len(fam.green_hat), 0.5), None
        return fam.green_hat, fam                   # local / federated

    def _skw_aggregate(self, world, reach_prob):
        # FedAvg pondere par les compteurs d'observations, sur les familles atteintes
        reached = [f for f in world.families if world.rng.random() < reach_prob]
        if len(reached) < 2:
            return
        world.skw_messages += len(reached)          # contacts SKW <-> familles
        counts = np.stack([f.obs_count for f in reached])
        hats = np.stack([f.green_hat for f in reached])
        total = counts.sum(axis=0)
        with np.errstate(invalid="ignore", divide="ignore"):
            global_hat = np.where(total > 0,
                                  (counts * hats).sum(axis=0) / total, 0.5)
        for f in reached:
            # adoption ponderee : une famille bien informee bouge peu
            w = np.clip(f.obs_count / (f.obs_count + 3.0), 0.0, 0.9)
            f.green_hat = w * f.green_hat + (1 - w) * global_hat
            f.obs_count = np.maximum(f.obs_count, total * 0.25)


def metrics(world):
    fam_disp, fam_coll, est_err = [], [], []
    for fam in world.families:
        pos = family_positions(fam)
        fam_disp.append(dispersion(world, pos))
        fam_coll.append(collision_count(world, pos))
        true_green = np.array([h.green for h in world.harbours])
        est_err.append(float(np.mean(np.abs(fam.green_hat - true_green))))
    # qualite reelle des emplacements occupes (le green VRAI, pas l'estime)
    placement_green = float(np.mean(
        [world.harbours[m.harbour].green for m in world.all_skds()]))
    return {
        "mean_dispersion": float(np.mean(fam_disp)),
        "worst_family_dispersion": float(np.min(fam_disp)),
        "collisions": float(np.mean(fam_coll)),
        "estimation_error": float(np.mean(est_err)),
        "placement_green": placement_green,
        "migration_cost": world.migration_cost,
        "skw_messages": world.skw_messages,
    }
