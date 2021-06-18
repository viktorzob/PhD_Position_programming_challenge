# Agent Based Model of a simple dayahead electrictiy market

Written for a sumbisson to a PhD_Position programming challenge. Simulates a simple unifrom dayahed electricity market.

## What should it do?

Simulation is called by *MarketSim(fin='data/input_dummy.csv', fout='data/output_dummy.csv')*:

- Takes as input a .csv-file includig the variables: time, demand, hydro_avil., wind_avail., solar_avail.;
- Attention: if one of those variable names isn't included, the code will not run! An exmaple is deilverd in data/input_dummy.csv
- Outputs again a .csv-file containing 'time', 'system cost', 'marginal price' and the profit of all agents

Agents get initalized by *MarketSim.add_agent(uid, tech, cap, var_cost, storage)*:

- uid: string, unique agent identifier
- tech: string, technology the agent uses. Possible choices are: gas, hydro, wind, solar, storage
- cap: int, installed capacity of this agent in MW
- var_cost: float, variable cost of generation in EUR/MWh. This holds the fuel cost (EUR/MWh_therm) for gas generators and the operational cost (EUR/MWh_el) for all other generators
- storage: int, optional, available storage capacity for storage agents in MWh

- It is not necessary to include all tech-types, if one (or more) are omitted a pseudo-agents gets initalized where all paramters are set to 0, so that it doesn't affect the outcome.

The Simulation gets executed by *MarketSim.run(gas_efficiency, storage_efficiency, CO2_emission , CO2_price, bids_per_day)*:

- All offered bids and capacities are collected for every 15 minutes for the dayahead (i.a. 96 offers) and then get cleared step by step by merit-oder market clearing
- Bids of all agents are equal to their marginal costs, only the storage-agent bids the average marginal price (from the marginal prices the day before) times the percentage of the newly purchased capacity to the maximum storage space + its marginal costs
- Offered capacities for 'hydro', 'wind' and 'solar' are equal their initalized capacities times their individual availability from the .csv-input file.
- 'storage' always offers its available capacity/96 times storage_efficiency
- 'gas' always offers its capacity times gas_efficiency and gets an additional penalty induced by CO2 emissions


Other functions included in class *MarketSim*:

- *market_clearing*: executes a merit-order market clearing. Input: demand and bids, Outputs: market price, bids and sold quantities
- *tie_break*: If two or more agents shared the same bid, the function fairly divides the offered quantities between the agent within the tie break situation

