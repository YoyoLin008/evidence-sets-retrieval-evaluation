"""Revision-added exploratory statistics; frozen primary outputs remain read-only.

Replay: python src/revision_v3_statistics.py [--qwen PATH]
A supplied Qwen file must contain the entire original eligible cohort.
"""
from __future__ import annotations
import argparse
from collections import Counter
from dataclasses import asdict
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pandas as pd
from evidence import ROOT, Instance, load_jsonl, score, completion_costs, topology, tokens, digest
from analyze import bootstrap_matrix, estimate, SEED, B, METRICS

STATUS = "revision-added exploratory"
CATEGORIES = ["One distinct set", "Multiple sets, one minimal set", "Multiple minimal sets, no supersets", "Multiple minimal sets plus supersets"]
COST_METRICS = ["depth_complete", "depth_union", "depth_penalty", "tokens_complete", "tokens_union", "tokens_penalty"]
TAUS = [.5, .75, .9]
PAIRS = [("dense", "bm25"), ("qwen3", "bm25"), ("qwen3", "dense")]


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def minimal_family(gold):
    refs = {frozenset(e) for e in gold}
    if not refs or any(not e for e in refs):
        raise ValueError("Evidence families and groups must be nonempty")
    return [sorted(e) for e in sorted(refs, key=lambda e: tuple(sorted(e))) if not any(z < e for z in refs)]


def category(gold):
    t = topology(gold)
    if t["n_distinct_sets"] == 1:
        return 0
    if t["n_minimal_sets"] == 1:
        return 1
    return 2 if t["n_minimal_sets"] == t["n_distinct_sets"] else 3


def pruning_check(order, gold, units=None):
    """Threshold event comparisons imply each property at every integer depth."""
    pruned = minimal_family(gold)
    union = set().union(*map(set, gold))
    small_union = set().union(*map(set, pruned))
    pos = {v: i + 1 for i, v in enumerate(order)}
    old_dC = min(max(pos[v] for v in e) for e in gold)
    new_dC = min(max(pos[v] for v in e) for e in pruned)
    assert small_union <= union
    assert old_dC == new_dC
    assert max(pos[v] for v in small_union) <= max(pos[v] for v in union)
    if units is not None:
        original = completion_costs(order, gold, units)
        new = completion_costs(order, pruned, units)
        assert original["tokens_complete"] == new["tokens_complete"]
        assert new["tokens_union"] <= original["tokens_union"]
    assert min(pos[v] for v in small_union) >= min(pos[v] for v in union)
    # Explicitly check every change point, plus endpoints: all intervening
    # prefixes have identical H/C/A and therefore satisfy the same inequalities.
    events = {0, len(order)}
    for u in union:
        events.add(pos[u])
        events.add(pos[u] - 1)
    for k in sorted(events):
        old, newscore = score(order[:k], gold), score(order[:k], pruned)
        assert old["complete"] == newscore["complete"]
        assert old["hit"] >= newscore["hit"]
        assert old["union_complete"] <= newscore["union_complete"]
        assert old["complete_without_union"] >= newscore["complete_without_union"]
    return len(events)


def summarize(values, clusters):
    if not len(values):
        return {"n": 0, "clusters": 0, "mean": None, "lo": None, "hi": None,
                "median": None, "q25": None, "q75": None, "q90": None,
                "q95": None, "max": None, "zero_fraction": None, "sparse": True}
    values = np.asarray(values, dtype=float)
    m, ci = estimate(values, bootstrap_matrix(clusters))
    return {"n": len(values), "clusters": len(set(clusters)), "mean": float(m[0]),
            "lo": float(ci[0, 0]), "hi": float(ci[0, 1]), "median": float(np.median(values)),
            **{f"q{int(q*100)}": float(np.quantile(values, q)) for q in [.25, .75, .9, .95]},
            "max": float(values.max()), "zero_fraction": float(np.mean(values == 0)),
            "sparse": len(set(clusters)) < 10}


def extended_percentile(values, q):
    """Linear percentile on the extended nonnegative reals, without inf-inf NaNs."""
    values = np.sort(np.asarray(values, dtype=float))
    if len(values) == 0 or np.isnan(values).any():
        return float("nan")
    location = (len(values) - 1) * q
    lo, hi = int(np.floor(location)), int(np.ceil(location))
    if lo == hi or values[lo] == values[hi]:
        return float(values[lo])
    if np.isinf(values[hi]):
        return float("inf")
    return float(values[lo] + (location - lo) * (values[hi] - values[lo]))


