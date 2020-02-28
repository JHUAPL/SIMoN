FROM ubuntu:18.04
RUN apt-get update && apt-get install -y python3-dev=3.6.7-1~18.04 python3-pip=9.0.1-2.3~ubuntu1.18.04.1 && apt-get -qy autoremove && apt-get clean && rm -r /var/lib/apt/lists/*
COPY ./requirements.txt /
RUN pip3 install -r /requirements.txt
CMD ["python3", "/opt/handler.py"]
