# Overview Orchestrator

# Setup: Correct the /etc/apt/sources.list
# Comment out/ remove the first line if it refers to the CD image
# Add the following line to your /etc/apt/sources.list:
deb http://deb.debian.org/debian stable main

# Update the system:
su
apt update
apt dist-upgrade

# Run the setup script:
./setup

# Configuration
Open the file 'mo_config.json' with a text editor. Fill in the correct IP and MAC addresses. Please note that you can use multiple MC - ME pairs, but you do not have to.
After a change of the configuration, restart the Measurement Orchestrator:

sudo systemctl restart measurementOrchestrator.service