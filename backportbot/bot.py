import requests
import json
import git
import os
import sys
from github import Github, GithubException


PROGRESS_MESSAGE = '🦑🦑 OK! Trying to backport... '
SUCCESS_MESSAGE = '🦑 Backport PR is up!'
EXPLAINER_MESSAGE = "Please mention me and say 'backport release_branch' where release_branch is the branch name you want this PR backported into"
AUTH_FAILURE_MESSAGE = "You're not a maintainer, byeeeee"
BRANCH_FAILURE_MESSAGE = "Hmm, that release branch doesn't exist yet 😢. Create it and then ping me again?"
FORK_FAILURE_MESSAGE = "I don't support backport requests from forked PRs yet 😢 you'll need to do this one"
GENERIC_FAILURE_MESSAGE = '😢 I had a problem backporting this PR, please help me with this one!'


class GithubBackportBot(object):
    def __init__(self):
        self.root_url = 'https://api.github.com'
        try:  # Loading all required env vars
            self.github_api_token = os.environ['BACKPORT_GH_API']
            self.maintainer = os.environ['BACKPORT_MAINTAINER']
            self.bot_name = os.environ['BACKPORT_BOT_GH_NAME']
            self.bot_email = os.environ['BACKPORT_BOT_GH_EMAIL']
            self.bot_ssh_key = os.environ['BACKPORT_BOT_SSH_KEY']
            self.github_org = os.environ['BACKPORT_GH_ORG']
            self.github_repo = os.environ['BACKPORT_GH_REPO']
            self.trunk_branch = os.environ['BACKPORT_TRUNK_BRANCH']

            # Save SSH key to disk with expected permissions.
            path_to_ssh_priv_key = '/home/botuser/.ssh/id_rsa'
            if not os.path.isfile(path_to_ssh_priv_key):
                with open(path_to_ssh_priv_key, 'w') as f:
                    f.write(self.bot_ssh_key)
                    f.write('\n')
            os.chmod(path_to_ssh_priv_key, 0o0600)
        except KeyError as e:
            print('Key not found: {}'.format(e))
            sys.exit()

        # Local git config, assumes use of SSH.
        self.git_repo = git.Repo.clone_from('git@github.com:{}/{}.git'.format(self.bot_name, self.github_repo), '/home/botuser/gitdir')
        self.git_repo.config_writer().set_value("user", "name", self.bot_name).release()
        self.git_repo.config_writer().set_value("user", "email", self.bot_email).release()

        # GitHub API
        self.github_api = Github(self.github_api_token)
        self.repo = self.github_api.get_repo("{org}/{repo}".format(org=self.github_org, 
            repo=self.github_repo))
        self.user = self.github_api.get_user()

    def poll_for_new_notifications(self):
        # By default, this API request will get only unread notifications.
        # i.e., events we've successfully handled here won't appear here,
        # since we mark notifications as read once we've processed them.
        notifications = self.user.get_notifications()

        for notification in notifications:
            if notification.reason == 'mention':  # We only react to mentions.
                self.handle_backport_request(notification)

        return

    def handle_backport_request(self, notification):
        pull_request_url = notification.subject.url
        pull_request_id = int(pull_request_url.split('/')[-1])
        pull_request = self.repo.get_pull(pull_request_id)

        notification_comment_url = notification.subject.latest_comment_url
        comment_id = int(notification_comment_url.split('/')[-1])
        comment = pull_request.get_issue_comment(comment_id)
        username_bot_was_mentioned_by = comment.user.login

        # Verify the user is allowed to trigger backport PRs.
        if username_bot_was_mentioned_by != self.maintainer:
            # Don't create an issue comment.. Maybe confused reaction emoji?
            # pull_request.create_issue_comment(AUTH_FAILURE_MESSAGE)
            notification.mark_as_read()
            return

        # Verify this is not from a fork. TODO: support forks.
        branch_to_backport = pull_request.head.ref
        if ':' in branch_to_backport:
            pull_request.create_issue_comment(FORK_FAILURE_MESSAGE)
            notification.mark_as_read()
            return

        # Verify the messages sent to the bot are what we expect.
        requested_action = comment.body.split()[1]
        release_branch = comment.body.split()[2]
        if requested_action != 'backport' or not release_branch:
            pull_request.create_issue_comment(EXPLAINER_MESSAGE)
            notification.mark_as_read()
            return

        # Verify the release branch requested exists on the remote.
        try:
            self.repo.get_branch(release_branch)
        except GithubException:
            pull_request.create_issue_comment(BRANCH_FAILURE_MESSAGE)
            notification.mark_as_read()
            return

        try:
            pull_request.create_issue_comment('@{} {}'.format(username_bot_was_mentioned_by, 
                                                              PROGRESS_MESSAGE))
            branch_name = self.prepare_branch_for_backport(pull_request_id, branch_to_backport, release_branch)
            self.make_pr(pull_request_id, branch_to_backport, branch_name, release_branch)
            pull_request.create_issue_comment(SUCCESS_MESSAGE)
            notification.mark_as_read()
        except git.exc.GitCommandError:  # This is the exception that occurs for a conflict.
            pull_request.create_issue_comment(GENERIC_FAILURE_MESSAGE)
            notification.mark_as_read()
            return

        return

    def make_pr(self, pr_number, old_branch, new_branch, release_branch):
        """
        Make a PR against the upstream repo with the target branch.
        """

        title = '[{}] Backporting changes from PR #{}'.format(release_branch, pr_number)
        body = "To test, verify these are the same commits as in PR #{}".format(pr_number)

        self.repo.create_pull(title=title,
                              body=body,
                              base=release_branch,
                              head='{}:{}'.format(self.bot_name, new_branch))

        return

    def prepare_branch_for_backport(self, pr_number, backport_branch, release_branch):
        """
        This method prepares a branch locally with the backported commits for the release
        branch.

        pr_number [int]: ID number of the pull request that is requested to be backported.
        backport_branch [str]: Name of the branch to get backported.
        release_branch [str]: Name of the release branch we want to backport into.
        """

        upstream = self.add_upstream_remote_of_project_if_needed()

        # Get latest release branch and check it out.
        upstream.fetch('refs/heads/{branch}:refs/heads/{branch}'.format(
            branch=release_branch))
        self.git_repo.git.checkout(release_branch)

        # Make the backport branch based on the release branch.
        new_branch = 'backport-{pr}-into-release'.format(pr=pr_number)
        self.git_repo.git.checkout('-b', new_branch)

        # Get the branch to be backported.
        upstream.fetch('refs/heads/{branch}:refs/heads/{branch}'.format(
            branch=backport_branch))
        self.git_repo.git.checkout(backport_branch)

        # Using git log, compare the PR branch with the trunk branch
        # to determine which commits are new and need to get backported.
        commits_to_backport = self.git_repo.git.log(
            '{base}..{backport}'.format(base=self.trunk_branch, backport=backport_branch),
            "--pretty=format:'%h'",
            '--abbrev=40')

        commits_to_backport = commits_to_backport.replace("'", "").split('\n')

        # Now cherry-pick onto the backport branch.
        self.git_repo.git.checkout(new_branch)
        for commit in reversed(commits_to_backport):
            self.git_repo.git.cherry_pick('-x', commit)

        # Cleanup: Destroy release branch locally so that we can fetch it again next time.
        self.git_repo.git.branch('-D', release_branch)
        # TODO: Delete backport branches post-merge.

        # Push our new branch to GitHub.
        for remote in self.git_repo.remotes:
            if str(remote) == 'origin':
                origin = remote

        origin.push(new_branch)

        return new_branch

    def add_upstream_remote_of_project_if_needed(self):
        """
        Helper method that ensures the upstream remote is configured.
        """
        for remote in self.git_repo.remotes:
            if str(remote) == 'upstream':
                return remote

        upstream = git.remote.Remote.add(self.git_repo, 'upstream', 
            'https://github.com/{}/{}.git'.format(self.github_org, self.github_repo))
        return upstream