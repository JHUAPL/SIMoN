# -*- coding: utf-8 -*-
"""
Created on Wed Jul 11 11:38:23 2018

@author: ponzodj1
"""

import json

from statsmodels.tsa.holtwinters import Holt
import pandas as pd
import numpy as np


def pop_sim(init_data):

    try:
        with open('updated_populations.json') as file:
            data = json.loads([x for x in file][0])
    except FileNotFoundError:
        data = init_data

    # Creates a temp dict, iterates through the loaded json data dict in the form
    # of {county1_index: {2000: pop, 2001: pop, etc}, county2_index:...}
    # applies Holt linear trend method to predict one year ahead
    # outputted data is dict of {county_index: next_year_pop}
    
    temp = {}

    for key, county in data.items():
        population = pd.Series(county)
        fit1 = Holt(np.asarray(population)).fit(smoothing_level=0.7, smoothing_slope=0.3)
        next_year = fit1.forecast(1)[0]
        temp[key] = next_year
        data[key][str(int(max(data[key].keys())) + 1)] = next_year

    with open('updated_populations.json', 'w') as file:
        file.write(json.dumps(data))

    return temp

