import glob
import sys
sys.path.append('/')
from outer_wrapper import OuterWrapper
import pyhector
import json


class InnerWrapper(OuterWrapper):

    def __init__(self):
        num_input_schemas = len(glob.glob("/opt/schemas/input/*.json"))
        super().__init__(model_id="hector", num_expected_inputs=num_input_schemas)

    def configure(self, **kwargs):
        self.rcp = kwargs['bootstrap']['rcp']

    def increment(self, **kwargs):
        if self.rcp == "rcp26":
            print("rcp26")
            pandas_df = pyhector.run(pyhector.rcp26)
        else:
            print("rcp85")
            pandas_df = pyhector.run(pyhector.rcp85)

        return {'climate': {'climate': {'data': json.loads(pandas_df["temperature.Tgav"].to_json()), 'granularity': 'global'}}}


def main():
    wrapper = InnerWrapper()
    wrapper.run()


if __name__ == "__main__":
    main()
