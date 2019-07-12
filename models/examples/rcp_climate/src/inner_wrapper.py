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
        # self.data = kwargs['rcp26data']
        print(self.incstep)
        if 'rcp26data' in kwargs.keys():
            self.data = temp_inc(kwargs['rcp26data'], self.incstep)
        elif 'rcp60data' in kwargs.keys():
            self.data = temp_inc(kwargs['rcp60data'], self.incstep)
        elif 'rcp85data' in kwargs.keys():
            self.data = temp_inc(kwargs['rcp85data'], self.incstep)
        else:
            print('rcp data not found')

    def increment(self, **kwargs):
        print(self.incstep)
        wrapped_data = {'temp': self.data}
        print(wrapped_data)

        if self.incstep != 94:
            if 'rcp26data' in kwargs.keys():
                data = temp_inc(kwargs['rcp26data'], self.incstep)
                wrapped_data = {'temp': data}
                self.data = wrapped_data
            # self.configure(self,**kwargs)
        else:
            if 'rcp26data' in kwargs.keys():
                data = temp_inc(kwargs['rcp26data'], 94)
                wrapped_data = {'temp': data}
                self.data = wrapped_data

        return {'rcp_climate': {'rcp_climate': {'data': wrapped_data, 'granularity': 'global'}}}


def main():
    wrapper = InnerWrapper()
    wrapper.run()


if __name__ == "__main__":
    main()