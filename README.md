# MONICA AgriTwin Simulation Setup

This repository contains MONICA simulation setups for the EOAgriTwin project.

## Simulation Setups

### Climate Projection Simulation

#### TraDef < DST

- **`run-producer.py`**: Producer script for climate projection simulations
- **`run-consumer.py`**: Consumer script to aggregate results into ASCII grid files
- **`sim_setups_projection.csv`**: CSV file defining simulation setups for climate projections
- **`sim_projection.json`**: Sim JSON used for this setup

#### NUTS3 Avg Yield 

Note: consumer and producer python scripts from the historical setups (**`run-consumer_nuts3_avg_yield.py`** and **`run-producer_nuts3_avg_yield.py`**) were used by changing the climate from historical to climate projections

- **`sim_projection_avgyield.json`**: Sim JSON used for this setup (climate projection)
- **`sim_setups_projection_avgyield.csv`**: CSV file defining simulation setups for NUTS3 average yield simulations with default parameter values (climate projection)

### NUTS3-Level Simulation

- **`run-producer_nuts3.py`**: Producer script for NUTS3-level simulations
- **`run-consumer_nuts3.py`**: Consumer script to aggregate NUTS3-level results
- **`sim_setups_nuts3.csv`**: CSV file defining simulation setups for NUTS3-level simulations
- **`sim.json`**: Sim JSON used for this setup
- **`run-producer_nuts3_hist.py`**: Updated Producer script for NUTS3-level with soiltype simulations
- **`run-consumer_nuts3_hist.py`**: Updated Consumer script to aggregate NUTS3-level results by soiltype

### NUTS3 Sensitivity Analysis

- **`run-producer_nuts3_sensitivity.py`**: Producer script for sensitivity analysis at NUTS3 level with soiltype 
- **`run-producer_nuts3_sensitivity2.py`**: Producer script for sensitivity analysis at NUTS3 level with soiltype (extra for parallel runs)
- **`run-producer_nuts3_sensitivity2_old.py`**: Producer script for sensitivity analysis at NUTS3 level without soiltype
- **`run-producer_nuts3_sensitivity3.py`**: Producer script for sensitivity analysis at NUTS3 level for Lower Saxony
- **`run-consumer_nuts3_sensitivity.py`**: Consumer script for sensitivity analysis results in CSV format. The CSV file includes columns for the stage, average number of days below the transpiration deficit threshold during that stage, total number of days in the stage, parameter values, average transpiration deficit for the stage, NUTS3 region name, and soil type.
- **`run-consumer_nuts3_sensitivity2.py`**: Consumer script for sensitivity analysis results in CSV format. The CSV file includes columns for the stage, average number of days below the transpiration deficit threshold during that stage, total number of days below the transpiration deficit threshold during that stage, parameter values, region name and soil type.
- **`run-consumer_nuts3_sensitivity2_old.py`**: Consumer script for sensitivity analysis results in CSV format. The CSV file includes columns for the stage, average number of days below the transpiration deficit threshold during that stage, total number of days below the transpiration deficit threshold during that stage, parameter values, region name only.
- **`run-consumer_nuts3_sensitivity3.py`**: Consumer script for sensitivity analysis results in CSV format. The CSV file includes columns for the stage, average number of days below the transpiration deficit threshold during that stage, total number of days in the stage, parameter values, average transpiration deficit for the stage, NUTS3 region name, and soil type.
- **`sim_setups_nuts3_notsensitivity.csv`**: CSV file defining simulation setups for sensitivity analysis with default parameter values
- **`sim_setups_nuts3_sensitivity.csv`**: CSV file defining simulation setups for sensitivity analysis with varied parameter values for North Rhine-Westphalia, BW, MV, RP, SA, SAAR, SH, TH
- **`sim_setups_nuts3_sensitivity2.csv`**: CSV file defining simulation setups for sensitivity analysis with varied parameter values for Saxony, Hessen, and Bavaria
- **`sim_setups_nuts3_sensitivity_BB.csv`**: CSV file defining simulation setups for sensitivity analysis with varied parameter values for Brandenburg
- **`sim_setups_nuts3_sensitivity_LS.csv`**: CSV file defining simulation setups for sensitivity analysis with varied parameter values for Lower Saxony
- **`sim_sensitivity.json`**: Sim JSON used for sensitivity analysis

### Average Transpiration Deficit Days Below Drought Stress Threshold Simulation

- **`run-producer_avgtradefdays.py`**: Producer script for average transpiration deficit days below drought stress threshold simulations
- **`run-producer_avgtradefdays_sm.py`**: Producer script for average transpiration deficit days below drought stress threshold simulations for silage maize
- **`run-consumer_avgtradefdays.py`**: Consumer script to aggregate average transpiration deficit days below drought stress threshold per stage results into ASCII grid files
- **`run-consumer_avgtradefdays_sm.py`**: Consumer script to aggregate average transpiration deficit days below drought stress threshold per stage results for silage maize into ASCII grid files
- **`sim_setups_germany.csv`**: CSV file defining simulation setups for average transpiration deficit days below drought stress threshold simulations for winter wheat
- **`sim_setups_germany_sm.csv`**: CSV file defining simulation setups for average transpiration deficit days below drought stress threshold simulations for silage maize
- **`sim_avgtradefdays.json`**: Sim JSON used for this setup for winter wheat
- **`sim_avgtradefdays_sm.json`**: Sim JSON used for this setup for silage maize

### Irrigation Simulation [DT Hydrology]

This setup runs MONICA simulations with explicit irrigation events derived from irrigation grids. Irrigation is applied as worksteps that are appended to the crop rotation worksteps.

- **`run-producer_irrigation.py`**: Producer script for irrigation simulations.
  - Adds irrigation worksteps only when:
    - irrigation is enabled in the `sim_setups_irrigation.csv`,
    - the crop is listed as irrigated in `irrigated_crops.json`, and
    - the irrigation grid value for that cell is > 0 (This is handled inside the irrigation manager).
- **`run-consumer_irrigation.py`**: Consumer script to aggregate irrigation simulation outputs.
  - Yield results are converted from kg/ha DM to dt/ha DM.
- **`sim_setups_irrigation.csv`**: CSV file defining simulation setups for irrigation simulations
- **`sim_irrigation.json`**: Sim JSON used for this setup
- **`irrigation_manager.py`**: Helper module to translate irrigation grids into irrigation worksteps
  - Reads irrigation grid time series from a folder (ASC files with dates in the filename, e.g., `BB_iwu_2017-04-21_100_25832_etrs89-utm32n.asc`)
  - Each grid represents a 14-day irrigation total ending on the date in the filename.
  - Irrigation events are distributed across dates within that 14-day window (e.g., every 3 days)
- **`irrigated_crops.json`**: Defines which crops or cultivars are irrigated

### NUTS3 Average Yield Simulation

This setup runs historical MONICA simulations to calculate average yields per soil type and NUTS3 region in CSV format. 

- **`run-producer_nuts3_avg_yield.py`**: Producer script for NUTS3 average yield simulations
- **`run-consumer_nuts3_avg_yield.py`**: Consumer script to aggregate NUTS3 average yield results into CSV format. The CSV file includes columns for the year, average yield in t/ha DM, NUTS3 region name, and soil type.
- **`sim_setups_nuts3_notsensitivity.csv`**: CSV file defining simulation setups for NUTS3 average yield simulations with default parameter values 
- **`sim_sensitivity.json`**: Sim JSON used for this setup
