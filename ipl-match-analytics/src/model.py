"""Two questions about predicting IPL results.

1. Pre-match: can information known before the first ball predict the winner?
2. Live: during a chase, how likely is the chasing team to win from here?

Every feature is built only from matches played *before* the one being predicted,
so the model never sees the future. Trained on 2008-2022, tested on 2023 onwards.

Usage:
    python src/model.py
"""

import json
import os
from collections import defaultdict, deque

import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, brier_score_loss, log_loss, roc_auc_score
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

ROOT = os.path.join(os.path.dirname(__file__), "..")
TEST_FROM = 2023
FORM_WINDOW = 10   # recent form = last 10 matches
PRIOR = 5          # shrink small samples towards 50%


def rate(wins, games):
    return (wins + 0.5 * PRIOR) / (games + PRIOR)


def build_features(m):
    form = defaultdict(lambda: deque(maxlen=FORM_WINDOW))
    career = defaultdict(lambda: [0, 0])
    h2h = defaultdict(lambda: [0, 0])
    venue_chase = defaultdict(lambda: [0, 0])
    rows = []

    for r in m.itertuples():
        # Team A is the alphabetically first side, so the label is not tied to listing order
        a, b = sorted([r.team1, r.team2])
        key = (a, b)
        vc = venue_chase[r.venue]
        a_bats_second = int(r.bat_second == a)
        rows.append({
            "season": int(r.season),
            "a_won_toss": int(r.toss_winner == a),
            "a_bats_second": a_bats_second,
            "a_form": rate(sum(form[a]), len(form[a])),
            "b_form": rate(sum(form[b]), len(form[b])),
            "a_career": rate(*career[a]),
            "b_career": rate(*career[b]),
            "a_h2h": rate(*h2h[key]),
            "venue_chase_rate": rate(*vc),
            "chase_edge_for_a": (rate(*vc) - 0.5) * (1 if a_bats_second else -1),
            "target": int(r.winner == a),
        })
        # Update history only after the row is recorded
        for t in (a, b):
            won = int(r.winner == t)
            form[t].append(won)
            career[t][0] += won
            career[t][1] += 1
        h2h[key][0] += int(r.winner == a)
        h2h[key][1] += 1
        vc[0] += int(r.winner == r.bat_second)
        vc[1] += 1

    df = pd.DataFrame(rows)
    df["form_diff"] = df.a_form - df.b_form
    df["career_diff"] = df.a_career - df.b_career
    return df


def scores(y, p):
    return {
        "accuracy": round(accuracy_score(y, p >= 0.5), 3),
        "log_loss": round(log_loss(y, np.clip(p, 1e-6, 1 - 1e-6)), 3),
        "brier": round(brier_score_loss(y, p), 3),
        "auc": round(roc_auc_score(y, p), 3) if len(set(np.round(p, 6))) > 1 else 0.5,
    }


LIVE_FEATS = ["runs_needed", "balls_left", "wickets_left", "required_rate", "rr_x_wkts"]


def chase_features(c):
    c = c.copy()
    c["required_rate"] = 6 * c.runs_needed / c.balls_left.clip(lower=1)
    c["rr_x_wkts"] = c.required_rate * (10 - c.wickets_left)
    return c