def uniform_budget(costs, tau, weights=None):
    """Exact minimum integer budget from full completion times; inf=unattained.

    Positive weights preserve every sampled cluster's multiplicity. Short
    candidate documents saturate; they are never removed from the denominator.
    """
    costs = np.asarray(costs, dtype=float)
    if not 0 < tau <= 1 or len(costs) == 0 or np.isnan(costs).any():
        raise ValueError("A nonempty cost vector and 0 < tau <= 1 are required")
    if weights is None:
        weights = np.ones(len(costs), dtype=np.int64)
    weights = np.asarray(weights)
    if len(weights) != len(costs) or np.any(weights < 0) or weights.sum() <= 0:
        raise ValueError("Weights must match costs and have positive total")
    order = np.argsort(costs, kind="stable")
    # Integer ceiling avoids nearest/linear quantile conventions: this is the
    # first observed cost whose item-weighted CDF attains the requested rate.
    target = int(np.ceil(tau * weights.sum() - 1e-12))
    j = np.searchsorted(np.cumsum(weights[order]), target, side="left")
    return float(costs[order[j]])


def bootstrap_budgets(costs, boot, taus=TAUS, batch_size=128):
    ids, counts, cluster_weights = boot
    costs = np.asarray(costs, dtype=float)
    order = np.argsort(costs, kind="stable")
    ordered_costs = costs[order]
    samples = np.empty((len(cluster_weights), len(taus)), dtype=float)
    for start in range(0, len(cluster_weights), batch_size):
        weights = cluster_weights[start:start+batch_size, ids[order]]
        cumulative = np.cumsum(weights, axis=1)
        denominator = cumulative[:, -1]
        for j, tau in enumerate(taus):
            targets = np.ceil(tau * denominator - 1e-12).astype(np.int64)
            index = np.argmax(cumulative >= targets[:, None], axis=1)
            samples[start:start+len(weights), j] = ordered_costs[index]
    return samples


def finite_or_none(value):
    return float(value) if np.isfinite(value) else None


def threshold_summary(complete, union, boot, taus=TAUS):
    sc = bootstrap_budgets(complete, boot, taus)
    sa = bootstrap_budgets(union, boot, taus)
    results = []
    for j, tau in enumerate(taus):
        bc, ba = uniform_budget(complete, tau), uniform_budget(union, tau)
        attainable = np.isfinite(sc[:, j]) & np.isfinite(sa[:, j])
        diffs = np.full(len(sc), np.nan)
        diffs[attainable] = sa[attainable, j] - sc[attainable, j]
        # Do not condition a claimed interval on attained-only replicates.
        # An undefined paired gap in any draw makes the ordinary paired gap
        # interval unreported; unattained endpoint counts remain visible.
        row = {"tau": tau, "B_C": finite_or_none(bc), "B_A": finite_or_none(ba),
               "difference": finite_or_none(ba - bc) if np.isfinite(bc) and np.isfinite(ba) else None,
               "B_C_attained": bool(np.isfinite(bc)), "B_A_attained": bool(np.isfinite(ba)),
               "bootstrap_replicates": len(sc), "B_C_unattained_replicates": int(np.isinf(sc[:, j]).sum()),
               "B_A_unattained_replicates": int(np.isinf(sa[:, j]).sum()),
               "difference_undefined_replicates": int((~attainable).sum())}
        for endpoint, sample in [("B_C", sc[:, j]), ("B_A", sa[:, j]), ("difference", diffs)]:
            for suffix, q in [("lo", .025), ("hi", .975)]:
                bound = extended_percentile(sample, q)
                row[f"{endpoint}_{suffix}"] = finite_or_none(bound)
                row[f"{endpoint}_{suffix}_unattained"] = bool(np.isinf(bound))
        results.append(row)
    return results


