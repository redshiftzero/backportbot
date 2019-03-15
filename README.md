# backportbot
bot that backports pull requests into a release branch

Configure the following env vars for deployment:

```
BACKPORT_GH_API = 'api_token_for_your_bot'
BACKPORT_MAINTAINER = 'bot_listens_to_this_user'
BACKPORT_BOT_GH_NAME = 'bot_github_username'
BACKPORT_BOT_GH_EMAIL = 'bot_github_email'
BACKPORT_BOT_SSH_KEY = 'SSH-key-for-bot'  # export BACKPORT_BOT_SSH_KEY=$(cat ~/.ssh/path_to_bot_key)
BACKPORT_GH_ORG = 'bot_github_org'
BACKPORT_GH_REPO = 'bot_github_repo'
BACKPORT_TRUNK_BRANCH = 'trunk_development_branch_name'
```

And do the following:

1. Make sure that your bot is _watching_ the repo you want it to backport PRs in.
2. Fork the repo to your bot's GitHub account.
3. Add an SSH key for the bot to its GitHub account (docs: https://help.github.com/en/articles/connecting-to-github-with-ssh). 