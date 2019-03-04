import requests
import json
import os
import sys


PROGRESS_MESSAGE = '🦑🦑 OK! Backporting... PR will be up in a few'
SUCCESS_MESSAGE = '🦑 Backport PR is up!'
FAILURE_MESSAGE = '😢 I had a problem backporting this PR, please help me!'


class GithubBackportBot(object):
    def __init__(self):
        try:
            self.github_api_token = os.environ['BACKPORT_GH_API']
            self.maintainer_list = os.environ['BACKPORT_MAINTAINERS']
        except KeyError:
            import pdb; pdb.set_trace()
            print('Define BACKPORT_GH_API as an env var')
            sys.exit()

    def poll_for_new_notifications(self):
        # maybe just get notifications in that repo?
        r = requests.get('https://api.github.com/notifications')

        # for notification in notifications:
        # if it's a mention, check if it's a maintainer
        # check if we've already acted on this PR (i.e. have we commented?)
        # if it is, do the needful
        # try:  except e: 'I had a problem backporting your PR :-(, please help me'
