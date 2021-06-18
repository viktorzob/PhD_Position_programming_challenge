# -*- coding: utf-8 -*-
"""
Created on Mon Jun 14 09:00:25 2021

@author: Viktor
"""
import os, sys
path = os.path.dirname(os.path.realpath('__file__'))
os.chdir(path)
sys.path.append(os.path.dirname(path))

import pandas as pd
import numpy as np
import numpy_groupies as npg

from numpy_groupies import aggregate_numpy as anp


class MarketSim():
    def __init__(self, fin='data/input_dummy.csv', fout='data/output_dummy.csv'):
        
        self.fin = fin
        self.fout = fout
        
        # read out input file (csv)
        read_out = pd.read_csv(self.fin, sep=';', header=0)
        self.var_names = np.asarray(read_out.columns)
        self.input_data = read_out.to_numpy()
        
        # list for all agets that get added by "add_aggent"
        self.all_agents =[]
        
    def add_agent(self, uid, tech, cap, var_cost, storage=0):
        # set up agent matrix
        # define data types of agents
        # index is used, because I wasn't sure if uid can be used as index variable
        index = len(self.all_agents)
        agent =['{}'.format(uid),tech,int(cap),float(var_cost),float(storage), index]
        self.all_agents.append(agent)
        

    def run(self, gas_efficiency = 0.8, storage_efficiency = 0.9, CO2_emission = 0.45, CO2_price = 50, bids_per_day = 24*4):
        
        # if some techs aren't included; sets up an empty agent of the missing tech, which does not effect the simulation
        techs_avail =['gas','hydro','wind','solar','storage']
        for i in range(len(techs_avail)):
            if not np.argwhere(np.asarray(self.all_agents)[:,1] == techs_avail[i]).size > 0:
                self.add_agent(uid='none{}'.format(techs_avail[i]), tech='{}'.format(techs_avail[i]), cap=0, var_cost=0, storage=0)
        
        # switch to numpy
        self.all_agents = np.asarray(self.all_agents, dtype = 'object')
        
        # get rows of different energy suppliers
        gas_row = np.argwhere(self.all_agents[:,1] == 'gas')
        hydro_row = np.argwhere(self.all_agents[:,1] == 'hydro')
        solar_row = np.argwhere(self.all_agents[:,1] == 'solar')
        wind_row = np.argwhere(self.all_agents[:,1] == 'wind')
        storage_row = np.argwhere(self.all_agents[:,1] == 'storage')

        
        # get colomuns of input variables
        #ATTENTION: Code will not run if on of those variable is missing in the input file
        time = np.argwhere(self.var_names == 'time')
        market_demand = np.argwhere(self.var_names == 'demand')
        hydro_avail = np.argwhere(self.var_names == 'hydro avail.')
        solar_avail = np.argwhere(self.var_names == 'solar avail.')
        wind_avail = np.argwhere(self.var_names == 'wind avail.')
                
        
        # set up saving variablas for  the output file
        self.all_rewards = []
        self.all_market_prices = []
        self.all_system_costs = []
        self.all_storage_cap_bid_offers =[]
        
        # storage-agent variables and starting strategy; SoC... State of Capacity
        storage_bids = self.all_agents[storage_row,3]
        max_cap_storage = self.all_agents[storage_row,2]
        max_storage_storage = self.all_agents[storage_row,4]
        
        self.SoC=0
        self.all_agents[storage_row,4] = self.SoC 
        storage_offer_cap = 0
        demand_storage = (max_storage_storage - self.SoC) / bids_per_day


        # for loop over the whole time series from the input file
        for step in range(len(self.input_data)):

            #storage-agent strategy: bids and cap offers for the next day; 
            #bids are the average market price from the day before times the ratio of new bought capacity to the max storage volume + marginal costs
            #always resets at the end of a day, i.a. after 24*4 bids
            if step % bids_per_day == 0 and step != 0:
                # Bid strategy storage-agent
                storage_bids = np.mean(np.asarray(self.all_market_prices[-bids_per_day:])) * ((self.SoC- self.all_agents[storage_row,4])/ max_storage_storage) + self.all_agents[storage_row,3]
                #Alternative Startegy (Caps lowest price at marginal costs):
                #storage_bids = np.clip(np.mean(np.asarray(self.all_market_prices[bids_per_day:])) * ((self.SoC- self.all_agents[storage_row,4])/ max_storage_storage), self.all_agents[storage_row,3], np.max(np.asarray(self.all_market_prices[-self.bids_per_day:]))

                # Capacity offer strategy storage-agent
                storage_new_offer_cap= np.clip(self.SoC, 0, max_cap_storage - self.all_agents[storage_row,2])
                self.all_agents[storage_row,2] = np.clip(self.all_agents[storage_row,2] + storage_new_offer_cap, 0, max_cap_storage)
                self.SoC = np.clip(self.SoC - storage_new_offer_cap, 0, max_storage_storage)
                self.all_agents[storage_row,4] = self.SoC
                storage_offer_cap = self.all_agents[storage_row,2] / bids_per_day
                demand_storage = (max_storage_storage - self.SoC) / bids_per_day
                
                 
            # adjust capacities according to availability and efficiencies
            adjcap_agents = np.copy(self.all_agents)
            adjcap_agents[gas_row,2] *= gas_efficiency
            adjcap_agents[hydro_row,2] *= self.input_data[step,hydro_avail]
            adjcap_agents[solar_row,2] *= self.input_data[step,solar_avail]
            adjcap_agents[wind_row,2] *= self.input_data[step,wind_avail]
            adjcap_agents[storage_row,2] = np.clip(storage_offer_cap, 0, max_cap_storage) * storage_efficiency
            
            # current storage-agent bid
            adjcap_agents[storage_row,3] = np.squeeze(storage_bids)
            
            # demand = current demand + demand by the storage-agent
            demand = self.input_data[step,market_demand] + demand_storage
            
            # market clearing: input are the bids of the agent and the demand (maximum available capacities ar needed in case of a tie break calculation)
            market_price, bids, quantities = self.market_clearing(demand,np.c_[adjcap_agents, adjcap_agents[:,2]])

            # storage-agent buys capacity
            bought_cap_storage = np.clip(np.sum(quantities) - self.input_data[step,market_demand], 0, demand_storage) * storage_efficiency            
            self.SoC = np.clip(self.SoC + bought_cap_storage - quantities[storage_row], 0, max_storage_storage)
            
            # to ensure that now unessecary volumes get paid
            if self.SoC >= max_storage_storage:
                demand_storage = 0
            
            # calculate profits: (market_price -carcosts) * sold_qunatities (using all_agents (instead of adjcap) here for the var_costs, ensures that storage-agents bid vary to its own costs)
            rewards = (market_price - self.all_agents[:,3]) * quantities 
            
            # CO2 Price penalty
            rewards[gas_row] -= (quantities[gas_row]*CO2_emission)*CO2_price 
            
            # price for the bought capacity of the storage-agent
            rewards[storage_row] -= market_price * bought_cap_storage
            
            # calculate system costs
            system_costs = demand * market_price

            
            # append data list
            self.all_storage_cap_bid_offers.append([storage_bids, storage_offer_cap])
            self.all_rewards.append(rewards)
            self.all_market_prices.append(market_price)
            self.all_system_costs.append(system_costs) 
            
            
        # Save Output Data  as csv again
        output_var_names = ['time','system cost','marginal price']
        for i in range(len(self.all_agents)):
            output_var_names.append('profit agent {}'.format(self.all_agents[i,0]))
            
        output_data = np.c_[np.squeeze(self.input_data[:,time]), np.squeeze(self.all_system_costs), np.asarray(self.all_market_prices), np.asarray(self.all_rewards)]
        output_df = pd.DataFrame(data=output_data, columns=output_var_names)
        output_df.to_csv(self.fout, sep=';', index = False)
        
        
    def market_clearing(self, demand,bids):    

        bids = bids.astype(object)
        
        # Sort by 3rd Row (ie by Price-Bids)
        ind = np.argsort(bids[:,3]) 
        bids = bids[ind]
        #print(bids)
        
        #Consecutively add up 2nd Row (ie Quantity-Bids)
        bids[:,2]=np.cumsum(bids[:,2])
        #print(bids)
        
        #Restrict Quantity by 0 and Demand
        bids[:,2]=np.clip(bids[:,2],0,demand)
        #print(bids)
        
        #Determine Position of Price setting player and Marketprice
        cutoff = np.argmax(bids[:,2])
        market_price = bids[cutoff,3]
        #print(bids)
        
        #Convert CumSum to Differences
        #This sets all quantities above cutoff to 0 and gives sold quantities below cutoff
        bids[:,2]=np.hstack((bids[0,2],np.diff(bids[:,2])))
        #print(bids)
        
        # Tie Break
        if len(np.argwhere(bids[:,3] == np.amax(bids[:,3]))) > 1:
            bids = self.tie_break(bids)
        #print(bids)
        
        #Attention: without dtype float in the values we get an overflow
        bids_del = np.delete(bids, [0,1], 1).astype('float64')
        quantities = npg.aggregate(bids_del[:,3].astype(int),bids_del[:,0],func='sum',dtype=np.float)
        #print(quantities)
        
        return market_price, bids, quantities


    def tie_break(self, bids):
        
        # determine candidates who are in a tie break
        tie_break_candidates = np.argwhere(bids[:,3] == np.amax(bids[:,3]))
        
        if len(tie_break_candidates) == 0:
            tie_break_candidates = np.argwhere(bids[:,3] == np.amax(bids[:,3]))
            
        # starting capacity for distributin
        overall_base_quantity = sum(bids[tie_break_candidates[0,0]:,2])   
        base_quantities = overall_base_quantity/len(tie_break_candidates)
        
        # parameters needed to start while-loop
        quantity_for_distribution = overall_base_quantity
        new_quantities = base_quantities
        more_cap_candidates = np.argwhere(bids[tie_break_candidates[0,0]:,6] > new_quantities)
        distributed_quantities = 0
        
        while quantity_for_distribution > 0:
            
            # check amount which is already distributed 
            quantity_for_distribution = overall_base_quantity -(distributed_quantities + new_quantities*len(more_cap_candidates))
            
            # determine those who sitll have free capacity to sell and those who are already satisfied
            more_cap_candidates = np.argwhere(bids[tie_break_candidates[0,0]:,6] > new_quantities) 
            less_cap_candidates = np.argwhere(bids[tie_break_candidates[0,0]:,6] <= new_quantities)
            
            # get how much is still left for distribution
            surplus= 0
            for i in range(len(less_cap_candidates)):
                surplus += new_quantities - bids[less_cap_candidates[i,0],6]
            
            # determine new amount for distribution
            if len(more_cap_candidates) > 0:
                new_quantities = new_quantities + (surplus/len(more_cap_candidates))
            
            # check amount of already satisfied candidates
            distributed_quantities = 0
            for i in range(len(less_cap_candidates)):
                distributed_quantities += bids[less_cap_candidates[i,0],6]
            
        
        bids[tie_break_candidates[0,0]:,2] = np.clip(new_quantities,0,bids[tie_break_candidates[0,0]:,6])
        
        return bids  