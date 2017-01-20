from collections import namedtuple
import datetime

import eloranking
import loldb


# Because of how pickling works, it will be very, very annoying to change this type.
class Match():
    def __init__(self, players1=None, players2=None, score1=None, score2=None, when=None):
        self.players1 = players1
        self.players2 = players2
        self.score1 = score1
        self.score2 = score2
        self.when = when
        

Context = namedtuple('Context',
                    ['channel', 'sender', 'slack', 'bot_id', 'users', 'matches'])


def get_name(uid, users):
    matches = filter(lambda x: x['id'] == uid.upper(), users)
    if matches:
        return matches[0]['name']
    return None


def reply_with_message(text, context, fixed_width=False):
    context.slack.chat.post_message(channel=context.channel,
                                    text=text if not fixed_width else '```{}\n```'.format(text),
                                    as_user=True)


def reply_with_file(file, context):
    reply = context.slack.files.upload(file, channels=context.channel)


def rank(context):
    elos = eloranking.get_rankings(context.matches)
    elos = sorted(elos.items(), key=lambda x: x[1], reverse=True)
    uids, scores = zip(*elos)
    ranks = range(1, len(elos) + 1)
    wins, losses = eloranking.get_ws_ls(context.matches, uids)

    n = lambda u: get_name(u, context.users)
    longest_name = max(map(len, map(n, uids)))
    rankFmt = lambda u,s,r,w,l: "{r:>3}. {u:<{ln}}  {s}  {w:>2} - {l:>2}".format(u=u,r=r,s=s,w=w,l=l,ln=longest_name)
    result_str = '\n'.join([rankFmt(*x) for x in zip(*[map(n, uids), scores, ranks, wins, losses])])
    reply_with_message(result_str, context, fixed_width=True)


def stats(users, context):
    if users == []:
        users = [context.sender]

    # Would like to do all users at once, but not currently supported.
    for u in users:
        u = u.upper()
        name = get_name(u, context.users)

        elos = eloranking.compile_histories(context.matches)[u]
        wins, losses = eloranking.get_ws_ls(context.matches, [u])
        fig_file = eloranking.get_stats_graph(context.matches, u, name)
        reply_with_file(fig_file, context)

        message = "Stats for {} since {}\n".format(name, elos[1][0].strftime("%b %-d %Y"))
        message += "-" * len(message) + "\n"
        message += "Current score: {}\n".format(elos[0][-1])
        message += "Win-Loss Record: {}-{}\n".format(wins[0], losses[0])
        last_game = loldb.getlastgame(u)
        n = lambda u: get_name(u, context.users)
        last_game = "{} vs {}: {} - {}".format(' and '.join(map(n, last_game.players1)),
                                               ' and '.join(map(n, last_game.players2)),
                                               last_game.score1,
                                               last_game.score2)
        message += "Last match: {}\n".format(last_game)

        reply_with_message(message, context, fixed_width=True)


def results(users, score1, score2, context):
    match = Match(players1=map(lambda x: x.upper(), users[0]),
                  players2=map(lambda x: x.upper(), users[1]),
                  score1=int(score1),
                  score2=int(score2),
                  when=datetime.datetime.now())
    game_id = loldb.addmatch(match)
    reply_with_message("Match {} submitted.".format(game_id), context)
    rank(context)


def predict(users, context):
    n = lambda u: get_name(u, context.users)
    odds_statement = "a {:.1f}% chance of beating "
    singles_winner = "{} has "
    doubles_winner = "{} and {} have "
    singles_loser = "{}."
    doubles_loser = "{} and {}."

    def predict_fmt(winners, odds, losers):
        if len(winners) > 1:
            m = doubles_winner.format(*map(n, winners))
        else:
            m = singles_winner.format(n(winners[0]))
        m += odds_statement.format(odds)
        if len(losers) > 1:
            m += doubles_loser.format(*map(n, losers))
        else:
            m += singles_loser.format(n(losers[0]))
        return m

    team_a = map(lambda x: x.upper(), users[0])
    team_b = map(lambda x: x.upper(), users[1])
    prediction = eloranking.predict_winner(context.matches, team_a, team_b)
    reply_with_message(predict_fmt(*prediction), context)


def delete(game_id, context):
    loldb.deletematch(game_id)
    reply_with_message("Match deleted.", context)

