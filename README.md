## SIMoN
System Integration with Multiscale Networks

Copyright 2020 The Johns Hopkins University Applied Physics Laboratory

Licensed under the MIT License

## Description
The SIMoN joint modeling framework integrates independently-designed predictive models into a cohesive system, in order to produce a unified model. While many useful models are limited to predicting only a single isolated component of a larger system, SIMoN is able to connect models together so that collectively they can provide a more complete representation of the global system and its dynamics.  By using the SIMoN software, a modeler is able to join these disparate models together in various combinations and find new insights in their data.

In order to translate data from its models across different geographic granularities, SIMoN uses a network graph that represents all the granularities, their corresponding entities, and their relationships to each other. The individual models feed each other updated data inputs at synchronized time intervals, and traverse the network graph to translate their data from one granularity to another. A sample granularity graph is provided, but modelers can extend it or create a graph of their own, by modifying and using the `graphs/build.py` script.

SIMoN is written in Python 3, and uses Docker to manage its models and their integration. Each model runs in its own separate, modular Docker container. An additional container runs the system’s centralized Broker, which receives each model’s data outputs using a PyZMQ publish-subscribe messaging pattern. The Broker then redirects the data to any models that request it. The models can then use this data as their inputs for the next incremental step in the system’s synchronized run.

## Setup
SIMoN uses Docker and Compose to run its models in separate containers. To run SIMoN, clone the repo and install these tools.

Additionally, install `make`, so that the shell commands that operate SIMoN can be executed more easily using the Makefile.

* install Docker
	* https://docs.docker.com/install/
* install Docker Compose
	* https://docs.docker.com/compose/install/

## Usage
1.  Choose the models that you want to run together in the SIMoN framework. Note their interdependencies, and make sure that each model has a source for all of its necessary data inputs.
2.  Once you have a consistent set of models, add the unique name of each of the models to the "models" list in `broker/config.json`
3.  Create an entry for each model in the "services" section in `build/docker-compose.yml`
    ```
    model_name_1:
        build: ../models/examples/model_name_1/
        volumes:
            - ../models/examples/model_name_1:/opt:ro
4.  start SIMoN
	* `make all`
5.  shut down SIMoN
	* `make down` to stop all models
	* `make clean` to stop all models and clear the database

## Add a new model
1. In the models/ directory, copy the template/ directory and rename it to the ID (unique name) of your new model.
1. Within this new directory are several required directories and files:
    * `src/` stores the model's source code
        * `inner_wrapper.py`
            * this file receives input data from other models, performs operations on it, and returns the output data that will be sent to other models.
            * implement the `configure()` and `increment()` abstract methods
            * replace the template name with the the model's ID (its unique name)
            * call the functions (e.g., my_function_1) defined in other custom scripts from this file
        * `my_function_1.py`
            * aditional code that your model uses
        * `my_function_2.py`
            * aditional code that your model uses
    * `schemas/input/` stores JSON schemas that incoming data messages must validate against
	* `*.json`
        * granularity: specify the granularity of input data that this model needs. SIMoN will translate incoming data to this granularity before sending it to the model's inner wrapper.
    * `schemas/output/` stores JSON schemas that outgoing data messages must validate against
        * `*.json`
        * granularity: specify the granularity of data that this model will output. SIMoN will translate outgoing data to this granularity after receiving it from the model's inner wrapper.
    * `config/` stores JSON objects with the initial data and parameters needed for the model's first time step
        * `*.json`
2. add the name of the new model to the "models" list in `broker/config.json`
3. add the new model to the "services" in `build/docker-compose.yml` by specifying its path:
    ```
    new_model_name:
        build: ../models/examples/new_model_name/
        volumes:
            - ../models/examples/new_model_name:/opt:ro
