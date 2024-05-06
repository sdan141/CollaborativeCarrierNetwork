"""Auctioneer agent class definition.

The AuctioneerAgent class represents auctioneer agents in a simulation. Auctioneer 
agents handle requests from carrier agents and respond to them accordingly. The auctioneer 
agent is capable of sending / receiving messages and respoding to certain messages.

Class:
    AuctioneerAgent: Represents class for auctioneer agents.
"""
from mesa import Agent

MESSAGE_TYPE_REGISTRATION = "registration"
MESSAGE_TYPE_REG_CONFIRM = "reg_confirm"

class AuctioneerAgent(Agent):
    """An agent representing an auctioneer in the simulation."""
    def __init__(self, unique_id, model):
        """Initialize a auctioneer agent.

        Args:
            unique_id (int): Unique identifier for the agent.
            model (mesa.Model): Reference to the model containing the agent.
        """
        super().__init__(unique_id, model)
        self.messages_received = []
        self.needs_response = False
        # self.registered_carriers = []

    def send_message(self, content, receiver_id, message_type):
        """Sends a message to another agent."""
        message = {"content": content, "sender_id": self.unique_id, "message_type": message_type}
        receiver = self.model.schedule.agents[receiver_id]
        receiver.receive_message(message)

    def receive_message(self, message):
        """Handles received messages from other agents."""
        self.messages_received.append(message)
        self.needs_response = True
    
    def respond_to_message(self, message):
        """Responds to received messages based on their type."""
        if message["message_type"] == MESSAGE_TYPE_REGISTRATION:
            self.handle_registration(message)

    def handle_registration(self, message):
        """Handles registration requests from carrier agents."""
        response_content = "You are now registered for the auction!"
        sender_id = message["sender_id"]
        self.send_message(response_content, sender_id, MESSAGE_TYPE_REG_CONFIRM)

    def step(self):
        """Executes a step in the simulation, processing received messages and responding accordingly."""
        if self.needs_response:
            for message in self.messages_received:
                self.respond_to_message(message)
            self.needs_response = False
