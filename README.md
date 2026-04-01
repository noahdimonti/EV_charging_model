# EV Charging Model

[![DOI](https://zenodo.org/badge/881729306.svg)](https://doi.org/10.5281/zenodo.19364798)


This repository contains the code developed for an MPhil research project in the School of Engineering at The Australian National University. The work studies EV charging in a hypothetical residential setting and compares different charging infrastructure configurations and coordination strategies.

The models are used to evaluate trade-offs across three stakeholder perspectives:

- Economic: investors
- Technical: distribution system operator
- Social: EV users

The mathematical formulations are described in a journal paper currently under review.

The repository is organised as a research workflow for running models, analysing outputs, and generating figures used in the thesis work.

## Model Scope

The project includes three charging strategies:

- `uncoordinated`: baseline simulation model
- `opportunistic`: coordinated optimisation model
- `flexible`: coordinated optimisation model with scheduling on certain days in a week

These strategies are tested across three infrastructure configurations:

- `config_1`
- `config_2`
- `config_3`

## Setup

Clone the repository:

```bash
git clone <repo-url>
cd EV_charging_model
```

Create and activate a virtual environment:

```bash
python -m venv .venv
source .venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

If you want to run the optimisation models, install Gurobi and activate a valid licence:

https://www.gurobi.com/academia/academic-program-and-licenses/

The coordinated models use `gurobipy`. A different solver can be used, but that requires code changes.

## Data

Download the input data from Zenodo:

https://doi.org/10.5281/zenodo.19364191

The Zenodo record also includes model results. Keep the downloaded folder structure under `data/` so the code can find the expected files.

At minimum, the project expects these paths to exist:

```text
data/inputs/ev_data/
data/inputs/household_load/
data/outputs/models/
data/outputs/metrics/
data/outputs/metrics/compiled_metrics/
data/outputs/plots/
```

## Running Models

Select the model combinations you want to run in `src/experiments/var_setup.py`. This file controls:

- `configurations`
- `charging_strategies`
- the output `version`

Then run:

```bash
python -m src.experiments.run_models
```

This will:

1. run the selected models
2. save model outputs as `.pkl` files in `data/outputs/models/`
3. compile and print evaluation metrics after the run

Useful notes:

- Use a unique `version` name. Existing result filenames are not overwritten.
- If `uncoordinated` is included, `opportunistic` must also be included because the baseline simulation reuses configuration attributes from the opportunistic model.
- `OBJ_WEIGHTS_TYPE` can be set with an environment variable. Supported values are `min_econ`, `min_tech`, `min_soc`, `econ_tech`, `econ_soc`, `tech_soc`, and `balanced`.
- `run_models` prints compiled metrics by default. Set `save_metrics_df = True` in `src/experiments/run_models.py` if you want those metrics saved as CSV files.

Example:

```bash
OBJ_WEIGHTS_TYPE=balanced DEBUGGING_VERSION=_test python -m src.experiments.run_models
```

To run the full set of objective-weight combinations in one go, use:

```bash
fish run_all_obj_weights_combinations.fish
```

This script loops through:

- `min_econ`
- `min_tech`
- `min_soc`
- `econ_tech`
- `econ_soc`
- `tech_soc`
- `balanced`

and runs `python -m src.experiments.run_models` once for each value by setting `OBJ_WEIGHTS_TYPE` automatically.

If you do not use Fish shell, you can use your own Bash script with the same loop structure.

Before using the script, make sure:

- `src/experiments/var_setup.py` is configured the way you want
- the output `version` will be the same for the whole batch in a single run
- that batch `version` is not already present in `data/outputs/models/`
- Fish shell is installed

## Analysing Results

If you already have model outputs and only want to compile the evaluation metrics, run:

```bash
python -m src.experiments.analyse_models
```

This reads the selected model results and prints the compiled metrics.

If you want CSV outputs as well, set `save_df = True` in `src/experiments/analyse_models.py`. Those files are written to `data/outputs/metrics/compiled_metrics/`.

## Generating Plots

Plot scripts are in `src/visualisation/scripts/`. Run the script for the figure set you want to generate, for example:

```bash
python -m src.visualisation.scripts.run_social
python -m src.visualisation.scripts.run_technical
```

Most visualisation scripts expect a matching `version` value inside the script, so update that before running if needed.
