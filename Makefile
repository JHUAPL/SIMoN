SHELL := /bin/bash

build-model:
	docker build -t simon-model:latest -f build/Dockerfile .

up:
	cd build && docker-compose up --build -d

down:
	cd build && docker-compose down

all: build-model up

clean: down
	sudo rm -rf ./data/db
