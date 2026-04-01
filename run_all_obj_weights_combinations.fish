#!/usr/bin/env fish

set obj_weights_types min_econ min_tech min_soc econ_tech econ_soc tech_soc balanced

for obj in $obj_weights_types
    echo "=================================================="
    echo "Running objective weight type: $obj"
    echo "=================================================="

    env OBJ_WEIGHTS_TYPE=$obj python -m src.experiments.run_models
    or exit 1
end