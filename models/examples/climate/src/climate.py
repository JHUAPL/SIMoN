import fair
from fair.forward import fair_scm
import numpy as np
import json

# need to iterate through another dictionary that has counties as values
# sum up the values set equaal to new variable
# scale it then CFT
def temperature_simulation(electric):
    total = sum(list(filter(None, electric.values())))
    # emissions[i]=
    emissions = np.array(total)
    # other_rf = np.zeros(emissions.size)

    # for x in range(0, emissions.size):
    # 	other_rf[x] = 0.5 * np.sin(2 * np.pi * (x) / 14.0)

    # emissions=emissions*6.66667*3.5714285 #scaling factors

    C, F, T = fair.forward.fair_scm(
        emissions_driven=True,
        emissions=np.array([emissions * 6.66667 * 3.5714285]),
        useMultigas=False,
    )

    return T


# temperature_simulation({'co2':{'data':{5646:9.9,489247:6,234708:4.5}},'therm':[2,3,2]})
