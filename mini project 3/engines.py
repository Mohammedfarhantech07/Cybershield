"""System A (fixed checklist), B (rule-based), C (intelligent). Each returns [(Action, confidence_or_None)].
`I` is a list of incident codes (first = primary). `obs` maps fact -> True/False; missing means unknown."""
from itertools import product
from library import ACTIONS, INCIDENT_FACTS, PRIOR, full


def checklist(I, obs):
    return [(a, None) for a in ACTIONS if I[0] in a.core]


def rules(I, obs):
    out = []
    for a in ACTIONS:
        if I[0] not in a.inc:
            continue
        if a.rule:
            neg = a.rule[0] == "!"
            if (obs.get(a.rule.lstrip("!")) is True) == neg:   # unknown counts as "no"
                continue
        out.append(a)
    return [(a, None) for a in sorted(out, key=lambda a: -a.urg)]


def intelligent(I, obs, keep=0.40, keep_urgent=0.25):
    """Chance each action is essential, averaged over unanswered facts using PRIOR.
    Urgent (5) actions get a lower bar so safety-critical steps are rarely dropped.
    Ranked by urgency x chance; actions are moved after their prerequisites."""
    Is = set(I)
    facts = sorted({f for i in I for f in INCIDENT_FACTS[i]})
    unk = [f for f in facts if obs.get(f) is None]
    known = {f: obs[f] for f in facts if obs.get(f) is not None}
    cand = [a for a in ACTIONS if a.inc & Is]
    p = {a.id: 0.0 for a in cand}
    for bits in product([False, True], repeat=len(unk)):
        c = full({**known, **dict(zip(unk, bits))})
        w = 1.0
        for f, b in zip(unk, bits):
            w *= PRIOR[f] if b else 1 - PRIOR[f]
        for a in cand:
            if a.need(c, Is):
                p[a.id] += w
    ranked = sorted([(a, p[a.id]) for a in cand if p[a.id] >= (keep_urgent if a.urg >= 5 else keep)],
                    key=lambda x: -x[0].urg * x[1])
    return _after_prereqs(ranked)


def _after_prereqs(L):
    L = list(L)
    for _ in range(len(L) ** 2):
        for k, (a, _) in enumerate(L):
            pre = [j for j, (b, _) in enumerate(L) if b.id in a.after]
            if pre and max(pre) > k:
                L.insert(max(pre), L.pop(k))
                break
        else:
            return L
    return L


ENGINES = {"A: Fixed checklist": checklist, "B: Rule-based": rules, "C: Intelligent": intelligent}
