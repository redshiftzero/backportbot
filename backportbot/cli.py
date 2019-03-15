import time
import requests

from backportbot.bot import GithubBackportBot


POLL_TIME = 60


def main():
    bot = GithubBackportBot()
    while True:
        try:
            bot.poll_for_new_notifications()
            time.sleep(POLL_TIME)
        except requests.exceptions.ConnectionError:
            time.sleep(POLL_TIME)