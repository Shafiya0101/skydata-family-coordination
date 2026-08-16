# SkyData — Family-Aware Federated Coordination of Autonomous Data Replicas

**A research project on how autonomous data copies spread themselves across a network — with no central controller — and what federated learning adds.**

*AIVANCITY · Federated Learning in Multi-Agent Systems · supervised by Dr. Etienne Mauffret.*

**▶ [Try the live demo](https://skydata-family-coordination.netlify.app/interface_demo)** — watch the copies migrate, and click any copy to see the limited slice of the network it can actually see.

---

## The problem

[SkyData](https://hal.science/hal-04040588) is a data system with **no central manager**. Every piece of data is an autonomous agent — an **SKD** — that decides for itself which host (a **harbour**) to live on. There is no global map of the network, and no guarantee that any two agents can ever reach each other.

Data is copied for safety, and the copies of one datum form a **family**. This creates the problem we study:

> If every copy independently picks the most attractive harbour, they all pick the **same** one. Then a single failure destroys the whole family — and the copies were pointless.

The copies need to **spread out**. But each one decides alone, sees only part of the network, and can't coordinate through any central authority.

## Our idea

A **temporary SkyWorker** — a helper agent that appears, coordinates one family so its copies move to *different* harbours, then disappears. It holds no permanent authority, which keeps SkyData's "no central controller" rule intact. On top of that, we add a **federated learning** layer so families can learn which harbours are good and share that knowledge without sharing raw data.

## What we found

1. **Being family-aware is what matters most.** Selfish copies cluster together and collide constantly. The moment copies simply try to avoid their siblings, they spread out twice as well and collisions disappear.

2. **The SkyWorker is a stability guarantee whose value grows with how much each copy can see.** When copies only glance at a few harbours, coordination barely helps — random chance already keeps siblings apart (we report this null result honestly). But when copies can see more of the network, uncoordinated copies collapse back onto the same harbours, while the SkyWorker keeps them reliably spread. It also cuts the amount of movement by about **4×**, at the cost of some coordination messages.

3. **Federated learning roughly halves the time to discover good harbours.** Each family learns harbour quality from its own noisy observations; the SkyWorker combines these estimates across families without ever centralising raw data. Families reach a good picture of the network about **twice as fast** together than alone. The benefit of federation here is the *speed* of collective discovery.

Full numbers and tables: [`RESULTS_v2.md`](RESULTS_v2.md).

## Try it yourself

**The live demo** ([link above](https://skydata-family-coordination.netlify.app/interface_demo)) is the easiest way in — no install. Pick a strategy, watch the copies move, drag the reachability slider to limit what they can see, and click a copy to inspect its partial view.

**Run the experiments:**

```bash
pip install numpy matplotlib
cd code
python run_all.py       # ~5 min; writes the figures + prints all result tables
python ablations.py     # review follow-ups: scoring-term + matched-weight checks
python ablation_d.py    # review follow-up: how coordination scales with the view
```

**Or open the notebook** — `notebook/SkyData_Notebook_Complet.ipynb` runs the simulator, experiments and demo end-to-end (works in Google Colab).

## Repository layout

```
code/skydata_core.py     # the simulator: harbours, families, strategies, federated layer
code/run_all.py          # main experiments — produces every figure and table
code/ablations.py        # review follow-up: scoring-sign + matched-weight checks
code/ablation_d.py       # review follow-up: candidate-count sweep
notebook/                # the full notebook (simulator + experiments + demo)
demo/Interface_demo.html # the interactive map (also runs offline — just double-click)
figures/                 # generated figures
RESULTS_v2.md            # all results in full
FICHE_SOUTENANCE.md      # defense notes (French)
```

*The research paper and the literature survey are being prepared for submission to a conference/journal and are not included in this repository yet.*

## How it relates to existing work

- **Versus gossip learning:** gossip spreads knowledge peer-to-peer and needs agents to reach one another — but SkyData guarantees no such path. The SkyWorker is a *mobile meeting point* that works even when families never meet directly.
- **Versus federated learning with partial participation:** there, missing participants are a scheduling or sampling issue; here it's a fact of the environment — agents are mobile and may never come back.

## Scope and honesty

This is a proof of concept in our own simulator, not yet a deployment. The communication model is simplified and harbour quality is static for now. We also did an internal review of our first version and corrected three real flaws before publishing these results — the corrected story is the one above. Details of what changed are in [`RESULTS_v2.md`](RESULTS_v2.md).

**Next steps:** port the mechanism to the JADE/Jason agent platform, and test it with harbours whose quality changes over time — where fast federated discovery should matter most.

## Team

Habiba Djigo · Shafiya Kausar · Maheni Soumah · Ketsia Talotsing · Lucrece Leckat, 
AIVANCITY — supervised by Dr. Etienne Mauffret.
