# Copyright 2020 The Johns Hopkins University Applied Physics Laboratory LLC
# All rights reserved.
# Distributed under the terms of the MIT License.


import glob
import sys
import logging

sys.path.append("/")
from outer_wrapper import OuterWrapper
from Water_Demand_Model import Water_Demand_Simulation


class InnerWrapper(OuterWrapper):
    def __init__(self):
        num_input_schemas = len(glob.glob("/opt/schemas/input/*.json"))
        super().__init__(
            model_id="water_demand", num_expected_inputs=num_input_schemas
        )

    def configure(self, **kwargs):
        if "rates" in kwargs.keys():
            self.rate = kwargs["rates"]
        else:
            logging.warning(f"incstep {self.incstep}: rates not found")
        if "thermo_water" in kwargs.keys():
            self.thermo_water = kwargs["thermo_water"]
        else:
            logging.warning(f"incstep {self.incstep}: thermo_water not found")
            self.thermo_water = {}
        if "2016_populations" in kwargs.keys():
            self.countypop = kwargs["2016_populations"]
        else:
            logging.warning(
                f"incstep {self.incstep}: 2016_populations not found"
            )

    def increment(self, **kwargs):
        if "population" in kwargs.keys():
            self.countypop = kwargs["population"]["population"]["data"]
        elif self.incstep > 1:
            logging.warning(f"incstep {self.incstep}: population not found")

        if "power_supply" in kwargs.keys():
            self.thermo_water = kwargs["power_supply"]["thermo_water"]["data"]
        elif self.incstep > 1:
            logging.warning(f"incstep {self.incstep}: thermo_water not found")

        demand = Water_Demand_Simulation(self.countypop, self.rate, self.thermo_water)

        results = {
            "water_demand": {
                "water_demand": {"data": demand, "granularity": "county"}
            }
        }
        return results


def main():
    wrapper = InnerWrapper()
    wrapper.run()


if __name__ == "__main__":
    main()
