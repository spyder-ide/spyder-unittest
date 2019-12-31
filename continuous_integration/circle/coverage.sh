#!/bin/bash

export COVERALLS_REPO_TOKEN=c5Qt1n27dLFCAIESYVkuCmVpUU8doney1
source $HOME/miniconda/etc/profile.d/conda.sh
conda activate test

coveralls
