#!/usr/bin/env python

import slacker
# import json
import websocket
import slackparser
import json
import traceback
import time
import sys
import yaml
import datetime

import foos
from parse import on_message

config = yaml.load(open('config.yaml'))
slack = slacker.Slacker(config['slacktoken'])
config['bot_id'] = slack.auth.test().body['user_id']
config['users'] = slack.users.list().body['members']


def getniceuser(users, n):
    uc = list(filter(lambda x: x['name'] == n, users))
    if len(uc) != 1:
        print("Unable to find user %s in slack, please check your config" % (n))
    else:
        return uc[0]['id']


def mangleconfig(config):
    users = config['users']
    config['adminuser'] = getniceuser(users, config['adminuser'])
    config['botuser'] = getniceuser(users, config['botuser'])


def onrecv(ws, message):
    # At this point, the bot should only reply to messages.
    message = json.loads(message)
    if message['type'] == "message":
        on_message(slack, config, message)
    else:
        pass


def onerr(ws, err):
    print("ERROR: ", err)


def onclose(ws):
    print("Socket closed")


def run_bot():
    rtminfo = slack.rtm.start()
    wsurl = rtminfo.body['url']

    print("Attempting to connect to %s" % (wsurl))

    ws = websocket.WebSocketApp(wsurl, on_message=onrecv,
                                on_error=onerr, on_close=onclose)

    ws.run_forever()


mangleconfig(config)

if __name__ == "__main__":
    failcount = 0
    lastfail = datetime.datetime.now()
    while True:
        print("Connecting")
        run_bot()
        print("Connection lost...")
        now = datetime.datetime.now()
        timeran = now - lastfail
        lastfail = now
        if timeran.total_seconds() < 3600:
            failcount += 1
        else:
            failcount = 0

        if failcount > 10:
            print("Too many failures, exiting")
            break
        else:
            print("Will reconnect in 60 seconds")
            time.sleep(60)
