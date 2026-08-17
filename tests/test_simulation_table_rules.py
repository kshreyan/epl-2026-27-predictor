import sys
from pathlib import Path

import numpy as np

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))
from src.simulation.simulate_full_season import build_tables, rank_teams, weighted_position_percentile  # noqa: E402


def test_build_tables_awards_correct_points_and_goal_difference():
    # Two matches, one sim: TeamA 2-0 TeamB (home), TeamB 1-1 TeamA (away)
    home_goals = np.array([[2, 1]])
    away_goals = np.array([[0, 1]])
    home_idx = np.array([0, 1])  # match0 home=TeamA(0), match1 home=TeamB(1)
    away_idx = np.array([1, 0])  # match0 away=TeamB(1), match1 away=TeamA(0)

    points, goal_diff, goals_for = build_tables(home_goals, away_goals, home_idx, away_idx, n_teams=2)

    # TeamA (idx 0): won match0 3pts, drew match1 1pt = 4pts; GF=2+1=3, GA=0+1=1, GD=2
    # TeamB (idx 1): lost match0 0pts, drew match1 1pt = 1pt; GF=0+1=1, GA=2+1=3, GD=-2
    assert points[0, 0] == 4
    assert points[0, 1] == 1
    assert goal_diff[0, 0] == 2
    assert goal_diff[0, 1] == -2
    assert goals_for[0, 0] == 3
    assert goals_for[0, 1] == 1


def test_rank_teams_orders_by_points_then_goal_diff_then_goals_for():
    teams = ["TeamA", "TeamB", "TeamC"]
    # sim0: A has most points; B and C tie on points but B has better GD
    points = np.array([[9, 6, 6]])
    goal_diff = np.array([[5, 2, 1]])
    goals_for = np.array([[10, 8, 8]])

    positions = rank_teams(points, goal_diff, goals_for, teams)
    assert positions[0, 0] == 1  # TeamA: most points -> 1st
    assert positions[0, 1] == 2  # TeamB: tied points, better GD -> 2nd
    assert positions[0, 2] == 3  # TeamC: tied points, worse GD -> 3rd


def test_rank_teams_breaks_full_tie_alphabetically():
    teams = ["Zeta", "Alpha", "Mid"]
    points = np.array([[10, 10, 10]])
    goal_diff = np.array([[0, 0, 0]])
    goals_for = np.array([[5, 5, 5]])

    positions = rank_teams(points, goal_diff, goals_for, teams)
    # Fully tied on points/GD/GF -> alphabetical: Alpha, Mid, Zeta
    alpha_pos = positions[0, teams.index("Alpha")]
    mid_pos = positions[0, teams.index("Mid")]
    zeta_pos = positions[0, teams.index("Zeta")]
    assert alpha_pos < mid_pos < zeta_pos


def test_rank_teams_produces_a_valid_permutation_per_simulation():
    rng = np.random.default_rng(0)
    n_sims, n_teams = 50, 20
    teams = [f"Team{i:02d}" for i in range(n_teams)]
    points = rng.integers(0, 100, size=(n_sims, n_teams))
    goal_diff = rng.integers(-50, 50, size=(n_sims, n_teams))
    goals_for = rng.integers(0, 120, size=(n_sims, n_teams))

    positions = rank_teams(points, goal_diff, goals_for, teams)
    for sim in range(n_sims):
        assert sorted(positions[sim].tolist()) == list(range(1, n_teams + 1))


def test_weighted_position_percentile_basic():
    # All probability mass on position 1 -> every percentile is position 1
    pos_probs = np.array([1.0] + [0.0] * 19)
    assert weighted_position_percentile(pos_probs, 0.5) == 1
    assert weighted_position_percentile(pos_probs, 0.95) == 1

    # Uniform distribution over 20 positions -> median should be mid-table
    pos_probs = np.full(20, 1 / 20)
    median = weighted_position_percentile(pos_probs, 0.5)
    assert 8 <= median <= 12
