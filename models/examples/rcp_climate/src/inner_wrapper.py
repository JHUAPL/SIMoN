import glob
import sys
sys.path.append('/')
from outer_wrapper import OuterWrapper
from climate_model import temp_inc


class InnerWrapper(OuterWrapper):

    def __init__(self):
        num_input_schemas = len(glob.glob("/opt/schemas/input/*.json"))
        super().__init__(model_id="rcp_climate", num_expected_inputs=num_input_schemas)

    def configure(self, **kwargs):
        self.raw_data = kwargs['rcp26data']
        if 'rcp26data' in kwargs.keys():
            self.mean_temp, self.climate_data0, self.climate_data1 = temp_inc(self.raw_data, self.incstep)
        else:
            print('rcp data not found')

    def increment(self, **kwargs):
        self.global_temp, self.climate_data0, self.climate_data1 = temp_inc(self.raw_data, self.incstep)

        results ={'rcp_climate':
                    {'global_temp':
                        {'data':
                            {'temp': self.global_temp},
                        'granularity': 'global'},
                    'precipitation':
                        {'data': self.climate_data0, 'granularity': 'climate'},
                    'evaporation':
                        {'data': self.climate_data1, 'granularity': 'climate'}
                    }
                }
        return results


def main():
    wrapper = InnerWrapper()
    wrapper.run()


if __name__ == "__main__":
    main()
