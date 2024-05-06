"""Generate random locations and assign them delivery routes.

This module provides functions to generate a list of random locations within a
specified grid and assign deliveries between these locations. The `generate_odd_random()` 
function ensures an odd number of locations, which includes one depot and an 
even number of delivery locations.

Functions:
    generate_odd_random(): 
        Generate a random odd number between MIN_REQUESTS and MAX_REQUESTS.

    create_random_locations(): 
        Create a list of random locations (x, y) within a -100 to 100 grid.

    assign_deliveries(locations): 
        Assign delivery pairs to a list of locations.

Constants:
    MIN_LOCATIONS (int): 
        The minimum number of requests for random location generation.

    MAX_LOCATIONS (int): 
        The maximum number of requests for random location generation.
"""
import random

MIN_LOCATIONS = 6
MAX_LOCATIONS = 12
# MIN_REVENUE = 10
# MAX_REVENUE = 100 

def generate_odd_random():
    """Return a random odd number between MIN_REQUESTS and MAX_REQUESTS."""
    while True:
        random_number = random.randint(MIN_LOCATIONS, MAX_LOCATIONS)  
        if random_number % 2 == 1:  
            return random_number
        
def create_random_locations():
    """Create a list of random locations (x, y) within a -100 to 100 grid.
    
    Returns:
        list of tuples: A list of random locations (x, y) within the specified grid range.
    """
    locations = []
    for _ in range(generate_odd_random()):
        horizontal_pos = round(random.uniform(-100, 100), 2)
        vertical_pos = round(random.uniform(-100, 100), 2)
        # revenue = round(random.uniform(MIN_REVENUE, MAX_REVENUE), 2)
        location = (horizontal_pos, vertical_pos)
        locations.append(location) 
    return locations

def assign_deliveries(locations):
    """Assign delivery pairs to a list of locations.

    Args:
        locations (list of tuples): A list of locations (x, y).

    Returns:
        list of lists: A list of pairs [x, y] representing assigned delivery locations.
    """
    pairs = []
    indices = list(range(1, len(locations))) # Exclude the depot
    while len(indices) >= 2:  
        pair = random.sample(indices, 2)  
        pairs.append(pair)
        indices.remove(pair[0]) 
        indices.remove(pair[1])
    return pairs