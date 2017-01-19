import json
import traceback
import sys
import datetime

import butterflyrank
import eloranking
import core
import loldb

_nextid = 1


def simpleMsg(text):
    global _nextid
    m = {'type': 'message', 'id': _nextid, 'text': text}
    _nextid += 1
    return m


def simpleResp(text):
    return [simpleMsg(text)]

def processSubmit(slack, args):
    p1 = []
    p2 = []
    try:
        a1 = args.pop(0)
        if not a1.startswith("<@"):
            return simpleResp("Didn't recognise user %s" % (a1))
        p1.append(a1[2:-1])

        a2 = args.pop(0)
        if a2.startswith("<@"):
            p1.append(a2[2:-1])
            a2 = args.pop(0)

        if not a2.startswith("vs"):
            return simpleResp("Expected to see vs now")

        a3 = args.pop(0)
        if not a3.startswith("<@"):
            return simpleResp("Didn't recognise user %s" % (a3))
        p2.append(a3[2:-1])

        a4 = args.pop(0)
        if a4.startswith("<@"):
            p2.append(a4[2:-1])
            a4 = args.pop(0)

        if '-' in a4:
            b4 = a4.split('-')
            s1 = int(b4[0])
            s2 = int(b4[1])
        else:
            s1 = int(a4)
            a5 = args.pop(0)
            if a5 == '-':
                a5 = args.pop(0)
            s2 = int(a5)
            if s2 < 0:
                s2 = -s2  # Deal with case where someone writes 2 -10 by mistake

        if max(s1, s2) < 10:
            return simpleResp("Someone should have scored at least 10 points!")

        if max(s1, s2) > 10 and abs(s2 - s1) != 2:
            return simpleResp("Someone should have been two points ahead at the end?")

        if min(s1, s2) < 0:
            return simpleResp("")

        m = core.Match(p1, p2, s1, s2, datetime.datetime.now())

        mid = loldb.addmatch(m)

        return simpleResp("Match %s successfully submitted" % (mid)) + processRank(slack, [])

    except Exception as e:
        print str(e)
        return simpleResp("I'm sorry I didn't understand that")


def mangleit(x, iseq):
    c = '.'
    if x[0] in iseq:
        c = '='
    return "%i%s %s" % (x[0], c, x[1])


def formatRanking(slack, d, mc, lastg):
    # print badr
    r = []
    l = 1e6
    c = 0
    tc = 0
    iseq = []

    bad_neg = []
    bad_cov = []

    allusers = slack.users.list().body

    now = datetime.datetime.now()
    daysall = datetime.timedelta(days=30)
    days10 = datetime.timedelta(days=7)

    if not 'ok' in allusers:
        raise Exception("Couldn't get users...")

    spb = lambda x: unicode(x[0]) + u'\u200B' + unicode(x[1:])

    for n in sorted(d.items(), key=lambda x: x[1][0], reverse=True):
        name = spb(getNiceName(allusers, n[0]))

        timediff = now - lastg[n[0]]

        if mc[n[0]] < 3:
            bad_neg.append(name)
            continue
        elif mc[n[0]] < 10:
            if timediff > days10:
                bad_neg.append(name)
                continue
        else:
            if timediff > daysall:
                continue

        # if badr[n[0]]:
            # bad_cov.append(name)
            # continue

        tc += 1
        if n[1][0] < l - 0.1:
            c = tc
            l = n[1][0]
        else:
            iseq.append(c)
        ss = "%.1f" % n[1][0]
        if mc[n[0]] < 3:
            ss = '*'
        r.append((c, "%s (%s), W-L: %i-%i" % (name, ss, n[1][1], n[1][2])))

    r = map(lambda x: mangleit(x, iseq), r)

    if len(bad_neg) > 0:
        r.append("Needs more games: %s" % (', '.join(bad_neg)))

    if len(bad_cov) > 0:
        r.append("Needs more varied games: %s" % (', '.join(bad_cov)))

    return r


def getNiceName(allusers, uid):
    members = allusers['members']
    name = uid
    dn = [x for x in members if x['id'] == uid]
    if len(dn) == 1:
        name = dn[0]['name']
    return name


def getTimeSinceDesc(w):
    delta = datetime.datetime.now() - w

    if delta.days > 0:
        return "%i days ago" % (delta.days)

    if delta.seconds > 3600:
        return "%i hours ago" % (delta.seconds / 3600)

    if delta.seconds > 60:
        return "%i minutes ago" % (delta.seconds / 60)

    return "just now"


def formatMatch(allusers, m):
    nnf = lambda u: getNiceName(allusers, u)
    part1 = ' '.join(map(nnf, m.players1))
    part2 = ' '.join(map(nnf, m.players2))
    tsd = getTimeSinceDesc(m.when)

    return '%s vs %s %i - %i (%s)' % (part1, part2, m.score1, m.score2, tsd)


def processRank(slack, args):
    m = loldb.getmatches()
    elos = eloranking.get_rankings(m)
    elos = sorted(elos.items(), key=lambda x: x[1], reverse=True)

    uids, scores = zip(*elos)
    ranks = range(1, len(elos)+1)
    wins, losses = eloranking.get_ws_ls(m,uids)


    allusers = slack.users.list().body
    nn = lambda x: getNiceName(allusers, x)
    longest_name = max(map(len, map(nn, uids)))
    rankFmt = lambda u,s,r,w,l: "{r:>3}. {u:<{ln}}  {s}  {w:>2} - {l:>2}".format(u=u,r=r,s=s,w=w,l=l,ln=longest_name)

    return simpleResp('```{}\n```'.format('\n'.join([rankFmt(*x) for x in zip(*[map(nn, uids),scores,ranks,wins,losses])])))


