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
        results = {'population': {'population': {'data': data, 'granularity': 'county'}}}
        return results, {}, {}
#is taking in the data from the previous run

def main():
    wrapper = InnerWrapper()
    wrapper.run()


if __name__ == "__main__":
    main()
