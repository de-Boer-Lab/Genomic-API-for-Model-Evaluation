#!/bin/bash

# set these variables before running the script
LOCAL_BASKERVILLE_PATH="/home/jlinder/baskerville"
LOCAL_CONDA_PATH="/home/jlinder/anaconda3/etc/profile.d/conda.sh"

# create env_vars sh scripts in local conda env
mkdir -p "$CONDA_PREFIX/etc/conda/activate.d"
mkdir -p "$CONDA_PREFIX/etc/conda/deactivate.d"

file_vars_act="$CONDA_PREFIX/etc/conda/activate.d/env_vars.sh"
if ! [ -e $file_vars_act ]; then
    echo '#!/bin/sh' > $file_vars_act
fi

file_vars_deact="$CONDA_PREFIX/etc/conda/deactivate.d/env_vars.sh"
if ! [ -e $file_vars_deact ]; then
    echo '#!/bin/sh' > $file_vars_deact
fi

# append env variable exports to /activate.d/env_vars.sh
echo "export BASKERVILLE_DIR=$LOCAL_BASKERVILLE_PATH" >> $file_vars_act
echo 'export PATH=$BASKERVILLE_DIR/src/baskerville/scripts:$PATH' >> $file_vars_act
echo 'export PYTHONPATH=$BASKERVILLE_DIR/src/baskerville/scripts:$PYTHONPATH' >> $file_vars_act

echo "export BASKERVILLE_CONDA=$LOCAL_CONDA_PATH" >> $file_vars_act

# append env variable unsets to /deactivate.d/env_vars.sh
echo 'unset BASKERVILLE_DIR' >> $file_vars_deact
echo 'unset BASKERVILLE_CONDA' >> $file_vars_deact

# finally activate env variables
source $file_vars_act
