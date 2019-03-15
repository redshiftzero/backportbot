FROM python:3

RUN apt-get update && apt-get -y upgrade && apt-get install -y sudo vim
RUN groupadd -r botuser && useradd -r -g botuser botuser && mkdir /home/botuser && chown botuser:botuser /home/botuser
USER botuser

RUN mkdir /home/botuser/app
COPY . /home/botuser/app
RUN cd /home/botuser/app/ && python setup.py install --user
RUN mkdir /home/botuser/.ssh/
RUN ssh-keyscan github.com > ~/.ssh/known_hosts
CMD ['/home/botuser/.local/bin/backportbot']
