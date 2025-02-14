# Agent Infrastructure

## Running the example test_n_carrier.sh shell script

The shell script will open one terminal for the auctioneer agent and a number of terminals for the desired carrier agents amount. This example demonstrates the workflow of two bundle rounds and at most 3 individual auction rounds and illustrates the communication between the agents.

1. Make sure you have gnome-terminal installed

        sudo apt-get install gnome-terminal

2. Enter to the directory location of the shell script with cd (depends on current working directory)

3. Open gnome-terminal (linux)

        /usr/bin/dbus-launch /usr/bin/gnome-terminal &

3. Enter to the directory location of the shell script with cd (depends on current working directory)

4. Execute the shell script, replace <CARRIER_AMOUNT> with the desired amount for testing:

        ./test_n_carrier.sh <CARRIER_AMOUNT>

> **_NOTE:_**  At least two carriers have to participate at the auction.


## Running the example test_duplicate_carrier.sh shell script

The shell script will open a terminal for the auctioneer agent and three carrier agents. As a check, it will open a fourth terminal for an already registered carrier. This example demonstrates the workflow of one auction round and illustrates the communication between the agents.

1. Make sure you have gnome-terminal installed

        sudo apt-get install gnome-terminal

2. Enter to the directory location of the shell script with cd (depends on current working directory)

3. Open gnome-terminal (linux)

        /usr/bin/dbus-launch /usr/bin/gnome-terminal &

3. Enter to the directory location of the shell script with cd (depends on current working directory)

4. Execute the shell script:

        ./test_duplicate_carrier.sh