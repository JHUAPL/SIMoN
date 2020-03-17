# Copyright 2020 The Johns Hopkins University Applied Physics Laboratory LLC
# All rights reserved.
# Distributed under the terms of the MIT License


import glob
import sys

sys.path.append("/")
from outer_wrapper import OuterWrapper

# import helper functions
from my_module import my_function


class InnerWrapper(OuterWrapper):
    def __init__(self):

        # count the number of JSON files in the input schemas directory
        num_input_schemas = len(glob.glob("/opt/schemas/input/*.json"))

        # unique_model_name is the name of the model (must match the name of the model's directory)
        super().__init__(
            model_id="unique_model_name", num_expected_inputs=num_input_schemas
        )

    def configure(self, **kwargs):
        # config_datax refers to the names of the JSON files in the config directory
        self.input_data1 = kwargs["config_data1"]
        self.input_data2 = kwargs["config_data2"]
        self.input_data3 = kwargs["config_data3"]

    # this model has two input schemas, and so expects input from two other models
    def increment(self, **kwargs):

        # input_model_name1 matches the name of a JSON file in the input schemas directory
        if "input_model_name1" in kwargs.keys():
            # example_input1 and example_input2 refer to fields in the input schema
            self.input_data1 = kwargs["input_model_name1"]["example_input1"][
                "data"
            ]
            self.input_data2 = kwargs["input_model_name1"]["example_input2"][
                "data"
            ]

        # input_model_name2 matches the name of a JSON file in the input schemas directory
        if "input_model_name2" in kwargs.keys():
            # example_input3 refers to a field in the input schema
            self.input_data3 = kwargs["input_model_name2"]["example_input3"][
                "data"
            ]

        # calculate the model's outputs
        output1, output2 = my_function(
            self.input_data1, self.input_data2, self.input_data3
        )

        # template_output_schema matches the name of the JSON file in the output schemas directory
        # example_output1 and example_output2 refer to fields in the output schema
        # example_output1 is returned by my_function() in the county granularity
        # example_output2 is returned by my_function() in the latlon granularity
        # before it is published, the data will automatically be translated to the granularities specified in template_output_schema
        return {
            "template_output_schema": {
                "example_output1": {"data": output1, "granularity": "county"},
                "example_output2": {"data": output2, "granularity": "latlon"},
            }
        }


def main():
    wrapper = InnerWrapper()
    wrapper.run()


if __name__ == "__main__":
    main()
