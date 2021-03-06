# Copyright 2020 The Johns Hopkins University Applied Physics Laboratory LLC
# All rights reserved.
# Distributed under the terms of the MIT License.


import glob
import sys
import logging

sys.path.append("/")
from outer_wrapper import OuterWrapper
from GenerationSimulation import gen_nerc


class InnerWrapper(OuterWrapper):
    def __init__(self):
        num_input_schemas = len(glob.glob("/opt/schemas/input/*.json"))
        super().__init__(
            model_id="power_supply", num_expected_inputs=num_input_schemas
        )

    def configure(self, **kwargs):
        if "nerc_energy_profiles" in kwargs.keys():
            self.prof = kwargs["nerc_energy_profiles"]
        else:
            logging.warning(
                f"incstep {self.incstep}: nerc_energy_profiles not found"
            )
        if "2016_demand" in kwargs.keys():
            self.dem = self.translate(
                data=kwargs["2016_demand"],
                src="county",
                dest="nerc",
                variable="2016_power_demand",
            )
        else:
            logging.warning(f"incstep {self.incstep}: 2016_demand not found")

    def increment(self, **kwargs):
        if "power_demand" in kwargs.keys():
            self.dem = kwargs["power_demand"]["power_demand"]["data"]
        elif self.incstep > 1:
            logging.warning(f"incstep {self.incstep}: power_demand not found")

        emissions, water = gen_nerc(self.dem, self.prof)

        results = {
            "power_supply": {
                "co2": {"data": emissions, "granularity": "nerc"},
                "thermo_water": {"data": water, "granularity": "nerc"},
            }
        }
        return results


def main():
    wrapper = InnerWrapper()
    wrapper.run()


if __name__ == "__main__":
    main()
