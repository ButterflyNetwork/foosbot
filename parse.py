import re

import core
import loldb

mention = "<@(?P<user>\w+)>"
rank_command    = r"rank.*"
stats_command   = r"stats?(?P<who>.*)"
results_command = r"results? (?P<who>.*)\s(?P<score1>\d{1,2})\s?-\s?(?P<score2>\d{1,2})"
predict_command = r"predict (?P<who>.*)"
delete_command  = r"delete (?P<what>.*)"
help_command = r"help"

help_message = """Basic usage:
    - In a public channel (like #foosball), use `@foosbot command`
    - You can also private message foosbot, and just put `command` (i.e., no @foosbot)
```
Commands:
    rank
        - Show the ranked listing of all players.
    stats [<player> <player>]
        - View basic stats (including a graph!) for one or more players.
        - If you don't specify a user, your own stats are given.
    result <player> [<player>] vs <player> [<player>]
        - Submit the result of a match with one or two players on each side.
    predict <player> [<player>] vs <player> [<player>]
        - Predict the result of a match with one or more players on each side.
    delete <match_id>
        - Delete an erroneously submitted match, using the match ID from the submission.
```"""

def get_teams(s):
    return re.split('vs', s, maxsplit=1)

def users_in(s):
    return re.findall(mention, s)

def users_in_teams(s):
    return [users_in(team) for team in get_teams(s)]


def on_message(slack, config, message):
    # Respond to all types of messages.
    channel_id = message['channel']
    if channel_id[0] in ['C', 'G']:
        # Channel/group message, make sure foosbot is being addressed.
        if not re.search("<@{}>".format(config['bot_id']), message['text']):
            return
        pass
    sender = message['user']
    text = message['text'].lower()

    context = core.Context(slack=slack,
                           channel=channel_id,
                           sender=sender,
                           bot_id=config['bot_id'],
                           users=config['users'],
                           matches=loldb.getmatches())

    # Look for HELP
    matches_help = re.search(help_command, text)
    if matches_help:
        core.reply_with_message(help_message, context)

    # Look for RANK
    matches_rank = re.search(rank_command, text)
    if matches_rank:
        core.rank(context)
        return

    # Look for STATS
    matches_stats = re.search(stats_command, text)
    if matches_stats:
        core.stats(users=users_in(matches_stats.group('who')), context=context)
        return

    # Look for RESULTS
    matches_results = re.search(results_command, text)
    if matches_results:
        core.results(users=users_in_teams(matches_results.group('who')),
                     score1=matches_results.group('score1'),
                     score2=matches_results.group('score2'),
                     context=context)
        return

    # Look for PREDICT
    matches_predict = re.search(predict_command, text)
    if matches_predict:
        core.predict(users=users_in_teams(matches_predict.group('who')), context=context)
        return

    # Look for DELETE
    matches_delete = re.search(delete_command, text)
    if matches_delete:
        core.delete(game_id=matches_delete.group('what'), context=context)


