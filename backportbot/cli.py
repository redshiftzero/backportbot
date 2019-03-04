import time

from backportbot.github import GithubBackportBot


POLL_TIME = 60


def main():
    bot = GithubBackportBot()
    while True:
        bot.poll_for_new_notifications()
        time.sleep(POLL_TIME)
