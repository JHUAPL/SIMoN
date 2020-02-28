# Copyright 2020 The Johns Hopkins University Applied Physics Laboratory LLC
# All rights reserved.
# Distributed under the terms of the MIT License.


import numpy as np
import json


def temp_inc(init_data, year):
    json1_data = init_data
    mean_glob_temps = []
    with open("/opt/src/weights.json") as f:
        weights = json.load(f)

    single_year_US = {}

    for i in json1_data:
        if 49 >= float(i) >= 23:
            # convert to format that plays nice with mongodb; only get U.S squares
            single_year_US[i] = {}
        for j in json1_data[i]:
            mean_glob_temps.append(json1_data[i][j][year][2])

            # contiguous United States boundaries
            if 49 >= float(i) >= 23 and -68 >= float(j) >= -128:
                single_year_US[i][j] = (
                    json1_data[i][j][year][0],
                    json1_data[i][j][year][1],
                    json1_data[i][j][year][2] - 273.15,
                )

    # apply weights to get global average temperature
    weighted_sum = np.sum([a * b for a, b in zip(mean_glob_temps, weights)])

    # convert Kelvin to Celsius
    temperature = weighted_sum - 273.15

    translated_pr = {}
    translated_ev = {}
    for lat, lat_values in single_year_US.items():
        for lon, lon_values in lat_values.items():
            lat = float(lat)
            lon = float(lon)
            if lon < 0:
                lon += 180

            # precipitation (mm)
            translated_pr[f"lat_{int(lat*100)}_lon_{int(lon*100)}"] = lon_values[0]
            # evaporation (mm)
            translated_ev[f"lat_{int(lat*100)}_lon_{int(lon*100)}"] = lon_values[1]

    return (
        temperature,
        translated_pr,
        translated_ev,
    )
