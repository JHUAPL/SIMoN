import time
import glob
from random import randint
import sys
sys.path.append('/')
from outer_wrapper import OuterWrapper


class InnerWrapper(OuterWrapper):

    def __init__(self):
        num_input_schemas = len(glob.glob("/opt/schemas/input/*.json"))
        super().__init__(model_id="water", num_expected_inputs=num_input_schemas)

    def configure(self, **kwargs):
        pass

    def increment(self, **kwargs):
        print("inner wrapper increment")
        time.sleep(randint(1, 3))
        return {'water': {'water': {'data': {}, 'granularity': 'county'}}}


def main():
    wrapper = InnerWrapper()
    wrapper.run()


if __name__ == "__main__":
    main()
