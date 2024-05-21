# Agent Infrastructure

## Description

## Visuals

## Runnig the example shell script

The shell script will open a terminal for the auctioneer agent and three carrier agents. As a check, it will open a fourth terminal for an already registered carrier. This example demonstrates the workflow of one auction round and illustrates the communication between the agents.

1. Make sure you have gnome-terminal installed

        sudo apt-get install gnome-terminal

2. Enter to the directory location of the shell script with cd (depends on current working directory)

3. Open gnome-terminal (linux)

        /usr/bin/dbus-launch /usr/bin/gnome-terminal &

3. Enter to the directory location of the shell script with cd (depends on current working directory)

4. Execute the shell script:

        ./test_ams.sh
