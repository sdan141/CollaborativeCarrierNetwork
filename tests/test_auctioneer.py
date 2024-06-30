import unittest
import sys
sys.path.insert(0, '/group09/Agent_Infrastructure')
from Agent_Infrastructure.offer import Offer
from Agent_Infrastructure.auctioneer import Auctioneer
import Agent_Infrastructure.utilities as utils

class Test_Auctioneer(unittest.TestCase):
    
    def __init__(self, *args, **kwargs):
        super(Test_Auctioneer, self).__init__(*args, **kwargs)
        self.auctioneer = Auctioneer()
        self.offers_df = utils.generate_random_requests(n=6)
        self.revenues = [280, 400, 260, 220, 100, 240]
        self.profits = [100, 200, 50, 36, 80, 90]
        
        # populate offers in auctioneer
        for i, offer in self.offers_df.iterrows():
            offer_id = 'offer' + str(i+1)
            loc_pickup = {
                "pos_x": offer.pickup_long, 
                "pos_y": offer.pickup_lat
            }
            loc_dropoff = {
                "pos_x": offer.delivery_long, 
                "pos_y": offer.delivery_lat
            }
            revenue = self.revenues[i]
            profit = self.profits[i]
            self.auctioneer.offers.append(Offer('carrier_'+str(i+1), offer_id, loc_pickup, loc_dropoff, revenue=revenue, profit=profit))
    
    def test_generate_bundles(self):
        self.auctioneer.generate_bundles(bundle_size=2)
        # ensure all bundles have size bundle_size, except potentially the last one
        bundles = list(self.auctioneer.bundles.values())
        bundle_size = len(bundles[0])
        for i in range(len(bundles) - 1):
            self.assertEqual(len(bundles[i]), bundle_size)
        # check the last bundle
        if len(bundles) > 0:
            last_bundle_size = len(bundles[-1])
            self.assertTrue(last_bundle_size <= bundle_size, f"Last bundle size is {last_bundle_size}, expected <= {bundle_size}")
        # check that correct bundles order
        expected_bundles = [['offer5', 'offer2', 'offer4', 'offer1'], ['offer6', 'offer3']]
        self.assertEqual(bundles, expected_bundles)

    def test_check_active_carriers(self):
        self.auctioneer.registered_carriers = ['carrier1', 'carrier2']
        self.auctioneer.active_carriers = ['carrier1']
        self.auctioneer.check_active_carriers()
        self.assertEqual(self.auctioneer.registered_carriers, self.auctioneer.active_carriers)

    def test_update_auction_list(self):
        offer_sold = self.auctioneer.offers[0].offer_id
        self.auctioneer.offers[0].winner = "shachar"
        self.auctioneer.update_auction_list()
        self.assertTrue(all(offer.winner == "NONE" for offer in self.auctioneer.offers))
        self.assertNotIn(offer_sold, [offer.offer_id for offer in self.auctioneer.offers])

    def test_valide_bids_for_unsold_offer(self):
        self.auctioneer.offers[1].bids = {'bid1': 160, 'bid2': 170}
        self.auctioneer.offers[2].bids = {'bid1': 260, 'bid2': 270}
        self.assertTrue(self.auctioneer.valide_bids_for_unsold_offer())
    
    def test_no_valide_bids_for_unsold_offer(self):
        self.auctioneer.offers[3].bids = {'bid1': 10, 'bid2': 17}
        self.auctioneer.offers[2].bids = {'bid1': 40, 'bid2': 25}
        self.assertFalse(self.auctioneer.valide_bids_for_unsold_offer())

    def test_calculate_share(self):
        self.auctioneer.generate_bundles(bundle_size=2)
        current_bundle_set = set(self.auctioneer.bundles[0])
        self.auctioneer.indices_on_auction = [i for i, offer in enumerate(self.auctioneer.offers) if offer.offer_id in current_bundle_set]
        bid = 500
        share = self.auctioneer.calculate_share('offer1', bid)
        total_revenue = 280 + 400 + 220 + 100
        single_revenue = 280
        expected_share = (single_revenue/total_revenue) * bid 
        self.assertEqual(share, expected_share)  

if __name__ == '__main__':
    unittest.main()