def export(out, name, rows):
    pd.DataFrame(rows).to_csv(out / f"{name}.csv", index=False, float_format="%.12g")


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--instances", type=Path, default=ROOT / "outputs/main_v1/instances.jsonl")
    parser.add_argument("--rankings", type=Path, default=ROOT / "reference_outputs/main_v1/rankings.jsonl")
    parser.add_argument("--rankings-only", action="store_true", help="Rebuild statistical tables using archived rankings and saved lexical costs, without source text")
    parser.add_argument("--qwen", type=Path, help="Optional complete 1,084-row Qwen ranking file")
    parser.add_argument("--output", type=Path, default=ROOT / "revisions/v3/statistics")
    args = parser.parse_args(argv)
    out = args.output
    out.mkdir(parents=True, exist_ok=True)
    protocol = out / "protocol.md"
    if not protocol.exists():
        raise ValueError("Freeze the revision statistics protocol in output/protocol.md before analysis")
    start = datetime.now(timezone.utc).isoformat()
    config = json.loads((ROOT / "configs/main_v1.json").read_text())
    methods = config["methods"][:]
    raw = load_jsonl(args.rankings)
    if args.rankings_only:
        # Metadata, evidence families and completion costs are in the archived
        # ranking rows. Source-text cost recomputation is a separate check.
        xs = [SimpleNamespace(dataset=r["dataset"], id=r["id"], cluster=r["cluster"],
                              gold=r["gold"], metadata=r["metadata"],
                              unit_count=r["unit_count"], instance_hash=r["instance_hash"])
              for r in raw if r["method"] == "bm25"]
    else:
        xs = [Instance(**r) for r in load_jsonl(args.instances)]
    assert len(xs) == len({(x.dataset, x.id) for x in xs}) == 1084 and len(raw) == 5420
    if args.qwen:
        extra = load_jsonl(args.qwen)
        if len(extra) != len(xs) or {r["method"] for r in extra} != {"qwen3"}:
            raise ValueError("Qwen must be a complete 1,084-row run; partial effectiveness is not analyzed")
        raw += extra
        methods.append("qwen3")
    lookup = {(r["dataset"], r["id"], r["method"]): r for r in raw}
    assert len(lookup) == len(raw) == len(xs) * len(methods)
    assert set(lookup) == {(x.dataset, x.id, method) for x in xs for method in methods}, "Candidate item/method universe mismatch"
    curves, costs_out, distribution, budgets, sensitivity, contrasts, item_rows, subgroup_membership = ([] for _ in range(8))
    validation = {"status": STATUS, "ranking_rows": len(raw), "scoring_points": sum(len(r["points"]) for r in raw),
                  "original_ranking_rows": 5420, "original_scoring_points": 32520, "methods": methods,
                  "replicates": B, "seed": SEED, "checks": {}, "pruning_event_checks": 0}
    for dataset, primary in [("qasper", 5), ("scifact", 3)]:
        dx = sorted([x for x in xs if x.dataset == dataset], key=lambda x: x.id)
        clusters = [x.cluster for x in dx]
        boot = bootstrap_matrix(clusters)
        assert len(dx) == (875 if dataset == "qasper" else 209)
        assert len(set(clusters)) == (367 if dataset == "qasper" else 164)
        counts = Counter(category(x.gold) for x in dx)
        assert [counts[i] for i in range(4)] == ([403, 187, 243, 42] if dataset == "qasper" else [124, 0, 85, 0])
        validation["checks"][dataset] = {"n": len(dx), "clusters": len(set(clusters)), "topology_counts": [counts[i] for i in range(4)]}
        if dataset == "qasper":
            for x in dx:
                assert x.metadata["answer_agreement"] == (len(set(x.metadata["answer_keys"])) == 1)
            agreed = [x for x in dx if x.metadata["answer_agreement"]]
            other = [x for x in dx if not x.metadata["answer_agreement"]]
            agreed_papers, other_papers = {x.cluster for x in agreed}, {x.cluster for x in other}
            assert len(agreed) == 195 and len(agreed_papers) == 149
            validation["checks"][dataset]["answer_groups"] = {
                "agreement_items": len(agreed), "agreement_papers": len(agreed_papers),
                "complement_items": len(other), "complement_papers": len(other_papers),
                "papers_shared_across_subsets": len(agreed_papers & other_papers),
                "rule": "all saved adapter-normalized answer strings exactly equal"}
        for x in dx:
            subgroup_membership.append({"dataset": dataset, "id": x.id, "cluster": x.cluster,
                                        "exact_answer_agreement": bool(x.metadata["answer_agreement"]),
                                        "topology": category(x.gold), "topology_label": CATEGORIES[category(x.gold)]})
        method_points, method_costs = {}, {}
        for method in methods:
            rows = [lookup[dataset, x.id, method] for x in dx]
            points, costs = [], []
            for x, r in zip(dx, rows):
                order = r["ranking"]
                unit_count = x.unit_count if args.rankings_only else len(x.units)
                assert len(order) == unit_count and sorted(order) == list(range(unit_count))
                assert r["cluster"] == x.cluster and r["gold"] == x.gold
                assert r["instance_hash"] == (x.instance_hash if args.rankings_only else digest(asdict(x)))
                assert x.gold and all(x.gold)
                assert all(0 <= u < unit_count for group in x.gold for u in group)
                computed_cost = r["costs"] if args.rankings_only else completion_costs(order, x.gold, x.units)
                position = {v: i + 1 for i, v in enumerate(order)}
                depths = [max(position[v] for v in e) for e in x.gold]
                assert computed_cost["depth_complete"] == min(depths)
                assert computed_cost["depth_union"] == max(depths)
                assert computed_cost["depth_penalty"] == max(depths) - min(depths)
                assert computed_cost["tokens_union"] >= computed_cost["tokens_complete"] > 0
                assert computed_cost["tokens_penalty"] == computed_cost["tokens_union"] - computed_cost["tokens_complete"]
                assert computed_cost == r["costs"]
                costs.append(computed_cost)
                assert sorted(p["k"] for p in r["points"]) == sorted(config["ks"]), "Missing, duplicate, or unexpected original scoring budget"
                computed = {k: score(order[:k], x.gold) for k in config["ks"]}
                for saved in r["points"]:
                    assert all(np.isclose(computed[saved["k"]][m], saved[m], atol=1e-13, rtol=0) for m in METRICS)
                if category(x.gold) == 0:
                    assert all(p["complete"] == p["union_complete"] for p in computed.values())
                points.append(computed)
                validation["pruning_event_checks"] += pruning_check(order, x.gold, None if args.rankings_only else x.units)
                item_rows.append({"dataset": dataset, "method": method, "id": x.id, "cluster": x.cluster,
                                  "unit_count": unit_count, **{field: computed_cost[field] for field in COST_METRICS}, "status": STATUS})
            method_points[method], method_costs[method] = points, costs
            for k in config["ks"]:
                values = [[p[k][m] for m in METRICS] for p in points]
                means, intervals = estimate(values, boot)
                for metric, mean, ci in zip(METRICS, means, intervals):
                    curves.append({"dataset": dataset, "method": method, "k": k, "primary": k == primary,
                                   "n": len(dx), "clusters": len(set(clusters)), "metric": metric,
                                   "mean": mean, "lo": ci[0], "hi": ci[1], "status": STATUS})
            for metric in COST_METRICS:
                values = np.asarray([c[metric] for c in costs])
                costs_out.append({"dataset": dataset, "method": method, "metric": metric,
                                  **summarize(values, clusters), "status": STATUS})
                if metric.endswith("penalty"):
                    zero_mean, zero_ci = estimate((values == 0).astype(int), boot)
                    for subset, ix in [("all", np.arange(len(dx))), ("positive_cost", np.flatnonzero(values > 0))]:
                        distribution.append({"dataset": dataset, "method": method, "metric": metric, "subset": subset,
                                             **summarize(values[ix], [clusters[i] for i in ix]),
                                             "overall_n": len(dx), "affected_n": int(np.sum(values > 0)),
                                             "overall_zero_fraction": zero_mean[0], "overall_zero_lo": zero_ci[0, 0],
                                             "overall_zero_hi": zero_ci[0, 1], "status": STATUS})
            for unit, cfield, afield in [("units", "depth_complete", "depth_union"), ("lexical_tokens", "tokens_complete", "tokens_union")]:
                complete, union = ([c[field] for c in costs] for field in [cfield, afield])
                for row in threshold_summary(complete, union, boot):
                    budgets.append({"dataset": dataset, "method": method, "budget_unit": unit,
                                    "n": len(dx), "clusters": len(set(clusters)), **row,
                                    "definition": "exact minimum integer budget; full rankings; all-item denominator", "status": STATUS})
            if dataset == "qasper":
                base = np.asarray([p[primary]["complete_without_union"] for p in points])
                pruned = np.asarray([score(r["ranking"][:primary], minimal_family(x.gold))["complete_without_union"] for x, r in zip(dx, rows)])
                for group, ix in [("exact_answer_agreement", [i for i, x in enumerate(dx) if x.metadata["answer_agreement"]]),
                                  ("agreement_complement", [i for i, x in enumerate(dx) if not x.metadata["answer_agreement"]]),
                                  ("full", list(range(len(dx))))]:
                    cs = [clusters[i] for i in ix]
                    sb = bootstrap_matrix(cs)
                    a = np.column_stack([base[ix], pruned[ix], pruned[ix] - base[ix]])
                    means, intervals = estimate(a, sb)
                    row = {"dataset": dataset, "method": method, "k": primary, "group": group, "n": len(ix),
                           "papers": len(set(cs)), "weight": len(ix) / len(dx), "status": STATUS}
                    for label, mean, ci in zip(["original_gap", "pruned_gap", "pruned_minus_original"], means, intervals):
                        row.update({label: mean, f"{label}_lo": ci[0], f"{label}_hi": ci[1]})
                    for c in range(4):
                        row[f"topology_{c}_n"] = sum(category(dx[i].gold) == c for i in ix)
                    sensitivity.append(row)
                subrows = [r for r in sensitivity if r["method"] == method]
                for field in ["original_gap", "pruned_gap", "pruned_minus_original"]:
                    assert np.isclose(sum(r["weight"] * r[field] for r in subrows if r["group"] != "full"), next(r[field] for r in subrows if r["group"] == "full"), atol=1e-15)
        bm = method_points["bm25"]
        categories = Counter("no_hit" if not p[primary]["hit"] else "partial" if not p[primary]["complete"] else "one_not_union" if not p[primary]["union_complete"] else "union" for p in bm)
        observed = [categories[k] for k in ["no_hit", "partial", "one_not_union", "union"]]
        assert observed == ([306, 123, 156, 290] if dataset == "qasper" else [34, 9, 58, 108])
        validation["checks"][dataset]["historical_BM25_categories"] = observed
        for left, right in PAIRS:
            if left not in methods:
                continue
            for k in config["ks"]:
                for metric in ["complete", "union_complete", "max_f1", "union_f1", "complete_without_union", "C_advantage_minus_A_advantage"]:
                    m = "complete_without_union" if metric == "C_advantage_minus_A_advantage" else metric
                    differences = [a[k][m] - b[k][m] for a, b in zip(method_points[left], method_points[right])]
                    mean, ci = estimate(differences, boot)
                    contrasts.append({"dataset": dataset, "method_left": left, "method_right": right, "k": k,
                                      "primary": k == primary, "metric": metric, "n": len(dx), "clusters": len(set(clusters)),
                                      "mean_difference": mean[0], "lo": ci[0, 0], "hi": ci[0, 1],
                                      "status": STATUS, "inference": "pointwise descriptive interval; no multiplicity-controlled claim"})
    # Counterexample retained in the validation record, not a claim of F1 invariance.
    old_f1, new_f1 = score([0, 1], [[0], [0, 1]])["max_f1"], score([0, 1], [[0]])["max_f1"]
    assert old_f1 == 1 and np.isclose(new_f1, 2 / 3)
    validation["best_reference_F1_counterexample"] = {"family": [[0], [0, 1]], "prefix": [0, 1], "original": old_f1, "pruned": new_f1}
    validation["checks"].update({"valid_permutations": True, "frozen_score_depth_replay": True, "source_text_lexical_cost_replay": not args.rankings_only,
                                "pruning_all_integer_prefixes_via_event_depths": True,
                                "answer_subgroup_weighted_reconstruction": True,
                                "full_cohort_thresholds_all_attained": all(r["B_C_attained"] and r["B_A_attained"] and r["difference_undefined_replicates"] == 0 for r in budgets)})
    validation["Qwen_status"] = "full cohort included" if args.qwen else "not included; no partial rankings inspected"
    for name, data in [("curves", curves), ("costs", costs_out), ("cost_distributions", distribution),
                       ("budget_thresholds", budgets), ("agreement_pruning", sensitivity),
                       ("method_contrasts", contrasts), ("item_completion_costs", item_rows), ("cohort_membership", subgroup_membership)]:
        export(out, name, data)
    export(out, "primary", [r for r in curves if r["primary"]])
    (out / "validation.json").write_text(json.dumps(validation, indent=2) + "\n")
    manifest = {"started_utc": start, "finished_utc": datetime.now(timezone.utc).isoformat(), "status": STATUS,
                "protocol_sha256": sha(protocol), "source_sha256": sha(__file__),
                "input_sha256": {**({"instances": sha(args.instances)} if not args.rankings_only else {}), "original_rankings": sha(args.rankings),
                                 **({"qwen_rankings": sha(args.qwen)} if args.qwen else {})},
                "mode": "archived rankings and costs only" if args.rankings_only else "source-text score/cost verification and statistics",
                "bootstrap": {"replicates": B, "seed": SEED, "unit": "original connected clusters", "weighting": "item-weighted after whole-cluster resampling", "interval": "pointwise 95% percentile, linear interpolation"},
                "outputs": {p.name: sha(p) for p in sorted(out.glob("*.csv"))}, "validation_sha256": sha(out / "validation.json")}
    (out / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print(json.dumps(validation, indent=2))
    print(pd.DataFrame(sensitivity).query("method == 'bm25'").to_string(index=False))
    print(pd.DataFrame(budgets).query("method == 'bm25'").to_string(index=False))


if __name__ == "__main__":
    main()
