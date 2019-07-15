import glob
import sys
sys.path.append('/')
from outer_wrapper import OuterWrapper
from PopulationSimulation import pop_sim
from bokeh_county_map import CountyMap

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
        html = CountyMap(data)
        htmls = {"population_inc{}.html".format(self.incstep): html}
        results = {'population': {'population': {'data': data, 'granularity': 'county'}}}
        return results, htmls, {}
#is taking in the data from the previous run

def main():
    wrapper = InnerWrapper()
    wrapper.run()


if __name__ == "__main__":
    main()
