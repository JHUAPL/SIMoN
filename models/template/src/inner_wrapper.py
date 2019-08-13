import glob
import sys
sys.path.append('/')
from outer_wrapper import OuterWrapper


class InnerWrapper(OuterWrapper):

    def __init__(self):
        num_input_schemas = len(glob.glob("/opt/schemas/input/*.json"))
        super().__init__(model_id="unique_model_name", num_expected_inputs=num_input_schemas)
        self.data = None

    def configure(self, **kwargs):
        self.data = kwargs['schema_name']

    def increment(self, **kwargs):
        return {'schema_name': {'data_variable_name': {'data': {}, 'granularity': 'county'}}}


def main():
    wrapper = InnerWrapper()
    wrapper.run()


if __name__ == "__main__":
    main()
