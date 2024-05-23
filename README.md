# Python Collaborative Carrier Network

## Description
The objective of this project is to implement a system that facilitates the reassignment of transport requests in a manner that increases the profit margins of participating delivery companies (carriers). This is to be achieved with an auction-based solution that respects the privacy of individual carriers while maximizing the efficiency of the entire network. The proposed solution uses an auctioneer agent to intelligently redistribute transport requests among participating carriers via auctions. The system ensures that the reassignment of transport requests is executed in a manner that either maintains or enhances the profit margins of all involved agents.

## Visuals

## Installation

1. Clone the repository

2. Download Python

    [Python Download](https://www.python.org/downloads)

3. Install dependencies

        pip install -r requirements.txt
        
## Usage 

* Simulate agent behavior

    > Simulate (Default: 3 carrier agents)
        
        cd Agent_Simulation
        python3 RunSimulation.py

    > Simulate with custom agent amount
        
        cd Agent_Simulation
        python3 RunSimulation.py -a AGENT_AMOUNT  

* Use as Carrier
    
        cd Agent_Infrastructure
        python3 Start_Carrier_Agent.py

* Use as Auctioneer

        cd Agent_Infrastructure
        python3 Start_Auctioneer_Agent.py

* Start application

        cd Application
        python3 app.py

## Authors

- Max Kretschmann
- Shachar Dan
- Lorenz Leddig
