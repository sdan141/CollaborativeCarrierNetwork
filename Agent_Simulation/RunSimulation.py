"""Run simulation of agent model.

This script demonstrates the usage of the AgentModel class 
for simulating a multi-agent system. It creates an instance 
of the AgentModel class, runs a single step of the simulation, 
displays the tour, and prints out the messages received by each agent.

Usage:
    # Simulate with 3 agents
    python3 RunSimulation.py

    # Simulate with 5 agents
    python3 RunSimulation.py -a 5  
"""
import argparse
from ModelClass import AgentModel
from TourGUI import show_tour

def parse_arguments():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(description="Run the agent model simulation.")
    parser.add_argument("--agents", "-a", type=int, default=3, help="Number of agents in the simulation (default: 3)")
    return parser.parse_args()

def main():
    """Run the agent model simulation."""
    # Parse command-line arguments
    args = parse_arguments()

    # Create agent model
    model = AgentModel(args.agents)

    # Run one step of the model
    model.step()

    # Display tours
    show_tour(model.schedule.agents)

    # Print messages received by each agent
    for agent in model.schedule.agents:
        print("Agent {}: {}".format(agent.unique_id, agent.messages_received))

if __name__ == "__main__":
    main()

    