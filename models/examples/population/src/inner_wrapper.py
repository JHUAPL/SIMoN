# Copyright 2020 The Johns Hopkins University Applied Physics Laboratory LLC
# All rights reserved.
# Distributed under the terms of the MIT License.


import glob
import sys

sys.path.append('/')
from outer_wrapper import OuterWrapper
from PopulationSimulation import pop_sim, get_data


class InnerWrapper(OuterWrapper):
    def __init__(self):
        num_input_schemas = len(glob.glob("/opt/schemas/input/*.json"))
        super().__init__(
            model_id="population", num_expected_inputs=num_input_schemas
        )

    def configure(self, **kwargs):
        if 'county_populations' in kwargs.keys():
            # number of years needs to be >= the maximum increment step
            # 2016 is init increment
            self.data = pop_sim(kwargs['county_populations'], 50)
            print(self.data)
        else:
            print('population initialization data not found')

    def increment(self, **kwargs):
        data = get_data(self.data, self.initial_year + self.incstep)
        results = {
            'population': {
                'population': {'data': data, 'granularity': 'county'}
            }
        }
        return results


def main():
    wrapper = InnerWrapper()
    wrapper.run()


if __name__ == "__main__":
    main()
