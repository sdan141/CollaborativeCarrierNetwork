"""Agent model class definition.

This module defines the AgentModel class, which represents a simulation model
for carrier and auctioneer agents. It instantiates a specified number of carrier 
agents and a single auctioneer agent.

Class:
    AgentModel: Represents the simulation model for carrier and auctioneer agents.

Usage:
    # Create AgentModel instance with 5 carrier agents and one auctioneer agent
    model = AgentModel(5)

    # Run one step of the simulation
    model.step()
"""
from CarrierClass import CarrierAgent
from AuctioneerClass import AuctioneerAgent
from GenerateRequests import create_random_locations, assign_deliveries
from mesa import Model
from mesa.time import BaseScheduler

class AgentModel(Model):
    """Model class used for simulating carrier and auctioneer agents."""
    def __init__(self, num_carriers):
        """Initialize the AgentModel with a specified number of carrier agents.

        Args:
            num_carriers (int): The number of carrier agents to create.
        """
        super().__init__()
        self.num_carriers = num_carriers
        self.schedule = BaseScheduler(self)
        
        # Create auctioneer agent
        self.auctioneer = AuctioneerAgent(0, self)
        self.schedule.add(self.auctioneer)

        # Create carrier agents
        for i in range(1, self.num_carriers + 1):
            locations = create_random_locations()
            deliveries = assign_deliveries(locations)
            carrier = CarrierAgent(i, locations, deliveries, self)
            self.schedule.add(carrier)

    def step(self):
        """Advance the simulation by one step."""
        self.schedule.step()