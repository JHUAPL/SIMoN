import glob
import sys
sys.path.append('/')
from outer_wrapper import OuterWrapper
from DemandSimulation import pow_dem_sim

class InnerWrapper(OuterWrapper):

    def __init__(self):
        num_input_schemas = len(glob.glob("/opt/schemas/input/*.json"))
        super().__init__(model_id="power_demand", num_expected_inputs=num_input_schemas)

    def configure(self, **kwargs):
        if 'state consumption per capita' in kwargs.keys():
            self.cons = kwargs['state consumption per capita']
        else:
            print('State consumption data not found')
        if '2016 populations' in kwargs.keys():
            self.pop = kwargs['2016 populations']

    def increment(self, **kwargs):
        if 'population' in kwargs.keys():
            self.pop = kwargs['population']['population']['data']
        else:
            print('input population not found')
        demand = pow_dem_sim(self.pop, self.cons)

        return {'power_demand': {'power_demand': {'data': demand, 'granularity': 'county'}}}


def main():
    wrapper = InnerWrapper()
    wrapper.run()


if __name__ == "__main__":
    main()
