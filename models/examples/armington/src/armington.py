#!/usr/bin/env python
# coding: utf-8

# inputs: s (elasticity), original price vector, original consumption vector (basket of goods), new price vector for each future year
# intermediate output: gamma preferences
# final ouput: new consumption vector -> change in real GDP

import sys
from numpy import dot, inf
from scipy.optimize import root, least_squares


class ArmingtonTrade:

    def __init__(self, s=2, consumption=[395976, 2934230, 281522], prices=[190, 215, 475]):
        self.s = s
        print("elasticity: {}".format(s))
        # wheat, rice, cassava
        self.original_consumption = consumption
        print("wheat, rice, cassava")
        print("initial consumption basket: {}".format(consumption))
        self.original_prices = prices
        print("initial prices: {}".format(prices))


    def sys_eqs_for_preferences(self, g, s, p, B, c):
        
        assert len(p) == len(c)
        
        # calculate utility
        r = 1 - 1/s
        U = 0
        for i in range(len(p)):
            U += (g[i+1]*c[i])**r
        U = U**(1/r)

        # build the system of equations to solve
        F = [None] * (len(p) + 2)
        F[0] = U/B - g[0]
        F[-1] = sum([g[i+1] for i in range(len(p))]) - 1
        F[-1] = sum(g) - g[0] - 1
        #F[-1] = g[2] - 1
        for i in range(len(p)):
            F[i+1] = U * g[i+1]**(s-1) / (g[0] * p[i])**s - c[i]
            
        return F

    def preference_eqs(self, s, p, c):
        B = dot(p, c)
        x0 = [1 / (len(p) + 1)] * (len(p) + 1)
        x0 = [1] * (len(p) + 1)
        lb = [0] * (len(p) + 1)
        ub = [inf] + [10] * len(p)
        #pref = root(self.sys_eqs_for_preferences, x0, args=(s, B, p, c), method='lm')
        pref = least_squares(self.sys_eqs_for_preferences, x0, args=(s, p, B, c), bounds=(lb, ub))
        return pref

    def sys_eqs_for_consumption(self, c, s, p, B, g):
        
        # calculate utility
        r = 1 - 1/s
        U = 0
        for i in range(len(p)):
            U += (g[i]*c[i+1])**r
        U = U**(1/r)

        # build the system of equations to solve
        F = [None] * (len(p) + 2)
        F[0] = U/B - c[0]
        F[0] = 0
        F[-1] = dot(p, c[1:]) - B
        for i in range(len(p)):
            F[i+1] = U * g[i]**(s-1) / (c[0] * p[i])**s - c[i+1]
            
        return F

    def consumption_eqs(self, s, p, B, g):
        x0 = [1] + self.original_consumption
        #x0 = [L] + original_consumption
        lb = [0] * (len(p) + 1)
        ub = [inf] * (len(p) + 1)
        #consumption = root(self.sys_eqs_for_consumption, x0, args=(s, p, B, g), method='lm')
        consumption = least_squares(self.sys_eqs_for_consumption, x0, args=(s, p, B, g), bounds=(lb, ub))
        return consumption

    def run(self, new_prices):
        s = self.s
        results = self.preference_eqs(s, self.original_prices, self.original_consumption)
        L = list(results.x)[0]
        pref = list(results.x)[1:]

        print("lambda = {:.4f}".format(L))
        gammas = [float("{:.4f}".format(gamma)) for gamma in pref]
        print("country preferences = {}".format(gammas))
        print("sum = {:.4f}".format(sum(pref)))

        B = dot(self.original_consumption, self.original_prices)

        p = new_prices
        print("new prices: {}".format(p))
        g = pref

        results = self.consumption_eqs(s, p, B, g)
        L = list(results.x)[0]
        consumption = list(results.x)[1:]
        print("lambda = {:.4f}".format(L))

        print("new consumption basket: {}".format(["{:.2f}".format(c) for c in consumption]))
        changes = [(c - original)/original for c, original in zip(consumption, self.original_consumption)]

        delta = ( dot(self.original_prices, consumption) - dot(self.original_prices, self.original_consumption) ) / dot(self.original_prices, self.original_consumption)
        print("percent change in GDP: {:.2f}%".format(delta*100))
        print("net change in GDP: {}".format(dot(self.original_prices, consumption) - dot(self.original_prices, self.original_consumption)))

        return consumption, delta

