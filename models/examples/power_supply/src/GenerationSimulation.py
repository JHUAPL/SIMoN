# Copyright 2020 The Johns Hopkins University Applied Physics Laboratory LLC
# All rights reserved.
# Distributed under the terms of the MIT License.


import pandas as pd


def gen_state(demand, prof):

    counties = (
        pd.DataFrame(demand, index=["demand"])
        .T.reset_index()
        .rename(columns={"index": "county"})
    )
    counties["state"] = counties.county.apply(lambda x: x[:-3])
    state_demand = counties.groupby("state")["demand"].sum()
    state_prof = (
        pd.DataFrame(prof).T.reset_index().rename(columns={"index": "state"})
    )
    state_demand = state_demand.to_frame().reset_index()
    counties = pd.merge(counties, state_demand, on="state", how="left")
    counties = pd.merge(counties, state_prof, on="state", how="left")
    counties["Fuel Used (MMBtu)"] = counties.apply(
        lambda x: (x["MMBtu per MWh"]) * (x.demand_x), axis=1
    )
    counties["CO2 Emissions (tons)"] = counties.apply(
        lambda x: (x["Tons CO2 per MWh"]) * (x.demand_x), axis=1
    )
    counties["Water Used (Mgal)"] = counties.apply(
        lambda x: (x["Mgal_per_MWh"]) * (x.demand_x), axis=1
    )
    counties = counties[
        [
            "county",
            "Fuel Used (MMBtu)",
            "CO2 Emissions (tons)",
            "Water Used (Mgal)",
        ]
    ].set_index("county")

    co2 = {}
    h2o = {}
    for index, row in counties.iterrows():
        co2[index] = row["CO2 Emissions (tons)"]
        h2o[index] = row["Water Used (Mgal)"]

    return co2, h2o


def gen_nerc(demand, profile_rates):

    co2 = {}
    h2o = {}

    for nerc in demand:
        co2[nerc] = demand[nerc] * profile_rates.get(nerc, {}).get("co2 (tons/MWh)", 0)
        h2o[nerc] = demand[nerc] * profile_rates.get(nerc, {}).get("water (Mgal/MWh)", 0)

    return co2, h2o