def processDelete(args):
    loldb.deletematch(args[0])
    return simpleResp("Match deleted!")


def processRecent(slack, args):
    allusers = slack.users.list().body
    rm = loldb.getrecent(3)
    fm = lambda m: formatMatch(allusers, m)
    msgt = 'Last 3 games:\n' + '\n'.join(map(fm, rm))
    return simpleResp(msgt)


def send_stats_graph(slack, args, user):
    if len(args) == 0:
        uid = user
    elif len(args) != 1:
        return None
    else:
        if not args[0].startswith("<@"):
            return None
        uid = args[0][2:-1]

    allusers = slack.users.list().body
    m = loldb.getmatches()
    fig_file = eloranking.get_stats_graph(m, uid, getNiceName(allusers, uid))
    channel_id = filter(lambda x: x['name'] == 'foosball-dev',
                        slack.channels.list().body['channels'])[0]['id']
    slack.files.upload(fig_file, channels=channel_id)
    os.remove(fig_file)


def processStats(slack, args, user):
    if len(args) == 0:
        uid = user
    elif len(args) != 1:
        return simpleResp("I don't understand...")
    else:
        if not args[0].startswith("<@"):
            return simpleResp("I don't know who %s is" % (args[0]))

        uid = args[0][2:-1]

    print("Stats UID: %s" % (uid))

    allusers = slack.users.list().body

    m = loldb.getmatches()
    lg = loldb.getlastgame(uid)
    td = butterflyrank.get_rankings(m)

    nn = getNiceName(allusers, uid)

    r1t = "Stats for %s" % nn
    div = '-' * (len(r1t))
    r1ta = "Skill level (0-10): %.1f" % td[uid][0]
    r2t = "W-L: %i-%i" % (td[uid][1], td[uid][2])
    r2ta = "Last match: %s" % formatMatch(allusers, lg)

    allt = [r1t, div, r1ta, r2t, r2ta]

    return simpleResp('```' + '\n'.join(allt) + '```')


def processPredict(slack, args):
    m = loldb.getmatches()
    print(args)
    try:
        middle = args.index('vs')
        print(middle)
        p1 = args[middle-1][2:-1]
        print(p1)
        p2 = args[middle+1][2:-1]
        print(p2)
        allusers = slack.users.list().body
        nn = lambda x: getNiceName(allusers, x)
        predict_fmt = lambda w, od, l: "{} has a {:.1f}% chance of beating {}".format(nn(w), od, nn(l))
        return (simpleResp(predict_fmt(*eloranking.predict_winner(m, p1, p2))+"\n"))
    except ValueError:
        return simpleResp("Perhaps you didn't use \'vs\'?\n")
    except KeyError:
        return simpleResp("Error in finding one or both players.\n")
    except:
        return simpleResp("An unknown error occured.")


def processHelp(args):
    ht = {'result': "Submit a match result\n```@foosbot: result @dave @steve vs @bob @jon 10 - 6```",
          'rank': "See a table of player rankings based on recent results",
          'delete': "Delete a match entered incorrectly or by mistake\n```@foosbot: delete abcdef123456```",
          'recent': "See recently played matches",
          'predict': "Predict a match result\n```@foosbot: predict @steve vs @dave```",
          'stats': "Get player stats\n```@foosbot: stats @dave```"}

    sht = 'Commands are %s and %s. For more help, type help <command>' % (', '.join(ht.keys()[:-1]), ht.keys()[-1])

    if len(args) == 0:
        return simpleResp(sht)
    else:
        if args[0] in ht:
            return simpleResp(ht[args[0]])
        else:
            return simpleResp("Sorry, I don't know about %s" % args[0])


def processMessage(slack, config, _msg):
    try:
        _fooschan = config['fooschan']
        _adminuser = config['adminuser']
        msg = json.loads(_msg)

        if not 'type' in msg:
            return []

        if msg['type'] != 'message':
            return []
        if msg['channel'] != _fooschan:
            return []

        if not 'text' in msg:
            print("Ignoring possible edit?")
            return []

        text = msg['text']
        user = 'UNKNOWN'

        if 'user' in msg:
            user = msg['user']

        # print text

        if not text.startswith('<@%s>' % config['botuser']):
            return []

        ctext = text.partition(' ')[2]

        args = ctext.split(None)
        if not args:
            return simpleResp("You didn't ask me to do anything!")

        cmd = args[0]

        if cmd.lower() == 'result':
            return processSubmit(slack, args[1:])
        elif cmd.lower().startswith('rank'):
            return processRank(slack, args[1:])
        elif cmd.lower().startswith('delete'):
            return processDelete(args[1:])
        elif cmd.lower().startswith('recent'):
            return processRecent(slack, args[1:])
        elif cmd.lower().startswith('help'):
            return processHelp(args[1:])
        elif cmd.lower().startswith('predict'):
            return processPredict(slack, args[1:])
        elif cmd.lower().startswith('stat'):
            send_stats_graph(slack, args[1:], user)
            return processStats(slack, args[1:], user)
        else:
            return simpleResp("I didn't understand the command %s" % (cmd))

    except Exception as e:
        exc_type, exc_value, exc_traceback = sys.exc_info()
        traceback.print_tb(exc_traceback)
        return simpleResp("<@%s> Error: %s" % (_adminuser, str(e)))



# {"type":"message","channel":"C0BCN8XD4","user":"U02AYNXND","text":"<@U0BCNAB3P>: test message","ts":"1443355146.000005","team":"T027SA6KX"}
