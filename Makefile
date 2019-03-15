build:
	docker build -t gcr.io/securedrop-personal/backportbot .

run:
	docker run -e BACKPORT_GH_API \
	    -e BACKPORT_MAINTAINER \
		-e BACKPORT_BOT_GH_NAME \
		-e BACKPORT_BOT_GH_EMAIL \
		-e BACKPORT_BOT_SSH_KEY \
		-e BACKPORT_GH_ORG \
		-e BACKPORT_GH_REPO \
		-e BACKPORT_TRUNK_BRANCH \
	    -it gcr.io/securedrop-personal/backportbot:latest \
		/home/botuser/.local/bin/backportbot
