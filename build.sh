#!/bin/bash

# Exit immediately if any command fails
set -e

# CRITICAL: Activate the Python virtual environment created by Netlify's build process
# The path changes based on the environment, but this is the standard path.
source /opt/buildhome/python3.8/bin/activate

# Install dependencies into the environment
pip install -r requirements.txt