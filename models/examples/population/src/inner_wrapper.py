import glob
import sys
sys.path.append('/')
from outer_wrapper import OuterWrapper
from PopulationSimulation import pop_sim

class InnerWrapper(OuterWrapper):

    def __init__(self):
        num_input_schemas = len(glob.glob("/opt/schemas/input/*.json"))
        super().__init__(model_id="population", num_expected_inputs=num_input_schemas)

    def configure(self, **kwargs):
        if 'county_populations' in kwargs.keys():
            self.data = kwargs['county_populations'] 
        else:
            print('population initialization data not found')

    def increment(self, **kwargs):
        data = pop_sim(self.data)
        self.data = data

        state = self.translate(data, 'county', 'state', self.model_id)
        US = self.translate(data, 'county', 'UnitedStates', self.model_id)
        NERC = self.translate(data, 'county', 'NERC', self.model_id)
        HUC8 = self.translate(data, 'county', 'HUC8', self.model_id)
        HUC12 = self.translate(data, 'county', 'HUC12', self.model_id)
        HUC12_2 = self.translate(HUC8, 'HUC8', 'HUC12', self.model_id)
        climate = self.translate(data, 'county', 'climate', self.model_id)
        tract = self.translate(data, 'county', 'tract', self.model_id)
        county = self.translate(US, 'UnitedStates', 'county', self.model_id)
        #NERC_county = self.translate(data, 'county', 'NERC^county', self.model_id)
        return {'population': {'population': {'data': {'US': US, 'state': state, 'NERC': NERC, 'HUC8': HUC8 }, 'granularity': 'US'}}}

        state_to_US = self.translate(state, 'state', 'UnitedStates', self.model_id)
        county_to_US = self.translate(county, 'county', 'UnitedStates', self.model_id)
        tract_to_US = self.translate(tract, 'tract', 'UnitedStates', self.model_id)
        HUC8_to_US = self.translate(HUC8, 'HUC8', 'UnitedStates', self.model_id)
        HUC12_to_US = self.translate(HUC12, 'HUC12', 'UnitedStates', self.model_id)
        HUC12_2_to_US = self.translate(HUC12_2, 'HUC12', 'UnitedStates', self.model_id)
        NERC_to_US = self.translate(NERC, 'NERC', 'UnitedStates', self.model_id)
        climate_to_US = self.translate(climate, 'climate', 'UnitedStates', self.model_id)
        #NERC_county_to_US = self.translate(NERC_county, 'NERC^county', 'UnitedStates', self.model_id)
        #return {'population': {'population': {'data': {'US': US, 'climate': climate_to_US, 'HUC8': HUC8_to_US, 'HUC12': HUC12_to_US, 'HUC12_2': HUC12_2_to_US, 'tract': tract_to_US, 'NERC': NERC_to_US, 'state': state_to_US, 'county': county_to_US}, 'granularity': 'US'}}}


def main():
    wrapper = InnerWrapper()
    wrapper.run()


if __name__ == "__main__":
    main()
