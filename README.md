# SIMoN

[System Integration with Multiscale Networks](SIMoN.pdf)

Copyright 2020 The Johns Hopkins University Applied Physics Laboratory

Licensed under the [MIT License](LICENSE.md)

[Copyrights](Third&#32;Party&#32;Copyrights.pdf) for Third Party Software

Contact: simon@jhuapl.edu

## Description

With the rise of globalization, climate change, population growth, and resource constraints, new modeling techniques are needed to assess the sustainability of our future resources. These methods must adapt to highly coupled domains, accommodate new models and data as they emerge, facilitate validation through model comparison, and handle the patchwork of data and models available with different units, definitions, and geo-temporal scales.

To address this challenge, the SIMoN modeling framework integrates independently-designed predictive models into a cohesive system, in order to produce a unified model. While many useful models are limited to predicting only a single isolated component of a larger system, SIMoN is able to connect models together so that collectively they can provide a more complete representation of the global system and its dynamics.

## Requirements

Supported operating systems:
 - Linux
 - macOS
 - Windows 10

Software:
 - [Python](https://www.python.org/downloads/) >= 3.6
 - [Docker](https://docs.docker.com/install/) >= 18.09.6
 - [Docker Compose](https://docs.docker.com/compose/install/) >= 1.23.2
 - [Docker Desktop for Windows](https://hub.docker.com/editions/community/docker-ce-desktop-windows/)

## Setup

To run SIMoN, first install [Docker](https://docs.docker.com/install/) and [Compose](https://docs.docker.com/compose/install/).

Additionally, install `make`, so that the shell commands that operate SIMoN can be executed more easily using the Makefile.

The Docker commands in the provided scripts assume that you are a privileged user. To use Docker as a non-root user, add your user to the `docker` group:
```
sudo usermod -aG docker <your_username>
```
Log out and back in for this to take effect.

## [Usage](models/README.md)

1. To start SIMoN:
    * `make all`
    * Use `docker logs broker -f` to track output from the broker container. The increment step "incstep" should increase over time as models publish their data, and the mongodb container should populate with documents (database: `broker`; collection: `sub`).
    * Use `docker logs simon_your_model_name_1 -f` to track output from the model named `your_model_name`.
2.  To shut down SIMoN:
    * `make stop` to stop all the SIMoN containers.
    * `make clean` to stop and remove all the SIMoN containers.
    * `make purge` to stop and remove all the SIMoN containers, and also remove their images.

## [Visualization](viz/README.md)

Use the scripts in the `viz` directory to create a choropleth map visualization of the model data.
```
cd viz/
./export.sh <model_name> <year> <doc_name>.json
pip install -r requirements.txt
python plot.py --data <doc_name>.json
```
A new HTML file will be created. Open this file in a web browser to display the Bokeh visualization.
![precipitation](viz/demo/2035_precipitation.png)

## [Architecture](broker/README.md)

SIMoN is written in Python, and uses Docker to manage its models and their integration. Each model runs in its own Docker container. An additional container hosts the system's centralized broker, which orchestrates model runs and shares data among models using a ZeroMQ publish-subscribe messaging pattern.

The Docker containers used for the broker and the models are built from the [Ubuntu 18.04](https://hub.docker.com/_/ubuntu/) image, with the [Python 3.6](https://packages.ubuntu.com/bionic-updates/python3-dev) package layered on top. The container used for the database is built from a [MongoDB image](https://hub.docker.com/_/mongo/).
