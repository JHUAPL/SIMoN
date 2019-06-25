import glob
import sys
sys.path.append('/')
from outer_wrapper import OuterWrapper
from Water_Demand_Model import waterdemand1

class InnerWrapper(OuterWrapper):

    def __init__(self):
        num_input_schemas = len(glob.glob("/opt/schemas/input/*.json"))
        super().__init__(model_id="waterdemand", num_expected_inputs=num_input_schemas)

    def configure(self, **kwargs):
        if 'rates' in kwargs.keys():
            self.rate=kwargs['rates']
#replace the populations with the 2015 water consumption rate
#need to take out the extra variable 
    def increment(self, **kwargs):
        if 'population' in kwargs.keys():
            self.countypop = kwargs['population']['population']['data']
        else:
            print('input population not found')
        if 'rate' in kwargs.keys()
            self.rate = kwargs['population']['data']
        else:
            print('input rate not found')
        demand = Water_Demand_Simulation(self.countypop)
       
        return {'waterdemand': {'waterdemand': {'data': demand, 'granularity': 'county'}}}


def main():
    wrapper = InnerWrapper()
    wrapper.run()


if __name__ == "__main__":
    main()
