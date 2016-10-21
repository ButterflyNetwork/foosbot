import itertools
import math

base_K = 60

def get_all_players(matches):
    # collects UIDs for any player to have played in a match
    allp = [m.players1 + m.players2 for m in matches]
    return list(set([x for y in allp for x in y]))


def adjusted_K(differential):
    return math.log(abs(differential) + 1) * base_K


def expected_point_percentages(elo_a, elo_b):
    expected_a = 1.0 / (1 + 10**((elo_b - elo_a) / 400))
    expected_b = 1.0 / (1 + 10**((elo_a - elo_b) / 400))
    return (expected_a, expected_b)


def elo_update(winner_elo, loser_elo, winner_score, loser_score):
    winner_expected, loser_expected = expected_point_percentages(winner_elo, loser_elo)

    winner_actual = winner_score / (winner_score + loser_score)
    loser_actual = loser_score / (winner_score + loser_score)

    K = adjusted_K(winner_score - loser_score)

    winner_elo += K * (winner_actual - winner_expected) + base_K * (winner_actual - 0.5)
    loser_elo += K * (loser_actual - loser_expected) + base_K * (loser_actual - 0.5)
    return (int(winner_elo+0.5), int(loser_elo+0.5))


def get_rankings(matches):
    # Assign everyone an initial score of 1500
    rankings = {player: 1500 for player in get_all_players(matches)}

    # Parse through all games and update elo of each player for each game
    for match in matches:
        if match.score1 > match.score2:
            winners, losers = match.players1, match.players2
            win_score, lose_score = match.score1, match.score2
        else:
            winners, losers = match.players2, match.players1
            win_score, lose_score = match.score2, match.score1

        # Update every pair of players
        for w, l in itertools.product(winners, losers):
            rankings[w], rankings[l] = elo_update(rankings[w], rankings[l], win_score, lose_score)

    return rankings


def predict_winner(matches, pl_a, pl_b):
    rankings = get_rankings(matches)
    expected_a, expected_b = expected_point_percentages(rankings[pl_a], rankings[pl_b])
    if expected_a > expected_b:
        return (pl_a, expected_a * 100, pl_b)
    else:
        return (pl_b, expected_b * 100, pl_a)

