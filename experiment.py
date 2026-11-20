"""Simulation + scoring. Run:  python experiment.py --n 2000
Scores every engine against the answer key (library.essential). Human measures (real decision time,
understanding, confidence) come from the Study tab in app.py, not from here."""
import argparse, random
import pandas as pd
from library import INCIDENTS, INCIDENT_FACTS, PRIOR, BY_ID, essential, full
from engines import ENGINES

READ_SECONDS = 9   # read-time model: seconds spent per item before reaching a needed urgent action


def make_scenario(rng, compound=0.3):
    I = [rng.choice(list(INCIDENTS))]
    if rng.random() < compound:                      # e.g. fraudulent payment plus a compromised account
        I.append(rng.choice([k for k in INCIDENTS if k != I[0]]))
    return I, full({f: rng.random() < PRIOR[f] for i in I for f in INCIDENT_FACTS[i]})


def observe(I, c, q, rng):
    return {f: c[f] for i in I for f in INCIDENT_FACTS[i] if rng.random() < q}


def score(recs, I, c):
    need = essential(I, c)
    ids = [a.id for a, _ in recs]
    tp = sum(i in need for i in ids)
    pos = next((k + 1 for k, i in enumerate(ids) if i in need and BY_ID[i].urg >= 4), len(ids) + 3)
    return {"correctness": tp / len(ids) if ids else 0.0, "completeness": tp / len(need),
            "unnecessary": len(ids) - tp, "items_to_first_urgent": pos, "est_seconds": READ_SECONDS * pos}


def simulate(n=2000, q=0.7, seed=7):
    rng, rows = random.Random(seed), []
    for s in range(n):
        I, c = make_scenario(rng)
        obs = observe(I, c, q, rng)
        for name, eng in ENGINES.items():
            rows.append({"scenario": s, "incident": I[0], "compound": len(I) > 1, "answer_rate": q, "system": name,
                         **score(eng(I, obs), I, c)})
    return pd.DataFrame(rows)


METRICS = ["correctness", "completeness", "unnecessary", "est_seconds"]

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=2000)
    ap.add_argument("--q", type=float, default=0.7, help="share of questions the user can answer")
    a = ap.parse_args()
    df = simulate(a.n, a.q)
    df.to_csv("sim_results.csv", index=False)
    print(df.groupby("system")[METRICS].mean().round(2), "\n")
    print(df.groupby(["incident", "system"])[METRICS].mean().round(2), "\n")
    sweep = pd.concat(simulate(max(a.n // 4, 200), q) for q in (0.3, 0.5, 0.7, 0.9, 1.0))
    print(sweep.pivot_table(index="answer_rate", columns="system", values=["correctness", "completeness"]).round(2))
    import matplotlib; matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig, ax = plt.subplots(1, 3, figsize=(11, 3.4))
    for k, m in enumerate(["correctness", "completeness", "unnecessary"]):
        sweep.groupby(["answer_rate", "system"])[m].mean().unstack().plot(ax=ax[k], marker="o", title=m)
        ax[k].set_xlabel("share of questions answered")
    plt.tight_layout(); plt.savefig("sim_chart.png", dpi=130)
