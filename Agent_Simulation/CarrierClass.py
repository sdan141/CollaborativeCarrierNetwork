"""Carrier agent class definition.

The CarrierAgent class represents carrier agents in a simulation. The carrier 
agent is capable of sending / receiving messages and registering for auctions.

Class:
    CarrierAgent: Represents class for carrier agents.
"""
from mesa import Agent

AUCTIONEER_ID = 0

class CarrierAgent(Agent):
    """An agent representing a carrier in the simulation."""
    def __init__(self, unique_id, locations, deliveries, model):
        """Initialize a carrier agent.

        Args:
            unique_id (int): Unique identifier for the agent.
            locations (list): List of locations for the carrier.
            deliveries (list): List of deliveries for the carrier.
            model (mesa.Model): Reference to the model containing the agent.
        """
        super().__init__(unique_id, model)
        self.locations = locations
        self.deliveries = deliveries
        self.messages_received = []
        self.register_auction()
        
    def send_message(self, content, receiver_id, message_type):
        """Send a message to another agent."""
        message = {"content": content, "sender_id": self.unique_id, "message_type": message_type}
        receiver = self.model.schedule.agents[receiver_id]
        receiver.receive_message(message)

    def receive_message(self, message):
        """Receive a message from another agent."""
        self.messages_received.append(message)

    def register_auction(self):
        """Request registration for an auction."""
        content = f"I am agent {self.unique_id} and I want to register for the auction!"
        self.send_message(content, AUCTIONEER_ID, "registration")
