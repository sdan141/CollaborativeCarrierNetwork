class Auction:
    def __init__(self, offers):
        
        self.bundle = offers if type(offers) is list else [offers]
        self.revenue = sum([offer.revenue for offer in offers])
        self.bids = {}

    def add_bid(self, bidder ,bid):
        self.bids[bidder] = bid

    def get_highest_bid(self):
        if not any(list(self.bids.values())):
            return None 
        else:
            highest_bid = max(self.bids.items(), key=lambda k: k[1])
            return highest_bid
    
    def update_results(self):
        highest_bid = self.get_highest_bid()
        if highest_bid:
            winner_carrier_id, winning_bid = highest_bid
        else:
            winner_carrier_id, winning_bid = ("NONE", "NONE")
        
        self.winner = winner_carrier_id
        self.winning_bid = winning_bid

    def to_dict(self):
        return {
            [offer.to_dict() for offer in self.bundle]
        }
    
    def calculate_shares(self):
        for offer in self.bundle:
            offer.winning_bid = (offer.revenue/self.revenue) * self.winning_bid  


class Offer:

    def __init__(self, carrier_id, offer_id, loc_pickup, loc_dropoff, profit=None, revenue=None, cost=None):
        self.carrier_id = carrier_id    
        self.offer_id = offer_id        
        self.loc_pickup = loc_pickup
        self.loc_dropoff = loc_dropoff
        self.profit = profit
        self.revenue = revenue
        self.cost = cost
        self.bids = {}     
        self.on_auction = False     
        self.winner = "NONE"      
        self.winning_bid = "NONE"         

    def add_bid(self, bidder ,bid):
        self.bids[bidder] = bid

    def get_highest_bid(self):
        if not any(list(self.bids.values())):
            return None 
        else:
            highest_bid = max(self.bids.items(), key=lambda k: k[1])
            return highest_bid
    
    def update_results(self):
        highest_bid = self.get_highest_bid()
        if highest_bid:
            winner_carrier_id, winning_bid = highest_bid
        else:
            winner_carrier_id, winning_bid = ("NONE", "NONE")
        
        self.winner = winner_carrier_id
        self.winning_bid = winning_bid

    def to_dict(self):
        return {
            "offeror": self.carrier_id,
            "winner": self.winner,
            "winning_bid": self.winning_bid,
            "offer_id": self.offer_id,
            "loc_pickup": self.loc_pickup,
            "loc_dropoff": self.loc_dropoff,
            "revenue": self.revenue
        }
