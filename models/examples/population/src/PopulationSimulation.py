# Copyright 2020 The Johns Hopkins University Applied Physics Laboratory LLC
# All rights reserved.
# Distributed under the terms of the MIT License.


from statsmodels.tsa.holtwinters import Holt
import pandas as pd
import numpy as np
import json


def pop_sim(init_data):

    try:
        with open('updated_populations.json') as file:
            data = json.loads([x for x in file][0])
    except FileNotFoundError:
        data = init_data

    temp = {}

    # data: {county1_index: {2000: pop, 2001: pop, etc}, county2_index:...}
    for key, county in data.items():
        population = pd.Series(county)
        # applies Holt linear trend method to predict one year ahead
        fit1 = Holt(np.asarray(population)).fit(
            smoothing_level=0.7, smoothing_slope=0.3
        )
        next_year = fit1.forecast(1)[0]
        temp[key] = next_year
        data[key][str(int(max(data[key].keys())) + 1)] = next_year

    with open('updated_populations.json', 'w') as file:
        file.write(json.dumps(data))

    # output data is dict of {county_index: next_year_pop}
    return temp
