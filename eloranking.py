import math
from datetime import datetime
import matplotlib.pylab as plt
import matplotlib.dates as mdates

base_K = 70

def get_all_players(matches):
    # collects UIDs for any player to have played in a match
    allp = [m.players1 + m.players2 for m in matches]
    return list(set([x for y in allp for x in y]))

def expected(elo_a, elo_b):
    return 1.0 / (1.0 + 10**(float(elo_b - elo_a) / 400))

def day_before(x):
    return datetime(x.year, x.month, x.day - 1, x.hour, x.minute, x.second)

def compile_histories(matches):
    histories = {}
    for match in sorted(matches, key=lambda m: m.when):
        # Find winner/loser scores
        if match.score1 > match.score2:
            winners, losers = match.players1, match.players2
            win_score, lose_score = match.score1, match.score2
        else:
            winners, losers = match.players2, match.players1
            win_score, lose_score = match.score2, match.score1

        # Add a 0-entry to histories if player hasn't played yet.
        for p in winners + losers:
            if p not in histories:
                histories[p] = ([1500], [day_before(match.when)])

        # Calculate average elos for winning and losing team
        win_elo = sum([histories[p][0][-1] for p in winners]) / len(winners)
        lose_elo = sum([histories[p][0][-1] for p in losers]) / len(losers)

        # Calculate new elos and add to histories lists
        for p in winners + losers:
            histories[p][1].append(match.when)
            # Effectively, the probability of player p winning has collapsed to either 0 or 1,
            # and we're comparing that with the elo-calculated probability of winning.
            prob_of_winning = expected(win_elo, lose_elo) if p in winners else expected(lose_elo, win_elo)
            histories[p][0].append( histories[p][0][-1]
                                    + int(base_K * ((1.0 if p in winners else 0.0) - prob_of_winning)
                                          + 0.5)) # The 0.5 is just the easiest way to round

    return histories


def get_rankings(matches):
    histories = compile_histories(matches)
    return {p : histories[p][0][-1] for p in histories.keys()}


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


def predict_winner(matches, pls_a, pls_b):
    rankings = get_rankings(matches)
    pl_a_score = sum(map(lambda p: rankings[p], pls_a)) / len(pls_a)
    pl_b_score = sum(map(lambda p: rankings[p], pls_b)) / len(pls_b)

    prob_of_a_winning = expected(pl_a_score, pl_b_score)
    if (prob_of_a_winning > 0.5):
        return (pls_a, prob_of_a_winning * 100, pls_b)
    return (pls_b, (1.0 - prob_of_a_winning) * 100, pls_a)


def get_stats_graph(matches, player_uids, player_names):
    # Get personal history:
    histories = compile_histories(matches)

    # Basic plot setup
    fig = plt.figure()
    ax = plt.subplot()
    # Add the history data
    for p in player_uids:
        ax.plot(histories[p][1], histories[p][0], marker='*')
    # Do the rest of the plot logistics/formatting
    ax.xaxis.set_major_locator(mdates.AutoDateLocator(minticks=5, maxticks=10))
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%b %-d')) # this is short month name, day
    locs, labels = plt.xticks()
    plt.setp(labels, rotation=25)
    plt.axhline(y=1500, color='black')

    # Save the file
    filename = "/tmp/foosfigs/{}-stats.png".format('-'.join(player_names))
    plt.savefig(filename, bbox_inches='tight', pad_inches=0.25)
    return filename



