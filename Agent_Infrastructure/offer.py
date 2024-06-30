import numpy as np


class Offer:

    def __init__(self, carrier_id, offer_id, loc_pickup, loc_dropoff, profit=None, revenue=None, cost=None, winning_bid="NONE", winner="NONE"):
        self.carrier_id = carrier_id    
        self.offer_id = offer_id # [offer_id]        
        self.loc_pickup = loc_pickup # [(x,y)] dict {x_pos:, y_pos:} => {x_pos:[..], ..}
        self.loc_dropoff = loc_dropoff
        self.profit = profit
        self.revenue = revenue
        self.cost = cost
        self.bids = {}     
        self.on_auction = False     
        self.winner = winner     
        self.winning_bid = winning_bid        

    def add_bid(self, bidder ,bid):
        self.bids[bidder] = bid

    def get_second_highest_bid(self):
        if not self.bids.values():
            return False 
        else:
            sorted_bids = sorted(self.bids.items(), key=lambda k: k[1])
            second_highest_bid = sorted_bids[1][1]
            winner = sorted_bids[0][0]
            if second_highest_bid <= self.profit:
                return False
            return winner, second_highest_bid
        
    def get_highest_bid(self):
        if not self.bids.values():
            return False 
        else:
            highest_bid = max(self.bids.items(), key=lambda k: k[1])
            if highest_bid[1] <= self.profit:
                return False
            return highest_bid

    def update_results(self, mode=None):
        if mode=='vickrey':
            highest_bid = self.get_second_highest_bid()
        else:
            highest_bid = self.get_highest_bid()
        if highest_bid:
            winner_carrier_id, winning_bid = highest_bid
        else:
            winner_carrier_id, winning_bid = ("NONE", "NONE")
        
        self.winner = winner_carrier_id
        self.winning_bid = winning_bid

    def to_dict(self, show_profit=False, show_cost=False):
        offer_dict= {
            "offeror": self.carrier_id,
            "winner": self.winner,
            "winning_bid": self.winning_bid,
            "offer_id": self.offer_id,
            "loc_pickup": self.loc_pickup,
            "loc_dropoff": self.loc_dropoff,
            "revenue": self.revenue
        }
        if show_cost:
            offer_dict['cost']=self.cost 
        if show_profit:
            offer_dict['profit']=self.profit

        return offer_dict
