import glob
import sys

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
            print('rcp data not found')

    def increment(self, **kwargs):
        self.global_temp, self.precipitation, self.evaporation = temp_inc(
            self.raw_data, self.incstep
        )

        results = {
            'gfdl_cm3': {
                'global_temp': {
                    'data': {'temp': self.global_temp},
                    'granularity': 'global',
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
