FROM ubuntu:18.04
RUN apt-get update && apt-get install -y python3-dev python3-pip wget vim
RUN echo "deb http://download.opensuse.org/repositories/network:/messaging:/zeromq:/release-stable/xUbuntu_18.04/ ./" >> /etc/apt/sources.list
RUN wget https://download.opensuse.org/repositories/network:/messaging:/zeromq:/release-stable/xUbuntu_18.04/Release.key -O- | apt-key add
RUN apt-get install -y libzmq3-dev
RUN pip3 install pymongo pyzmq jsonschema
CMD ["python3", "/opt/handler.py"]
