# Copyright 2020 The Johns Hopkins University Applied Physics Laboratory LLC
# All rights reserved.
# Distributed under the terms of the MIT License.


def Water_Demand_Simulation(countypop, rates, thermo_water):

    water = {}
    for i in rates:
        water[i] = thermo_water.get(i, 0) + countypop.get(i, 0) * rates[i]
    return water
