FROM ubuntu:18.04
RUN apt-get update && apt-get install -y python3-dev python3-pip && apt-get -qy autoremove && apt-get clean && rm -r /var/lib/apt/lists/*
COPY ./requirements.txt /
RUN pip3 install -r /requirements.txt
CMD ["python3", "/opt/handler.py"]
