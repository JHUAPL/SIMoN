SHELL := /bin/bash

.PHONY: build-model up all stop clean purge

build-model:
	docker build -t simon-model:latest -f build/Dockerfile .

up:
	cd build && docker-compose up --build -d

all: build-model up

stop:
	cd build && docker-compose stop

clean:
	cd build && docker-compose down

purge:
	cd build && docker-compose down --rmi all
