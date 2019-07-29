import glob
import sys
sys.path.append('/')
from outer_wrapper import OuterWrapper
from LogisticGrowth import populationfunction

class InnerWrapper(OuterWrapper):

    def __init__(self):
        num_input_schemas = len(glob.glob("/opt/schemas/input/*.json"))
        super().__init__(model_id="logisticpopulation", num_expected_inputs=num_input_schemas)

    def configure(self, **kwargs):
        if '2016 populations' in kwargs.keys():
            self.population = kwargs['2016 populations'] 
        else:
            print('population initialization data not found')

    def increment(self, **kwargs):
        #if 'logisticpopulation' in kwargs.keys():
        #    self.population = kwargs['logistispopulation']['logisticpopulation']['data']
        #else:
        #    print('input population not found')

        population = populationfunction(self.population)
        self.population=population
        return {'logisticpopulation': {'logisticpopulation': {'data': population, 'granularity': 'county'}}}


def main():
    wrapper = InnerWrapper()
    wrapper.run()


if __name__ == "__main__":
    main()
