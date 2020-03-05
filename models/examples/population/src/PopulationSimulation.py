# Copyright 2020 The Johns Hopkins University Applied Physics Laboratory LLC
# All rights reserved.
# Distributed under the terms of the MIT License.


from statsmodels.tsa.holtwinters import Holt
import pandas as pd
import numpy as np


def pop_sim(init_data, num_increments):

    data = init_data

    for key, county in init_data.items():
        population = pd.Series(county)

        # https://www.statsmodels.org/stable/examples/notebooks/generated/exponential_smoothing.html#Holt's-Method
        fit1 = Holt(np.asarray(population)).fit(
            smoothing_level=0.7, smoothing_slope=0.3
        )
        future_pop = fit1.forecast(num_increments)

        last_inc = int(max(data[key].keys()))
        for inc, value in zip(range(num_increments), future_pop):
            data[key][str(last_inc + 1 + inc)] = value

    return data


def get_data(data, year):

    current_year = {}

    for county, values in data.items():
        current_year[county] = values[str(year)]

    return current_year
