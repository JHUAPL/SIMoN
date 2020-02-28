# Copyright 2020 The Johns Hopkins University Applied Physics Laboratory LLC
# All rights reserved.
# Distributed under the terms of the MIT License.


import glob
import sys
import logging

sys.path.append('/')
from outer_wrapper import OuterWrapper
from DemandSimulation import pow_dem_sim


class InnerWrapper(OuterWrapper):
    def __init__(self):
        num_input_schemas = len(glob.glob("/opt/schemas/input/*.json"))
        super().__init__(
            model_id="power_demand", num_expected_inputs=num_input_schemas
        )

    def configure(self, **kwargs):
        if 'state_consumption_per_capita' in kwargs.keys():
            self.cons = kwargs['state_consumption_per_capita']
        else:
            logging.warning(f'incstep {self.incstep}: state_consumption_per_capita not found')
        if '2016_populations' in kwargs.keys():
            self.pop = kwargs['2016_populations']
        else:
            logging.warning(f'incstep {self.incstep}: 2016_populations not found')

    def increment(self, **kwargs):
        if 'population' in kwargs.keys():
            self.pop = kwargs['population']['population']['data']
        elif self.incstep > 1:
            logging.warning(f'incstep {self.incstep}: population not found')

        demand = pow_dem_sim(self.pop, self.cons)

        results = {
            'power_demand': {
                'power_demand': {'data': demand, 'granularity': 'county'}
            }
        }

        return results


def main():
    wrapper = InnerWrapper()
    wrapper.run()


if __name__ == "__main__":
    main()
