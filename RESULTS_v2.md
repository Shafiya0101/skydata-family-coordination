# Results v2 — corrected experiments and the real Federated Learning layer

All experiments: 20 seeds (paired across configurations), 80 rounds,
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
| Naive family-aware        | 0.617     | 0.530        | 0.00       |
| SKW-coordinated (oracle)  | 0.619     | 0.528        | 0.00       |

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
| No learning         | 0.662     | 0.477                         | n/a (fixed prior)|
| Local only          | 0.623     | 0.682                         | 0.024            |
| Federated (SKW)     | 0.623     | 0.682                         | 0.020            |
| Oracle (upper bound)| 0.619     | 0.690                         | n/a              |

*Estimation error is only meaningful for the learning modes: "no learning" keeps a fixed prior (its 0.254 is the prior's error, nothing is learned) and the oracle bypasses estimates entirely.*

Speed of discovery (the FL question):

- error < 0.05 reached in **7.8 rounds (federated)** vs **14.1 (local)** — 1.8x faster
- error < 0.04 reached in **10.3 rounds (federated)** vs **21.7 (local)** — 2.1x faster
- at round 10, federated beats local on **20/20 paired seeds** (mean delta +0.024)

Honest claims: (1) learning matters enormously — placement quality rises from
0.477 to 0.682, close to the oracle's 0.690; (2) federated sharing roughly
halves the time to discover harbour quality under partial observability, while
final performance converges to the same near-oracle level; (3) the value of
federation here is the **speed of collective discovery**, which is what matters
in a dynamic system — and no raw observation is ever centralised.

## E3 — When does coordination pay? (matched fw, corrected cap)

| d    | Naive disp | Naive coll | Coord disp | Coord coll | Paired delta | Coord wins |
|------|-----------|-----------|-----------|-----------|--------------|------------|
| 2    | 0.620     | 0.00      | 0.621     | 0.00      | +0.002       | 11/20      |
| 4    | 0.617     | 0.00      | 0.619     | 0.00      | +0.002       | 12/20      |
| 8    | 0.588     | 0.25      | 0.619     | 0.00      | +0.031       | **20/20**  |
| all  | 0.570     | 0.44      | 0.621     | 0.00      | +0.051       | 18/20      |

With a narrow random glance (small d), random sampling already de-synchronises
replicas. With a wide view, simultaneous decisions collide again (collisions
return for Naive) while the coordinated strategy is flat and collision-free
regardless of d. Coordination = a stability guarantee whose value grows with
the agents' view of the network.

## E4 — The price of coordination

| Strategy                    | Dispersion | Migration cost | SKW messages |
|-----------------------------|-----------|----------------|--------------|
| Naive family-aware          | 0.617     | 154.2          | 0            |
| SKW-coordinated (oracle)    | 0.619     | **36.4**       | 2 491        |
| SKW-coordinated (federated) | 0.623     | 39.1           | 2 613        |

Unexpected and valuable: sequential reservation cuts migration cost by ~4x —
replicas stop chasing each other — at the price of SKW messaging. A clean
distributed-systems trade-off: communication buys placement stability and a
large saving in movement.

## The story for the defense

1. Family-awareness vs selfish is the massive effect (collisions eliminated,
   dispersion doubled).
2. SkyWorker coordination is a stability guarantee: indistinguishable from
   naive when views are narrow, decisively better when views widen (20/20 at
   d = 8), always collision-free, and ~4x cheaper in migration cost.
3. Federated learning is real and quantified: SkyWorker aggregation of family
   estimates halves the time to discover harbour quality under partial
   observability, without centralising any raw data.
4. Everything is a proof of concept in our own simulator; porting to
   JADE/Jason is the next step.
