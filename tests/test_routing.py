import unittest
import sys
sys.path.insert(0, '/home/shachardan/tuhh/SW-D/group09/Agent_Infrastructure')
from routing import Routing
from offer import Offer
import utilities as utils
import numpy as np

class Test_Routing(unittest.TestCase):

    def __init__(self, *args, **kwargs):
        super(Test_Routing, self).__init__(*args, **kwargs)
        self.routing = Routing(carrier_id='carrier_1', n=5)
        for i, offer in enumerate(self.routing.offers):
            offer.offer_id = "offer_" + str(i+1)
            if i==0 or i==2:
                offer.on_auction = True

    def test_initial_locations_and_assignments(self):
        len_locations = len(self.routing.locations)
        len_assignmets = len(self.routing.assignments)
        self.assertEqual(len_locations, len(self.routing.offers)*2+1)
        self.assertEqual(len_assignmets, len(self.routing.offers))
        all_assignments = np.ravel(np.array(self.routing.assignments))
        self.assertEqual(all_assignments.tolist(), np.arange(1,len_locations).tolist())
    
    def test_add_n_locations(self, n=2):
        loc_pickups = np.round(np.random.uniform((81.9698,37.5281),(93.2898,46.2281),(n,2)), 3)
        loc_dropoffs = np.round(np.random.uniform((81.9698,37.5281),(93.2898,46.2281),(n,2)), 3)
        loc_pickups_dicts = []
        loc_dropoffs_dicts = []
        for pickup, dropoff in zip(loc_pickups, loc_dropoffs):
            loc_pickups_dicts.append({'pos_x': pickup[0], 'pos_y': pickup[1]})
            loc_dropoffs_dicts.append({'pos_x': dropoff[0], 'pos_y': dropoff[1]})
        
        len_locations_before = len(self.routing.locations)
        len_assignmets_before = len(self.routing.assignments)

        self.routing.add_location(loc_pickups_dicts, loc_dropoffs_dicts)
        
        len_locations_after = len(self.routing.locations)
        len_assignmets_after = len(self.routing.assignments)
        self.assertEqual(len_locations_before+n*2, len_locations_after)
        self.assertEqual(len_assignmets_before+n, len_assignmets_after)
        all_assignments = np.ravel(np.array(self.routing.assignments))
        self.assertEqual(all_assignments.tolist(), np.arange(1,len_locations_after).tolist())
        index = -1
        for dropoff, pickup in zip(reversed(loc_dropoffs), reversed(loc_pickups)):
            self.assertEqual(self.routing.locations[index], tuple(dropoff))
            self.assertEqual(self.routing.locations[index - 1], tuple(pickup))
            index -= 2


    def test_delete_locations(self, indices_to_delete=[1]):
        n = len(indices_to_delete)
        len_locations_before = len(self.routing.locations)
        len_assignmets_before = len(self.routing.assignments)
        assignments_to_ignore = [self.routing.assignments[i] for i in indices_to_delete]
        assignments_to_ignore_flat = np.ravel(np.array(assignments_to_ignore))
        assert all(assignments_to_ignore_flat == np.array([i for assignment in assignments_to_ignore for i in assignment]))
        locations_to_delete = [self.routing.locations[i] for i in assignments_to_ignore_flat]
        self.routing.delete_location(indices_to_delete)
        self.assertNotIn(locations_to_delete, self.routing.locations)
        len_locations_after = len(self.routing.locations)
        len_assignmets_after = len(self.routing.assignments)
        self.assertEqual(len_locations_before-n*2, len_locations_after)
        self.assertEqual(len_assignmets_before-n, len_assignmets_after)        

    def test_update_offer_list_winner_and_seller(self):
        self.routing.delete_location([0])
        offer_to_update = {
            'offer_id': 'offer_1',
            'offeror': 'carrier_1',
            'winner': 'carrier_1',
            'winning_bid': 150.0,
            'loc_pickup': {'pos_x': 90.0, 'pos_y': 40.0},
            'loc_dropoff': {'pos_x': 85.0, 'pos_y': 35.0},
            'revenue': 1000.0
        }
        len_locations_before = len(self.routing.locations)
        len_assignments_before = len(self.routing.assignments)

        self.routing.update_offer_list(offer_to_update)

        len_locations_after = len(self.routing.locations)
        len_assignments_after = len(self.routing.assignments)
        self.assertEqual(len_locations_before+2, len_locations_after)
        self.assertEqual(len_assignments_before+1, len_assignments_after)

        updated_offer = next((o for o in self.routing.offers if o.offer_id == 'offer_1'), None)
        self.assertIsNotNone(updated_offer)
        self.assertEqual(updated_offer.winner, 'carrier_1')
        self.assertEqual(updated_offer.winning_bid, 150.0)
        self.assertFalse(updated_offer.on_auction)

    def test_update_offer_list_winner_not_seller(self):
        offer_to_update = {
            'offer_id': 'offer_12',
            'offeror': 'carrier_2',
            'winner': 'carrier_1',
            'winning_bid': 120.0,
            'loc_pickup': {'pos_x': 88.0, 'pos_y': 42.0},
            'loc_dropoff': {'pos_x': 86.0, 'pos_y': 36.0},
            'revenue': 1000.0
        }

        len_locations_before = len(self.routing.locations)
        len_assignments_before = len(self.routing.assignments)

        self.routing.update_offer_list(offer_to_update)

        len_locations_after = len(self.routing.locations)
        len_assignments_after = len(self.routing.assignments)
        self.assertEqual(len_locations_before + 2, len_locations_after)
        self.assertEqual(len_assignments_before + 1, len_assignments_after)

        updated_offer = next((o for o in self.routing.offers if o.offer_id == 'offer_12'), None)
        self.assertIsNotNone(updated_offer)
        self.assertEqual(updated_offer.winner, 'carrier_1')
        self.assertEqual(updated_offer.winning_bid, 120.0)
        self.assertFalse(updated_offer.on_auction)

    def test_update_offer_list_seller_not_winner(self):
        self.routing.delete_location([2])
        offer_to_update = {
            'offer_id': 'offer_3',
            'offeror': 'carrier_1',
            'winner': 'carrier_3',
            'winning_bid': 110.0,
            'loc_pickup': {'pos_x': 89.0, 'pos_y': 41.0},
            'loc_dropoff': {'pos_x': 84.0, 'pos_y': 38.0},
            'revenue': 1000.0
        }

        len_locations_before = len(self.routing.locations)
        len_assignments_before = len(self.routing.assignments)

        self.routing.update_offer_list(offer_to_update)

        len_locations_after = len(self.routing.locations)
        len_assignments_after = len(self.routing.assignments)
        self.assertEqual(len_locations_before, len_locations_after)
        self.assertEqual(len_assignments_before, len_assignments_after)

        updated_offer = next((o for o in self.routing.offers if o.offer_id == 'offer_3'), None)
        self.assertIsNotNone(updated_offer)
        self.assertEqual(updated_offer.winner, 'carrier_3')
        self.assertEqual(updated_offer.winning_bid, 110.0)
        self.assertTrue(updated_offer.on_auction)


if __name__ == '__main__':
    unittest.main()