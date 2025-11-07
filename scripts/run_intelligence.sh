#!/bin/bash
# Helper script to run Intelligence Capture System

# Activate virtual environment
source venv/bin/activate

# Run with arguments passed to script
cd intelligence_capture
python run.py "$@"
