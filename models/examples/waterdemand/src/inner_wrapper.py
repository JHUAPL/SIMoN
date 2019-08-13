import glob
import sys
sys.path.append('/')
from outer_wrapper import OuterWrapper
from Water_Demand_Model import Water_Demand_Simulation
from bokeh_county_map import CountyMap

class InnerWrapper(OuterWrapper):

    def __init__(self):
        num_input_schemas = len(glob.glob("/opt/schemas/input/*.json"))
        super().__init__(model_id="waterdemand", num_expected_inputs=num_input_schemas)

    def configure(self, **kwargs):
        if 'rates' in kwargs.keys():
            self.rate=kwargs['rates']
        if '2016 populations' in kwargs.keys(): #instead of 2016 populations would put the name of the 2015 water consumption rate
            self.countypop = kwargs['2016 populations']
#replace the populations with the 2015 water consumption rate
#need to take out the extra variable 
    def increment(self, **kwargs):
        if 'population' in kwargs.keys():
            self.countypop = kwargs['population']['population']['data']
        else:
            print('input population not found')
        demand = Water_Demand_Simulation(self.countypop, self.rate)
        translated_demand = self.translate(demand, 'county', 'HUC8', self.model_id)

        html = CountyMap(demand) 

        results = {'waterdemand': {'waterdemand': {'data': translated_demand, 'granularity': 'HUC8'}}}
        htmls = {"water_demand_inc{}.html".format(self.incstep): html}
        images = {}
        return results, htmls, images


def main():
    wrapper = InnerWrapper()
    wrapper.run()


if __name__ == "__main__":
    main()
