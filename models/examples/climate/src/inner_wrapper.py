import glob
import sys
import fair
sys.path.append('/')
from outer_wrapper import OuterWrapper
from climate import temperature_simulation

#put the json file from the output of power supply into the schemas/input file

class InnerWrapper(OuterWrapper):

    def __init__(self):
        num_input_schemas = len(glob.glob("/opt/schemas/input/*.json"))
        super().__init__(model_id="climate", num_expected_inputs=num_input_schemas)
        #self.electric=None

    def configure(self, **kwargs):
        if 'co2' in kwargs.keys():
            self.electric = kwargs['co2']
        if 'thermo_water' in kwargs.keys():
            self.electric = kwargs['thermo_water']

    def increment(self, **kwargs):
        if 'power_output' in kwargs.keys():
            self.electric = kwargs['power_output']['co2']['data']
        else: 
            print('input co2 not found')
        temperature=float(temperature_simulation(self.electric))
        
        return {'climate': { 'climate': {'data': {'global_temp': temperature}, 'granularity': 'global'}}}


def main():
    wrapper = InnerWrapper()
    wrapper.run()


if __name__ == "__main__":
    main()
