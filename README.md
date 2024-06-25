# Python Collaborative Carrier Network

## Description
The objective of this project is to implement a system that facilitates the reassignment of transport requests in a manner that increases the profit margins of participating delivery companies (carriers). This is to be achieved with an auction-based solution that respects the privacy of individual carriers while maximizing the efficiency of the entire network. The proposed solution uses an auctioneer agent to intelligently redistribute transport requests among participating carriers via auctions. The system ensures that the reassignment of transport requests is executed in a manner that either maintains or enhances the profit margins of all involved agents.

## Installation

1. Clone the repository

2. Download Python

    [Python Download](https://www.python.org/downloads)

3. Install dependencies

        pip install -r requirements.txt
        
## Usage 

* Use as Carrier
    
        cd Agent_Infrastructure

        python3 carrier_main.py

* Use as Auctioneer

        cd Agent_Infrastructure

        python3 auctioneer_main.py

* Start application

        cd Application
        
        python3 app.py [portNumber]

## Application

* Use as Carrier
    
        > carrier.html


* Use as Auctioneer

        > auctioneer.html


* Simulate

        > simulation.html


## Authors

- Max Kretschmann
- Shachar Dan
- Lorenz Leddig
