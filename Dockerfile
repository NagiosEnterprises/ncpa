FROM ubuntu
MAINTAINER Nicholas Scott

RUN apt-get update
RUN apt-get install build-essential -y
RUN apt-get install zlib1g-dev -y
RUN apt-get install libssl-dev -y
RUN apt-get install python-dev -y
RUN apt-get install curl -y
RUN mkdir -p /src/ncpa

ADD . /src/_ncpa
RUN curl --silent --show-error --retry 5 https://bootstrap.pypa.io/get-pip.py | python2.7
RUN pip install -r /src/_ncpa/requirements.txt

RUN groupadd nagcmd
RUN useradd nagios -M -g nagcmd -u 1000

CMD python /src/ncpa/agent/ncpa_posix_listener.py -n
