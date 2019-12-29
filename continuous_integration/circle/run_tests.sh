#!/bin/bash

source $HOME/miniconda/etc/profile.d/conda.sh
conda activate test

# Run tests
pytest -x -vv --cov=spyder_unittest spyder_unittest
