import glob
import os
import sys
sys.path.append('/')
from outer_wrapper import OuterWrapper
from CivilConflict import CivilConflict

class InnerWrapper(OuterWrapper):

    def __init__(self):
        num_input_schemas = len(glob.glob("/opt/schemas/input/*.json"))
        print("num input schemas " + str(num_input_schemas))
        super().__init__(model_id="civil_conflict", num_expected_inputs=num_input_schemas)
        self.data = None
        self.gdps = []
        self.years = []

    def configure(self, **kwargs):
        self.gdp = kwargs['config']['gdp_delta']
        self.year_actual = kwargs['config']['year_actual']
        self.ccode = kwargs['config']['ccode']

    def increment(self, **kwargs):
        print(kwargs.keys())
        if 'armington' in kwargs.keys():
            self.gdp = kwargs['armington']['gdp_delta']['data']['gdp_delta']
            self.year_actual = kwargs['armington']['gdp_delta']['data']['year_actual']
            self.ccode = kwargs['armington']['gdp_delta']['data']['ccode']
        else:
            print("armington input data not found")

        self.gdps.append(self.gdp)
        self.years.append(self.year_actual)
        conflict = CivilConflict()
        html = conflict.run(self.gdps, self.years)

        results = {'civil_conflict': {'data_variable_name': {'data': {}, 'granularity': 'county'}}}
        htmls = {"civil_conflict_inc{}.html".format(self.incstep): html}
        images = {}
        return results, htmls, images

def main():
    wrapper = InnerWrapper()
    wrapper.run()


if __name__ == "__main__":
    main()
