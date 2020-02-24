SHELL := /bin/bash

build-model:
	docker build -t simon-model:latest -f build/Dockerfile .

up:
	cd build && docker-compose up --build -d

all: build-model up

stop:
	cd build && docker-compose stop

clean:
	cd build && docker-compose down
