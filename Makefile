SHELL := /bin/bash

.PHONY: build-model up all stop clean purge graph

build-model:
	docker build -t simon-model:latest -f build/Dockerfile .

up:
	cd build && docker-compose -p simon up --build -d

all: build-model up

stop:
	cd build && docker-compose -p simon stop

clean:
	cd build && docker-compose -p simon down

purge:
	cd build && docker-compose -p simon down --rmi all

graph:
	cd graphs && docker build -t simon-graph:latest . && docker run -v `pwd`:/opt -d simon-graph:latest
