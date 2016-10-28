import itertools
import math

base_K = 100

def get_all_players(matches):
    # collects UIDs for any player to have played in a match
    allp = [m.players1 + m.players2 for m in matches]
    return list(set([x for y in allp for x in y]))


def adjusted_K(differential):
    return math.log(abs(differential) + 1) * base_K


def expected_point_percentages(elo_a, elo_b):
    a = 1.0 / (1.0 + 10.0**(float(elo_b - elo_a) / 400.0))
    b = 1.0 / (1.0 + 10.0**(float(elo_a - elo_b) / 400.0))
    return (a, b)


def elo_update(winner_elo, loser_elo, winner_score, loser_score):
    winner_expected, loser_expected = expected_point_percentages(winner_elo, loser_elo)
    assert(0.999 <= winner_expected + loser_expected <= 1.001)

    winner_actual = float(winner_score) / (winner_score + loser_score)
    loser_actual = float(loser_score) / (winner_score + loser_score)
    assert(0.999 <= winner_actual + loser_actual <= 1.001)

    K = adjusted_K(winner_score - loser_score)
    adjustment = K * (winner_actual - winner_expected)

    winner_elo += adjustment
    loser_elo -= adjustment
    # 0.5's are just to round to nearest int, rather than just down
    return (int(winner_elo+0.5), int(loser_elo+0.5))


def get_rankings(matches):
    # Assign everyone an initial score of 1500
    rankings = {player: 1500 for player in get_all_players(matches)}

    # Parse through all games and update elo of each player for each game
    for match in matches:
        # Find winner/loser scores
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

def get_ws_ls(matches, players):
    records = {p:[0,0] for p in players}
    for match in matches:
        if match.score1 > match.score2:
            winners, losers = match.players1, match.players2
        else:
            winners, losers = match.players2, match.players1
        for p in winners:
            if p in records:
                records[p][0] += 1
        for p in losers:
            if p in records:
                records[p][1] += 1
    return zip(*[records[p] for p in players])



def predict_winner(matches, pl_a, pl_b):
    rankings = get_rankings(matches)
    print("Rankings collected")
    expected_a, expected_b = expected_point_percentages(rankings[pl_a], rankings[pl_b])
    print(expected_a, expected_b)
    if expected_a > expected_b:
        return (pl_a, expected_a * 100, pl_b)
    else:
        return (pl_b, expected_b * 100, pl_a)

