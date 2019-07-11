import glob
import os
import sys
sys.path.append('/')
from outer_wrapper import OuterWrapper
from armington import ArmingtonTrade

from bokeh.plotting import figure
from bokeh.embed import file_html
from bokeh.resources import CDN
from bokeh.layouts import column
colors = ["red", "green", "blue"]
labels = ["wheat", "rice", "cassava"]
TOOLS = "pan, box_zoom, wheel_zoom, undo, redo, reset, hover, save"

TOOLTIPS = [
("price", "$y"),
("year", "$x{int}"),
]

class InnerWrapper(OuterWrapper):

    def __init__(self):
        num_input_schemas = len(glob.glob("/opt/schemas/input/*.json"))
        super().__init__(model_id="armington", num_expected_inputs=num_input_schemas)
        self.elasticity = None
        self.initial_prices = None
        self.initial_consumption = None

        self.initial_year = 2020

        self.new_prices_series = [ [1, 2, 3], [2, 4, 5], [1, 2, 3] , [1, 1, 1], [5, 4, 1], [10, 8, 2], [15, 10, 2], [2, 2, 2], [4, 4, 4], [3, 6, 9] ]
        self.new_consumption_series = []
        self.delta_series = []

    def configure(self, **kwargs):
        self.elasticity = kwargs['config']['elasticity']
        self.initial_prices = kwargs['config']['initial_prices']
        self.initial_consumption = kwargs['config']['initial_consumption']
        self.trade = ArmingtonTrade(self.elasticity, self.initial_consumption, self.initial_prices)

    def increment(self, **kwargs):
        print(kwargs.keys())
        consumption, delta = self.trade.run(self.new_prices_series[self.incstep])
        self.new_consumption_series.append(consumption)
        self.delta_series.append(delta)
        consumption_dict = {}
        for i in range(len(consumption)):
            consumption_dict["crop{}".format(i)] = consumption[i]

        # prices
        prices_plot = figure(title="Prices", plot_width=400, plot_height=400, tools=TOOLS, tooltips=TOOLTIPS)
        for i in range(3):
            prices = [series[i] for series in self.new_prices_series[:len(self.new_consumption_series)]]
            prices_plot.line(range(self.initial_year, self.initial_year + len(self.new_prices_series)), prices, line_width=2, legend=labels[i], line_color=colors[i])

        # consumption
        consumption_plot = figure(title="Consumption (elasticity = {})".format(self.elasticity), plot_width=400, plot_height=400, tools=TOOLS, tooltips=TOOLTIPS)
        for i in range(3):
            consumption = [series[i] for series in self.new_consumption_series]
            consumption_plot.line(range(self.initial_year, self.initial_year + len(self.new_prices_series)), consumption, line_width=2, legend=labels[i], line_color=colors[i])

        html = file_html(column(prices_plot, consumption_plot), CDN, title="armington")
 
        results = {'armington': {'consumption': {'data': consumption_dict, 'granularity': 'national'}, 'gdp_delta': {'data': {'gdp_delta': delta, 'year_actual': self.initial_year + self.incstep, 'ccode': '500'}, 'granularity': 'national'}}}
        htmls = {"armington_inc{}.html".format(self.incstep): html}
        images = {}
        return results, htmls, images


def main():
    wrapper = InnerWrapper()
    wrapper.run()


if __name__ == "__main__":
    main()
