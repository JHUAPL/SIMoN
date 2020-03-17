# Copyright 2020 The Johns Hopkins University Applied Physics Laboratory LLC
# All rights reserved.
# Distributed under the terms of the MIT License.


import pandas as pd


def pow_dem_sim(pop, cons):

    temp = {}

    count = pd.DataFrame(pop, index=["pop"])
    count = count.T
    count.reset_index(inplace=True)
    count["State"] = count["index"].apply(lambda x: x[:-3])
    state_pops = count.groupby("State").sum().reset_index()
    count = pd.merge(count, state_pops, on="State", how="left")
    count["perc"] = count.apply(lambda x: x.pop_x / x.pop_y, axis=1)

    cons_pc = pd.DataFrame(cons, index=["cons"])
    cons_pc = cons_pc.T

    count = pd.merge(
        count,
        cons_pc.reset_index(),
        left_on="State",
        right_on="index",
        how="left",
    )
    # simply multiplies current pop by state consumption per capita
    count["demand"] = count.apply(
        lambda x: (x.pop_y * x.cons) * x.perc, axis=1
    )
    count = count[["index_x", "demand"]].set_index("index_x")

    for index, row in count.iterrows():
        temp[index] = row["demand"]

    return temp
