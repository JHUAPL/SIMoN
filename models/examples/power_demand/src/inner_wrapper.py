import glob
import sys
sys.path.append('/')
from outer_wrapper import OuterWrapper
from DemandSimulation import pow_dem_sim #for water demand, going to do something similar ##

class InnerWrapper(OuterWrapper):

    def __init__(self):
        num_input_schemas = len(glob.glob("/opt/schemas/input/*.json"))
        super().__init__(model_id="power_demand", num_expected_inputs=num_input_schemas)

    def configure(self, **kwargs): #this would be the water consumption rate in here 
        if 'state consumption per capita' in kwargs.keys(): #instead of state, do water 2015, the json we made
            self.cons = kwargs['state consumption per capita'] #copy the file name 
        else:
            print('State consumption data not found')
        if '2016 populations' in kwargs.keys(): #instead of 2016 populations would put the name of the 2015 water consumption rate
            self.pop = kwargs['2016 populations']

    def increment(self, **kwargs): #this is handling all the new data that is coming from other models, the whole function would be similar besides power instead of water
        if 'population' in kwargs.keys():
            self.pop = kwargs['population']['population']['data'] #assume you can keep as is for now and it may work
        else:
            print('input population not found')
        demand = pow_dem_sim(self.pop, self.cons) #instead of power demand simulation, have water demand, your inputs will be population and consumption rate, #do water demand sim, #and change inputs to the actual name of our arguments 

        results = {'power_demand': {'power_demand': {'data': demand, 'granularity': 'county'}}} #obviously this will all say water demand isntead of power demand 
#checks to see if it has data on population, writes it to selfpop and outputs power demand
    #does not use self because it doesnt use its own previous data 
        return results, {}, {}

def main():
    wrapper = InnerWrapper()
    wrapper.run()


if __name__ == "__main__":
    main()
