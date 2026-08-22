# Results v2 — corrected experiments and the real Federated Learning layer

All experiments: 60 seeds (paired across configurations), 80 rounds,
reachability 0.65, d = 4 candidates unless stated. Corrections applied from
the internal review: `cap = 1 - saturation` (free capacity rewarded), family
weight fw = 0.70 identical across all family-aware strategies, separate RNG
streams for environment and strategies. New metrics: migration cost (total
normalised distance moved) and SKW messages (agent/family contacts).

## E1 — Strategies (corrected)

| Strategy                  | Dispersion | Worst family | Collisions |
|---------------------------|-----------|--------------|------------|
| Random                    | 0.432     | 0.241        | 1.00       |
| Selfish PoC               | 0.305     | 0.087        | 2.13       |
| Naive family-aware        | 0.637     | 0.545        | 0.00       |
| SKW-coordinated           | 0.637     | 0.549        | 0.00       |

The large, robust effect is family-awareness vs selfish. At d = 4, naive and
coordinated are statistically indistinguishable (see E3 for where they part).

## E2 — Federated Learning (the real layer)

Setup: the energy quality (`green`) of harbours is unknown a priori. A replica
only obtains a noisy observation of a harbour's quality when it evaluates it.
Each family maintains an estimate (mean of its own observations). The
migration score uses the estimate, not the true value. Modes: `none` (fixed
prior), `local` (family learns alone), `federated` (a SkyWorker aggregates
estimates across reached families every 5 rounds — weighted federated
averaging by observation counts — and redistributes), `oracle` (true values,
upper bound).

Final state:

| Mode                | Dispersion | Placement quality (true green) | Estimation error |
|---------------------|-----------|-------------------------------|------------------|
| No learning         | 0.662     | 0.506                         | 0.254            |
| Local only          | 0.623     | 0.700                         | 0.024            |
| Federated (SKW)     | 0.623     | 0.700                         | 0.020            |
| Oracle (upper bound)| 0.619     | 0.707                         | —                |

Speed of discovery (the FL question):

- error < 0.05 reached in **8 rounds (federated)** vs **14 (local)** — ~2x faster
- error < 0.04 reached in **10.3 rounds (federated)** vs **21.7 (local)** — 2.1x faster
- at round 10, federated beats local on **60/60 paired seeds** (mean delta +0.023)

Honest claims: (1) learning matters enormously — placement quality rises from
0.506 to 0.700, close to the oracle's 0.707; (2) federated sharing roughly
halves the time to discover harbour quality under partial observability, while
final performance converges to the same near-oracle level; (3) the value of
federation here is the **speed of collective discovery**, which is what matters
in a dynamic system — and no raw observation is ever centralised.

## E3 — When does coordination pay? (matched fw, corrected cap)

| d    | Naive disp | Naive coll | Coord disp | Coord coll | Paired delta | Coord wins |
|------|-----------|-----------|-----------|-----------|--------------|------------|
| 2    | 0.636     | 0.00      | 0.638     | 0.00      | +0.002       | 28/60      |
| 4    | 0.637     | 0.00      | 0.637     | 0.00      | +0.000       | 33/60      |
| 8    | 0.608     | 0.22      | 0.638     | 0.00      | +0.031       | **52/60**  |
| all  | 0.576     | 0.45      | 0.638     | 0.00      | +0.062       | **60/60**  |

With a narrow random glance (small d), random sampling already de-synchronises
replicas. With a wide view, simultaneous decisions collide again (collisions
return for Naive) while the coordinated strategy is flat and collision-free
regardless of d. Coordination = a stability guarantee whose value grows with
the agents' view of the network.

## E4 — The price of coordination

| Strategy                    | Dispersion | Migration cost | SKW messages |
|-----------------------------|-----------|----------------|--------------|
| Naive family-aware          | 0.617     | 134.7          | 0            |
| SKW-coordinated (oracle)    | 0.619     | **35.5**       | 2 491        |
| SKW-coordinated (federated) | 0.623     | 37.9           | 2 613        |

Unexpected and valuable: sequential reservation cuts migration cost by ~4x —
replicas stop chasing each other — at the price of SKW messaging. A clean
distributed-systems trade-off: communication buys placement stability and a
large saving in movement.

## The story for the defense

1. Family-awareness vs selfish is the massive effect (collisions eliminated,
   dispersion doubled).
2. SkyWorker coordination is a stability guarantee: indistinguishable from
   naive when views are narrow, decisively better when views widen (52/60 at
   d = 8), always collision-free, and ~4x cheaper in migration cost.
3. Federated learning is real and quantified: SkyWorker aggregation of family
   estimates halves the time to discover harbour quality under partial
   observability, without centralising any raw data.
4. Everything is a proof of concept in our own simulator; porting to
   JADE/Jason is the next step.
