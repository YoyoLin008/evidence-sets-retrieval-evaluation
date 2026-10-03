"""Tests target scientific risks in new exploratory statistics."""
import sys
from pathlib import Path
import numpy as np
import pytest
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from evidence import score, completion_costs
from analyze import bootstrap_matrix
from revision_v3_statistics import (minimal_family, pruning_check, category,
    summarize, uniform_budget, bootstrap_budgets, threshold_summary, extended_percentile)


def test_nested_duplicate_alternative_pruning_and_f1_counterexample():
    family = [[0], [0], [0, 1], [2]]
    assert minimal_family(family) == [[0], [2]]
    assert pruning_check([0, 1, 2], family, ['one', 'two', 'three']) > 0
    old, new = score([0, 1], [[0], [0, 1]]), score([0, 1], [[0]])
    assert old['complete'] == new['complete'] == 1
    assert old['max_f1'] == 1 and new['max_f1'] == pytest.approx(2 / 3)


def test_four_topologies_and_empty_strata():
    assert [category(g) for g in [[[0], [0]], [[0], [0, 1]], [[0], [1]], [[0], [1], [0, 2]]]] == [0, 1, 2, 3]
    assert summarize([], [])['n'] == 0
    assert summarize([], [])['mean'] is None
    with pytest.raises(ValueError):
        minimal_family([[]])


def test_exact_budget_saturation_and_whole_token_prefix():
    # A short item remains complete after it saturates; a long item remains
    # incomplete until budget 8. Removing the short item changes the answer.
    assert uniform_budget([1, 8, 8], .5) == 8
    assert uniform_budget([1, 8, 8], 1 / 3) == 1
    assert uniform_budget([2, 7], .5, [3, 1]) == 2
    c = completion_costs([0, 1, 2], [[1]], ['a b c d e', 'f g', 'h'])
    assert c['tokens_complete'] == 7
    # Budget 2 cannot skip the first 5-token unit and retrieve the gold unit.
    assert uniform_budget([c['tokens_complete']], 1) == 7


def test_cluster_budget_bootstrap_matches_explicit_cluster_multiplicity():
    clusters = ['a', 'a', 'b', 'c']
    costs = [1, 9, 5, 12]
    boot = bootstrap_matrix(clusters, seed=11, b=37)
    samples = bootstrap_budgets(costs, boot, [.5, .75, .9], batch_size=7)
    ids, counts, draws = boot
    for i, draw in enumerate(draws):
        # Whole clusters induce identical multiplicity for the two a items;
        # item denominator varies and is not number of sampled clusters.
        assert draw[ids[0]] == draw[ids[1]]
        for j, tau in enumerate([.5, .75, .9]):
            explicit = np.repeat(costs, draw[ids])
            assert samples[i, j] == uniform_budget(explicit, tau)
    result = threshold_summary(costs, np.array(costs) + 3, boot, [.5])
    assert result[0]['difference'] == 3
    assert result[0]['difference_lo'] == 3 == result[0]['difference_hi']


def test_unattained_draws_remain_visible_not_conditioned_away():
    boot = bootstrap_matrix(['a', 'b'], seed=5, b=100)
    rows = threshold_summary([1, 1], [2, np.inf], boot, [.9])
    row = rows[0]
    assert row['B_A'] is None and not row['B_A_attained']
    assert row['B_A_unattained_replicates'] > 0
    assert row['difference_undefined_replicates'] == row['B_A_unattained_replicates']
    assert row['difference_lo'] is None and row['difference_hi'] is None
    assert extended_percentile([1, 2, np.inf], .975) == np.inf
    assert np.isnan(extended_percentile([1, np.nan], .5))
