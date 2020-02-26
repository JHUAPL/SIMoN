# Copyright 2020 The Johns Hopkins University Applied Physics Laboratory LLC
# All rights reserved.
# Distributed under the terms of the MIT License.


import glob
import sys

sys.path.append('/')
from outer_wrapper import OuterWrapper
from Water_Demand_Model import Water_Demand_Simulation


class InnerWrapper(OuterWrapper):
    def __init__(self):
        num_input_schemas = len(glob.glob("/opt/schemas/input/*.json"))
        super().__init__(
            model_id="water_demand", num_expected_inputs=num_input_schemas
        )

    def configure(self, **kwargs):
        if 'rates' in kwargs.keys():
            self.rate = kwargs['rates']
        if '2016_populations' in kwargs.keys():
            self.countypop = kwargs['2016_populations']

    def increment(self, **kwargs):
        if 'population' in kwargs.keys():
            self.countypop = kwargs['population']['population']['data']
        else:
            print('input population not found')
        demand = Water_Demand_Simulation(self.countypop, self.rate)

        results = {
            'water_demand': {
                'water_demand': {'data': demand, 'granularity': 'county'}
            }
        }
        return results


def main():
    wrapper = InnerWrapper()
    wrapper.run()


if __name__ == "__main__":
    main()
