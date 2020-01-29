SHELL := /bin/bash

build-model:
	docker build -t simon-model:latest -f build/Dockerfile .

up:
	cd build && docker-compose up --build -d

all: build-model up

down:
	cd build && docker-compose down

clean: down
	sudo rm -rf ./data/db
