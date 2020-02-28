# Copyright 2020 The Johns Hopkins University Applied Physics Laboratory LLC
# All rights reserved.
# Distributed under the terms of the MIT License.


import glob
import sys
import logging

sys.path.append('/')
from outer_wrapper import OuterWrapper
from PopulationSimulation import pop_sim, get_data


class InnerWrapper(OuterWrapper):
    def __init__(self):
        num_input_schemas = len(glob.glob("/opt/schemas/input/*.json"))
        super().__init__(
            model_id="population", num_expected_inputs=num_input_schemas
        )

        # should match the max_incstep in broker/config.json
        self.max_incstep = 50

    def configure(self, **kwargs):
        if 'county_populations' in kwargs.keys():
            self.data = pop_sim(kwargs['county_populations'], self.max_incstep)
        else:
            logging.warning(f'incstep {self.incstep}: county_populations not found')

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
