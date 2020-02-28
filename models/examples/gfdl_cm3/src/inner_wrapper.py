# Copyright 2020 The Johns Hopkins University Applied Physics Laboratory LLC
# All rights reserved.
# Distributed under the terms of the MIT License.


import glob
import sys
import logging

sys.path.append('/')
from outer_wrapper import OuterWrapper
from climate_model import temp_inc


class InnerWrapper(OuterWrapper):
    def __init__(self):
        num_input_schemas = len(glob.glob("/opt/schemas/input/*.json"))
        super().__init__(
            model_id="gfdl_cm3", num_expected_inputs=num_input_schemas
        )

    def configure(self, **kwargs):
        self.raw_data = kwargs['rcp26data']
        if 'rcp26data' in kwargs.keys():
            self.global_temp, self.precipitation, self.evaporation = temp_inc(
                self.raw_data, self.incstep
            )
        else:
            logging.warning(f'incstep {self.incstep}: rcp26data not found')

    def increment(self, **kwargs):
        self.global_temp, self.precipitation, self.evaporation = temp_inc(
            self.raw_data, self.incstep
        )

        results = {
            'gfdl_cm3': {
                'global_temp': {
                    'data': {'global_temp': self.global_temp},
                    'granularity': None,
                },
                'precipitation': {
                    'data': self.precipitation,
                    'granularity': 'latlon',
                },
                'evaporation': {
                    'data': self.evaporation,
                    'granularity': 'latlon',
                },
            }
        }
        return results


def main():
    wrapper = InnerWrapper()
    wrapper.run()


if __name__ == "__main__":
    main()
