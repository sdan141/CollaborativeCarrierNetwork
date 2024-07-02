import yaml
import utilities as utils
import random

class CostModel:

    def __init__(self, cost_model):
        self.a1 = float(cost_model['base_price'])
        self.a2 = float(cost_model['kilometerPrice'])
        self.b1 = float(cost_model['loadingRate']) 
        self.b2 = float(cost_model['kilometerCost'])
        self.sell_threshhold = float(cost_model['sell_threshold'])
        self.buy_threshold = float(cost_model['buy_threshold'])
        print(f"Cost model[base_price: {self.a1} kilometer_price: {self.a2} loading_rate: {self.b1} kilometer_cost: {self.b2} sell below: {self.sell_threshhold} minimum profit: {self.buy_threshold}]")

    def get_mariginal_revenue(self, loc_pickup, loc_dropoff):
        margin_revenue = self.a1 + self.a2 * (utils.get_distance(loc_pickup, loc_dropoff, mode='manhattan') / 1000)
        print(f"Distnace: {utils.get_distance(loc_pickup, loc_dropoff, mode='manhattan')}")
        return margin_revenue

    def get_marginal_cost(self, marginal_distance, n_jobs=1):
        margin_cost = n_jobs * self.b1 + self.b2 * (marginal_distance / 1000)
        return margin_cost

    def get_marginal_profit(self, marginal_revenue, marginal_cost):
        return marginal_revenue - marginal_cost
