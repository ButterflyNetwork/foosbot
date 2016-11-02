import itertools
import math

base_K = 70

def get_all_players(matches):
    # collects UIDs for any player to have played in a match
    allp = [m.players1 + m.players2 for m in matches]
    return list(set([x for y in allp for x in y]))


def expected(elo_a, elo_b):
    return 1.0 / (1.0 + 10**(float(elo_b - elo_a) / 400))


def get_rankings(matches):
    # Assign everyone an initial score of 1500
    rankings = {player: 1500 for player in get_all_players(matches)}

    # Parse through all games and update elo of each player for each game
    for match in matches:
        # Find winner/loser scores
        if match.score1 > match.score2:
            winners, losers = match.players1, match.players2
        else:
            winners, losers = match.players2, match.players1

        avg_win_elo = sum([rankings[p] for p in winners]) / len(winners)
        avg_loss_elo = sum([rankings[p] for p in losers]) / len(losers)

        for p in winners + losers:
            # Effectively, the probability of player p winning has collapsed to either 0 or 1,
            # and we're comparing that with the elo-calculated probability of winning.
            prob_of_winning = expected(avg_win_elo, avg_loss_elo) if p in winners else expected(avg_loss_elo, avg_win_elo)
            rankings[p] += int(base_K * ((1.0 if p in winners else 0.0) - prob_of_winning) + 0.5)
            # The 0.5 at the end is just because it's the easiest way to round-to-nearest without numpy.

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

