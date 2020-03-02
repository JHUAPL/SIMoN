FROM ubuntu:18.04
RUN apt-get update && apt-get install -y python3-dev=3.6.7-1~18.04 python3-pip=9.0.1-2.3~ubuntu1.18.04.1 cmake=3.10.2-1ubuntu2.18.04.1 wget && apt-get -qy autoremove && apt-get clean && rm -r /var/lib/apt/lists/*
RUN wget https://github.com/libspatialindex/libspatialindex/releases/download/1.9.3/spatialindex-src-1.9.3.tar.gz -P /
RUN tar xfvz /spatialindex-src-1.9.3.tar.gz
WORKDIR /spatialindex-src-1.9.3
RUN cmake -DCMAKE_INSTALL_PREFIX=/libspatialindex .
RUN make
RUN make install
ENV LD_LIBRARY_PATH=/libspatialindex/lib
COPY ./requirements.txt /
RUN pip3 install -r /requirements.txt
ENTRYPOINT ["python3", "/opt/build.py"]
