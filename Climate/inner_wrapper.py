import glob
import sys
sys.path.append('/')
from outer_wrapper import OuterWrapper
from climate_model import pr_model, tas_model, evap_model


class InnerWrapper(OuterWrapper):
    def __init__(self):
        num_input_schemas = len(glob.glob("/opt/schemas/input/*.json"))
        super().__init__(model_id="unique_model_name", num_expected_inputs=num_input_schemas)
        self.data = None

    def configure(self, **kwargs):
        self.data = kwargs['schema_name']

    def increment(self, **kwargs):
        return {'schema_name': {'data_variable_name': {'data': {}, 'granularity': 'county'}}}
# d1 = Dataset('rcp26/pr/pr_Amon_GFDL-CM3_rcp26_r1i1p1_200601-201012.nc')
# print(pr_model(d1))