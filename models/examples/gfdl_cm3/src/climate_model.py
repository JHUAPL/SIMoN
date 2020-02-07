"""
Created on Wed Jul 10 2019

@author: afiallo1
"""

import numpy as np
import json


def temp_inc(init_data, year):
    json1_data = init_data
    year = year-1
    mean_glob_temps = []
    with open("/opt/src/weights.json") as f:
        weights = json.load(f)

    single_year_US = {}
    # Go through the json divided into lat,lon grid squares

    for i in json1_data:
        if 49 >= float(i) >= 23:
            # Convert to format that plays nice with mongodb; only get U.S squares
            single_year_US[i] = {}
        for j in json1_data[i]:
            # Use two outputs, single global mean temperature and gridded climate data
            mean_glob_temps.append(json1_data[i][j][year][2])

            # Contiguous U.S bounded by (49 N, 122W), (24N 66W)
            if 49 >= float(i) >= 23 and -68 >= float(j) >= -128:
                single_year_US[i][j] = (
                    json1_data[i][j][year][0], json1_data[i][j][year][1], json1_data[i][j][year][2]-273.15
                )

    # Apply weights
    weighted_sum = np.sum([a*b for a, b in zip(mean_glob_temps, weights)])

    # Output: Global average (C) +
    # grid of U.S (precipitation (mm), evaporation (mm), surface temp(C))
    translated_pr = {}
    translated_ev = {}
    for lat, lat_values in single_year_US.items():
        for lon, lon_values in lat_values.items():
            lon = float(lon)
            if lon < 0:
                lon += 180
            translated_pr["lat_" + str(lat) + "_lon_" + str(lon)] =  lon_values[0]
            translated_ev["lat_" + str(lat) + "_lon_" + str(lon)] =  lon_values[1]

    return weighted_sum-273.15, translated_pr, translated_ev #single_year_US
