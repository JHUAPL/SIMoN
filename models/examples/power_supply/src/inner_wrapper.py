import glob
import sys
sys.path.append('/')
from outer_wrapper import OuterWrapper
from GenerationSimulation import gen_sim

class InnerWrapper(OuterWrapper):

    def __init__(self):
        num_input_schemas = len(glob.glob("/opt/schemas/input/*.json"))
        super().__init__(model_id="power_supply", num_expected_inputs=num_input_schemas)

    def configure(self, **kwargs):
        if 'state_energy_profiles' in kwargs.keys():
            self.prof = kwargs['state_energy_profiles']
        else:
            print('State profile data not found')
        if '2016 demand' in kwargs.keys():
            self.dem = kwargs['2016 demand']

    def increment(self, **kwargs):
        if 'power_demand' in kwargs.keys():
            self.dem = kwargs['power_demand']['power_demand']['data']
        else:
            print('input demand not found')
        emissions, water = gen_sim(self.dem, self.prof)
        translated_emissions = self.translate(emissions, 'county', 'NERC', self.model_id)
        translated_water = self.translate(water, 'county', 'NERC', self.model_id)

        results = {'power_output': { 'co2': {'data': translated_emissions, 'granularity': 'NERC'},
                'thermo_water': {'data': translated_water, 'granularity': 'NERC'}}}
        return results, {}, {}

def main():
    wrapper = InnerWrapper()
    wrapper.run()


if __name__ == "__main__":
    main()
