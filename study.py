"""Researcher pages: study mode (human experiment) and results."""
import random, time
from pathlib import Path
import pandas as pd
import streamlit as st
from library import INCIDENTS, FACTS, INCIDENT_FACTS, BY_ID, essential
from engines import ENGINES
from experiment import make_scenario, score

LOG = Path("data/study_log.csv")
YN = {"Unknown": None, "Yes": True, "No": False}
NAMES = list(ENGINES)
ORDERS = [[0, 1, 2], [1, 2, 0], [2, 0, 1]]                      # cyclic Latin square of systems
SCEN = [make_scenario(random.Random(100 + k)) for k in range(3)]  # same three fictional cases for everyone


def ask(I, prefix):
    """Yes/No/Unknown questions for the facts relevant to incidents I."""
    obs = {}
    for f in dict.fromkeys(f for i in I for f in INCIDENT_FACTS[i]):
        v = st.radio(FACTS[f], list(YN), horizontal=True, key=prefix + f)
        if YN[v] is not None:
            obs[f] = YN[v]
    return obs


def page():
    LOG.parent.mkdir(exist_ok=True)
    tab2, tab3 = st.tabs(["Study mode", "Results"])
    with tab2:
        st.caption("Researcher use only. Cases are fictional. Participants tick the actions they would take.")
        pid = st.text_input("Participant ID")
        if pid:
            if st.session_state.get("pid") != pid:
                st.session_state.update(pid=pid, k=0)
            k = st.session_state["k"]
            if k >= 3:
                st.success("All three cases done. Thank you.")
            else:
                I, c = SCEN[k]
                sysname = NAMES[ORDERS[sum(map(ord, pid)) % 3][k]]
                t0 = st.session_state.setdefault(f"t0_{pid}_{k}", time.time())
                st.subheader(f"Case {k + 1} of 3")
                st.write("**Incident:** " + " + ".join(INCIDENTS[i] for i in I))
                for f in dict.fromkeys(f for i in I for f in INCIDENT_FACTS[i]):
                    st.write(f"- {FACTS[f]}: {'yes' if c[f] else 'no'}")
                obs = {} if sysname == NAMES[0] else ask(I, f"s{pid}{k}_")
                recs = ENGINES[sysname](I, obs)
                st.markdown("**Tick the actions you would take:**")
                chosen = [a.id for a, p in recs if st.checkbox(a.text, key=f"c{pid}{k}{a.id}")]
                need, tf = essential(I, c), f"tf_{pid}_{k}"
                if tf not in st.session_state and any(i in need and BY_ID[i].urg >= 4 for i in chosen):
                    st.session_state[tf] = time.time() - t0
                und = st.slider("I understood what to do and why", 1, 7, 4, key=f"u{pid}{k}")
                con = st.slider("I am confident I would recover correctly", 1, 7, 4, key=f"n{pid}{k}")
                if st.button("Submit this case"):
                    m = score([(BY_ID[i], None) for i in chosen], I, c)
                    row = {"participant": pid, "case": k + 1, "system": sysname,
                           "sec_to_first_correct_urgent": st.session_state.get(tf),
                           "sec_total": round(time.time() - t0, 1), "selected": ";".join(chosen),
                           "correctness": m["correctness"], "completeness": m["completeness"],
                           "unnecessary": m["unnecessary"], "understanding": und, "confidence": con}
                    pd.DataFrame([row]).to_csv(LOG, mode="a", header=not LOG.exists(), index=False)
                    st.session_state["k"] += 1
                    st.rerun()

    with tab3:
        sim = Path("sim_results.csv")
        if sim.exists():
            st.subheader("Simulation (answer key)")
            st.dataframe(pd.read_csv(sim).groupby("system")[["correctness", "completeness", "unnecessary", "est_seconds"]].mean().round(2))
        if LOG.exists():
            df = pd.read_csv(LOG)
            st.subheader(f"Study results ({df.participant.nunique()} participants)")
            cols = ["sec_to_first_correct_urgent", "sec_total", "correctness", "completeness", "unnecessary", "understanding", "confidence"]
            st.dataframe(df.groupby("system")[cols].mean().round(2))
            st.caption("For B and C, time includes answering the questions. Test differences with Friedman and Wilcoxon (Holm-corrected).")
        else:
            st.info("No study data yet. Run participants in Study mode.")
