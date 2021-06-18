import os, sys
path = os.path.dirname(os.path.realpath('__file__'))
os.chdir(path)
sys.path.append(os.path.dirname(path))

import matplotlib.pyplot as plt
import numpy as np

from marketsim import MarketSim


# create a new market simulation real market data
market = MarketSim(fin='data/input_dummy.csv', fout='data/output_dummy.csv')

# add agents to the market
market.add_agent(uid='1', tech='gas', cap=4000, var_cost=45)
market.add_agent(uid='2', tech='hydro', cap=6000, var_cost=7)
market.add_agent(uid='3', tech='wind', cap=3300, var_cost=4)
market.add_agent(uid='4', tech='solar', cap=1500, var_cost=1)
market.add_agent(uid='5', tech='storage', cap=100, var_cost=10, storage=400)

# run the market simulation for every timestamp in the input file and save results to the output file
market.run()


# Plots the Profits of all agents and the marginal price
plt.plot(np.asarray(market.all_rewards)[:,0], label = 'gas')
plt.plot(np.asarray(market.all_rewards)[:,1], label = 'hydro')
plt.plot(np.asarray(market.all_rewards)[:,2], label = 'wind')
plt.plot(np.asarray(market.all_rewards)[:,3], label = 'solar')
plt.plot(np.asarray(market.all_rewards)[:,4], label = 'storage')
plt.plot(np.asarray(market.all_market_prices), label = 'marginal price')
plt.ylabel('Profits/Marginal Price (EUR)')
plt.xlabel('Bidding Rounds')
plt.title('Energy Market Simulation')
plt.legend()

