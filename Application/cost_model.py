from calculate_tour import create_tour_data, get_optimal_tour

def get_cost_list(locations, deliveries, distance_total, loading_cost, kilometer_cost):
    # Cost für request = Laderate + Kilometerkosten * Auftrags distanz
    costs = []
    multiplier = 0
    for i in range(0, len(deliveries)):
        locations_without_request = locations[:]
        del locations_without_request[i + 1 + multiplier]
        del locations_without_request[i + 1 + multiplier]
        
        deliveries_without_request = deliveries[:]
        del deliveries_without_request[-1]

        data = create_tour_data(locations_without_request, deliveries_without_request)
        tour_calculation_without_request = get_optimal_tour(data)
        distance_without_request = tour_calculation_without_request['distance']
        
        request_distance = distance_total - distance_without_request
        cost = round(loading_cost + kilometer_cost * (request_distance / 1000), 2)
        costs.append(cost) 
        multiplier = multiplier + 1
    return costs

def get_revenue_list(locations, deliveries, base_price, kilometer_price):
    # Preis für request = Basisrate + Kilometerpreis * Distanz zwischen punkten
    revenues = []
    multiplier = 0
    for i in range(0, len(deliveries)):
        first_node = locations[i + 1 + multiplier]
        second_node = locations[i + 2 + multiplier]
        node_distance = round(abs(first_node[0] - second_node[0]) + abs(first_node[1] - second_node[1]), 2)
        revenue = round(base_price + kilometer_price * (node_distance / 1000), 2)
        revenues.append(revenue) 
        multiplier = multiplier + 1
    return revenues

def get_profit_list(individual_revenues, individual_real_cost):
    profit_list = []

    for i in range(0, len(individual_revenues)):
        individual_profit = round(individual_revenues[i] - individual_real_cost[i], 2)
        profit_list.append(individual_profit)

    return profit_list