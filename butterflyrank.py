import collections
import datetime

import loldb


def get_all_players(matches):
    # collects UIDs for any player to have played in a match
    allp = [m.players1 + m.players2 for m in matches]
    return list(set([x for y in allp for x in y]))


def get_rankings(matches):

    players = get_all_players(matches)

    num_matches = collections.defaultdict(float)
    num_wins = collections.defaultdict(float)
    num_goals = collections.defaultdict(float)
    latest_match = collections.defaultdict(lambda: datetime.datetime(1900, 1, 1))
    score_a = collections.defaultdict(float)  # A: win / total games
    score_b = collections.defaultdict(float)  # B: # goals / total possible
    score_c = collections.defaultdict(float)  # C: average of A+B for all opponents played
    temporal_decay = collections.defaultdict(float)  # Td: temporal decay
    sum_ab = collections.defaultdict(float)  # sum A + B
    num_ab = collections.defaultdict(float)  # num AB

    # Final Score = (4A + 4B + C) * Td
    # (max score = 10)

    for m in matches:
        # count matches played and keep track of latest game played
        for p in m.players1 + m.players2:
            num_matches[p] += 1
            if m.when > latest_match[p]:
                latest_match[p] = m.when

        # count wins
        if m.score1 > m.score2:
            for p in m.players1:
                num_wins[p] += 1
        else:
            for p in m.players2:
                num_wins[p] += 1

        # count goals
        for p in m.players1:
            num_goals[p] += m.score1
        for p in m.players2:
            num_goals[p] += m.score2

    # compute A and B scores
    for p in players:
        score_a[p] = num_wins[p] / num_matches[p]
        score_b[p] = num_goals[p] / (10.0 * num_matches[p])

    # compute C score
    for m in matches:
        for p1 in m.players1:
            for p2 in m.players2:
                sum_ab[p1] += (score_a[p2] + score_b[p2])
                num_ab[p1] += 1
        for p2 in m.players2:
            for p1 in m.players1:
                sum_ab[p2] += (score_a[p1] + score_b[p1])
                num_ab[p2] += 1
    for p in players:
        score_c[p] = sum_ab[p] / num_ab[p]

    # compute temporal decay and final score
    score_final = collections.defaultdict(float)
    for p in players:
        temporal_decay[p] = 0.999 ** float((datetime.datetime.now() - latest_match[p]).days)
        score_final[p] = (4.0 * score_a[p] + 4.0 * score_b[p] + score_c[p]) * temporal_decay[p]

    # organized uids and scores
    scores_by_player = [0] * len(players)
    for i, p in enumerate(players):
        scores_by_player[i] = score_final[p]

    return {k: v for k, v in zip(players, scores_by_player)}

def generate_prediction(ranking, players1, players2):
    m = loldb.getmatches()
    d = get_rankings(m)

    players1 = []
    while len(args) > 0 and args[0].startswith('<@'):
        players1.append(args.pop(0)[2:-1])

    if len(args) == 0:
        return simpleResp("Was expecting a 'vs' at some point")

    args.pop(0)

    players2 = []
    while len(args) > 0 and args[0].startswith('<@'):
        players2.append(args.pop(0)[2:-1])

    r1 = []
    r2 = []
    for p in players1:
        if not p in d:
            return simpleResp("I don't know the rank of <@%s>" % p)
        r1.append(d[p])

    for p in players2:
        if not p in d:
            return simpleResp("I don't know the rank of <@%s>" % p)
        r2.append(d[p])

    sd = numpy.mean(r2) - numpy.mean(r1)

    pred = ranking.generatePrediction(sd, 10000)

    line1 = "I predict team 2 has a %.0f%% chance of winning" % (pred[0] * 100.0)
    line2 = "The most likely outcome is %i - %i (%.0f%% chance)" % \
            (pred[1][0], pred[1][1], pred[2] * 100.0)

    return simpleResp('\n'.join([line1, line2]))
