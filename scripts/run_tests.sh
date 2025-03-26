#!/bin/bash
# Add the project root to PYTHONPATH
export PYTHONPATH=$PYTHONPATH:$(pwd)

# Run the test
python scripts/test_models.py 