import collections
import datetime


def getAllUids(matches):
    allu = [m.players1 + m.players2 for m in matches]
    return list(set([x for y in allu for x in y]))


def getRanking(matches):

    uids = getAllUids(matches)

    num_matches = collections.defaultdict(float)
    num_wins = collections.defaultdict(float)
    num_goals = collections.defaultdict(float)
    latest_match = collections.defaultdict(lambda: datetime.datetime(1900, 1, 1))
    scoreA = collections.defaultdict(float)  # A: win / total games
    scoreB = collections.defaultdict(float)  # B: # goals / total possible
    scoreC = collections.defaultdict(float)  # C: average of A+B for all opponents played
    tempDecay = collections.defaultdict(float)  # Td: temporal decay
    sumAB = collections.defaultdict(float)  # sum A + B
    numAB = collections.defaultdict(float)  # num AB

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
    for p in num_matches:
        scoreA[p] = num_wins[p] / num_matches[p]
        scoreB[p] = num_goals[p] / (10.0 * num_matches[p])

    # compute C score
    for m in matches:
        for p1 in m.players1:
            for p2 in m.players2:
                sumAB[p1] += (scoreA[p2] + scoreB[p2])
                numAB[p1] += 1
        for p2 in m.players2:
            for p1 in m.players1:
                sumAB[p2] += (scoreA[p1] + scoreB[p1])
                numAB[p2] += 1

    for p in num_matches:
        scoreC[p] = sumAB[p] / numAB[p]

    # compute temporal decay and final score
    scoreFinal = collections.defaultdict(float)
    for p in num_matches:
        tempDecay[p] = 0.999 ** float((datetime.datetime.now() - latest_match[p]).days)
        scoreFinal[p] = (4.0 * scoreA[p] + 4.0 * scoreB[p] + scoreC[p]) * tempDecay[p]




    prank_r = getRankingRaw(matches, uids)
    # This isn't a great line of code, probably improve the whole API for getting rankings?
    return {k: v for k, v in zip(uids, prank_r)}