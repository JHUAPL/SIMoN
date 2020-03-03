# SIMoN Models

## Description

The SIMoN framework is designed to be extensible and flexible, providing tools for modelers to integrate new models, domains, and the corresponding geographic definitions easily. It currently connects predictive resource models from several different domains, including as climate, energy, water, and population. These SIMoN models are low fidelity, designed as proxies for larger models developed by the community.

![example models](models_diagram.png)

## Usage

1.  Choose the models that you want to run together in the SIMoN framework. The default SIMoN configuration uses these 5 sample models:
    * population
    * power_demand
    * power_supply
    * water_demand
    * gfdl_cm3

    To use a different set of models, see the instructions on how to "Add a new model" and "Remove a model" below.

2. Optionally, adjust the models' output schemas, in order to change the granularity of their output data. The recognized granularities (all lowercase) are:
    * usa48
    * state
    * county
    * nerc
    * huc8
    * latlon

## Add a new model

1.  Choose the models that you want to run together in the SIMoN framework. Note their interdependencies carefully, and make sure that each model has a source for all of its necessary data inputs. Sample models are provided in the `examples` directory, where each model has its own directory. Each model's dependencies are specified in its `schemas/inputs` directory. For example, the `power_supply` model relies on the `power_demand` model, and the `power_demand` and `water_demand` models both rely on the `population` model. The `population` and `gfdl_cm3` models do not rely on any other models, and can each be run independently.
2.  Once you have a complete set of models where all dependencies are satisfied, add the unique name of each of the models to the "models" list in `broker/config.json`.
3.  Create an entry for each model in the "services" section in `build/docker-compose.yml` and specify the path to each model's directory.
    ```
    model_name_1:
        build: ../models/examples/model_name_1/
        volumes:
            - ../models/examples/model_name_1:/opt:ro
4. In the `models` directory, copy the `template` directory, which serves as a blueprint for new models. Rename `template` to the ID (unique name) of your new model.
5. Within this new directory are several required directories and files that need to be modified:
    * `src/` stores the model's source code
        * `inner_wrapper.py`
            * This file receives input data from other models, performs operations on it, and returns the output data that will be sent to other models.
            * You must replace the template name with the the model's ID (its unique name).
            * You must implement the `configure()` and `increment()` abstract methods.
                * `configure()` simply loads the initialization data from the `config` directory.
                * `increment()` performs the model's calculations by calling any of the its custom function(s) (e.g., my_function_1) defined in other scripts.
        * `my_function_1.py`
            * additional code that your model uses
        * `my_function_2.py`
            * additional code that your model uses
    * `schemas/input/` stores JSON schemas that incoming JSON data messages must validate against. SIMoN uses the `jsonschema` Python package to validate the data messages against the schemas.
	* `*.json`
        * granularity: specifies the granularity of input data that this model needs. SIMoN will translate incoming data to this granularity before sending it to the model's inner wrapper.
    * `schemas/output/` stores JSON schemas that outgoing JSON data messages must validate against. SIMoN uses the `jsonschema` Python package to validate the data messages against the schemas.
        * `*.json`
        * granularity: specifies the granularity of data that this model will output. SIMoN will translate outgoing data to this granularity after receiving it from the model's inner wrapper.
    * `config/` stores JSON objects with the initial data and parameters needed to bootstrap the model and run its first time step.
        * `*.json`

## Remove a model

1.  Before removing a model from SIMoN, make sure that no other models rely on it for their dependencies. For example, the `gfdl_cm3` model can safely be removed because no other models depend on it for their data inputs. However, the `power_demand` model cannot be removed without also removing the `power_supply` model, which relies on `power_demand` as an input.
2.  Remove the name of the model from the "models" list in `broker/config.json`.
3.  Remove the entry for the model in the "services" section of `build/docker-compose.yml`.
4.  The model will no longer be included in future SIMoN runs. Note, however, that the model's dedicated directory is left intact.
5.  To add the model back into SIMoN, simply repeat steps 2 and 3 from "Add a new model."