def chase_model():
    """Win probability for the chasing team at the end of each over."""
    c = chase_features(pd.read_csv(os.path.join(ROOT, "data", "chase_states.csv")))
    train, test = c[c.season < TEST_FROM], c[c.season >= TEST_FROM]
    model = make_pipeline(StandardScaler(), LogisticRegression(C=1.0, max_iter=1000))
    model.fit(train[LIVE_FEATS], train.chasing_team_won)
    test = test.assign(p=model.predict_proba(test[LIVE_FEATS])[:, 1])

    by_stage = {}
    for label, lo, hi in (("After 6 overs", 6, 6), ("After 10 overs", 10, 10), ("After 15 overs", 15, 15)):
        t = test[(test.over >= lo) & (test.over <= hi)]
        by_stage[label] = {"states": int(len(t)), **scores(t.chasing_team_won.values, t.p.values)}

    # Calibration: when the model says 70%, does the chaser win about 70% of the time?
    bins = pd.cut(test.p, np.linspace(0, 1, 11), include_lowest=True)
    calib = test.groupby(bins, observed=True).agg(predicted=("p", "mean"), actual=("chasing_team_won", "mean"), n=("p", "size"))
    calib = calib[calib.n >= 20].round(3)

    # Win-probability curve for the most recent match in the test set
    last_id = test.match_id.iloc[-1]
    curve = test[test.match_id == last_id][["over", "runs_needed", "balls_left", "wickets_left", "p"]]

    import pickle
    with open(os.path.join(ROOT, "outputs", "chase_model.pkl"), "wb") as f:
        pickle.dump(model, f)

    # The game changed in 2023 (Impact Player rule). Does retraining on recent seasons fix calibration?
    # Retrain on seasons up to 2024 with a flag for the Impact Player era, test on 2025 onwards.
    c["impact_era"] = (c.season >= 2023).astype(int)
    era_feats = LIVE_FEATS + ["impact_era"]
    recent_train, recent_test = c[c.season < 2025], c[c.season >= 2025]
    retrained = make_pipeline(StandardScaler(), LogisticRegression(C=1.0, max_iter=1000))
    retrained.fit(recent_train[era_feats], recent_train.chasing_team_won)
    old_p = model.predict_proba(recent_test[LIVE_FEATS])[:, 1]
    new_p = retrained.predict_proba(recent_test[era_feats])[:, 1]
    y25 = recent_test.chasing_team_won.values
    retrain = {
        "test_seasons": "2025-" + str(int(c.season.max())),
        "trained_to_2022": {**scores(y25, old_p), "mean_predicted": round(float(old_p.mean()), 3)},
        "trained_to_2024_with_era_flag": {**scores(y25, new_p), "mean_predicted": round(float(new_p.mean()), 3)},
        "actual_chase_win_rate": round(float(y25.mean()), 3),
    }

    return {
        "retrain_check": retrain,
        "train_states": int(len(train)),
        "test_states": int(len(test)),
        "overall": scores(test.chasing_team_won.values, test.p.values),
        "by_stage": by_stage,
        "calibration": calib.reset_index(drop=True).to_dict("records"),
        "example_match_id": str(last_id),
        "example_curve": curve.round(3).to_dict("records"),
    }


def main():
    m = pd.read_csv(os.path.join(ROOT, "data", "matches.csv"))
    m = m[m.result != "no result"].sort_values(["date", "match_id"])
    os.makedirs(os.path.join(ROOT, "outputs"), exist_ok=True)
    df = build_features(m)
    train, test = df[df.season < TEST_FROM], df[df.season >= TEST_FROM]
    feats = ["a_won_toss", "a_bats_second", "form_diff", "career_diff", "a_h2h", "chase_edge_for_a"]
    y = test.target.values

    results = {
        "Coin flip": {**scores(y, np.full(len(y), 0.5)), "accuracy": 0.5},
        "Pick the toss winner": scores(y, np.where(test.a_won_toss == 1, 0.55, 0.45)),
        "Pick the chasing team": scores(y, np.where(test.a_bats_second == 1, 0.55, 0.45)),
        "Pick the team in better form": scores(y, np.where(test.form_diff > 0, 0.55, np.where(test.form_diff < 0, 0.45, 0.5))),
    }

    logit = make_pipeline(StandardScaler(), LogisticRegression(C=0.5))
    logit.fit(train[feats], train.target)
    results["Logistic regression"] = scores(y, logit.predict_proba(test[feats])[:, 1])

    gbm = HistGradientBoostingClassifier(max_depth=3, learning_rate=0.05, max_iter=150, random_state=7)
    gbm.fit(train[feats], train.target)
    results["Gradient boosting"] = scores(y, gbm.predict_proba(test[feats])[:, 1])

    coefs = dict(zip(feats, np.round(logit[-1].coef_[0], 3)))
    live = chase_model()
    out = {
        "train_matches": int(len(train)),
        "test_matches": int(len(test)),
        "test_seasons": f"{TEST_FROM}-{int(df.season.max())}",
        "results": results,
        "logistic_coefficients": {k: float(v) for k, v in coefs.items()},
        "live_chase_model": live,
    }
    with open(os.path.join(ROOT, "outputs", "model_results.json"), "w") as f:
        json.dump(out, f, indent=2)

    print(f"Train {len(train)} matches, test {len(test)} matches ({out['test_seasons']})\n")
    print(f"{'Approach':32} {'Accuracy':>9} {'Log loss':>9} {'Brier':>7} {'AUC':>6}")
    for k, v in results.items():
        print(f"{k:32} {v['accuracy']:>9} {v['log_loss']:>9} {v['brier']:>7} {v['auc']:>6}")
    print("\nLogistic regression coefficients (standardised):", coefs)
    print("\nLive chase model (test 2023 onwards):", json.dumps(live["by_stage"], indent=1))
    print("\nRetrain check:", json.dumps(live["retrain_check"], indent=1))


if __name__ == "__main__":
    main()
