# Copyright (c) 2019-2024 The University of Chicago.
# Part of skyway, released under the BSD 3-Clause License.

# Maintainer: Trung Nguyen

"""@package docstring
Documentation for SLURMCluster Class
"""
import os
import io
import subprocess
from tabulate import tabulate
from .core import Cloud
from .. import utils

from datetime import datetime, timezone
import pandas as pd


class SLURMCluster(Cloud):
    """Documentation for SLURMCluster
    This Class is used as the driver to operate SLURM-provisioned resource for [Demo]
    """
    
    def __init__(self, account):
        """Constructor:
        The construct initialize the connection to the cloud platform, by using
        setting informations passed by [cfg], such as the credentials.        

        account [string]
        """

        #super().__init__(vendor_cfg, kwargs)

        # load [account].yaml under $SKYWAYROOT/etc/accounts
        account_path = os.environ['SKYWAYROOT'] + '/etc/accounts/'
        account_cfg = utils.load_config(account, account_path)
        if account_cfg['cloud'] != 'slurm' :
            raise Exception(f'Service provider slurm is not associated with this account.')

        for k, v in account_cfg.items():
            setattr(self, k.replace('-','_'), v)

        self.usage_history = f"{account_path}usage-{account}.pkl"

        # load cloud.yaml under $SKYWAYROOT/etc/
        cloud_path = os.environ['SKYWAYROOT'] + '/etc/'
        vendor_cfg = utils.load_config('cloud', cloud_path)
        if 'slurm' not in vendor_cfg:
            raise Exception(f'Service provider slurm is undefined.')

        self.vendor = vendor_cfg['slurm']
        self.account_name = account

       
    # account info

    def check_valid_user(self, user_name, verbose=False):
        '''
        check if a user name is in the cloud account
        '''
        if user_name not in self.users:
            if verbose == True:
                print(f"{user_name} is not listed in the user group of this account.")
            return False

        if verbose == True:
            user_info = []
            user_info.append([user_name, self.users[user_name]['budget']])
            print(tabulate(user_info, headers=['User', 'Budget']))
            print("")
        return True
      

    def get_node_types(self):
        """
        List all the node (instance) types provided by the vendor and their unit prices
        """
        node_info = []
        for node_type in self.vendor['node-types']:
            node_info.append([node_type, self.vendor['node-types'][node_type]['name'], self.vendor['node-types'][node_type]['price']])
        print(tabulate(node_info, headers=['Name', 'Instance Type', 'Per-hour cost']))
        print("")

    def get_group_members(self):
        """
        List all the users in this account
        """
        user_info = []
        for user in self.users:
            user_info.append([user, self.users[user]['budget']])
        print(tabulate(user_info, headers=['User', 'Budget']))
        print("")

    # billing operations

    def get_budget(self, user_name=None, verbose=True):
        '''
        get the current budget of the whole account, or of a user name from the account yaml file
        '''
        if user_name is not None:
            if user_name not in self.users:
                print(f"{user_name} is not listed in the user group of this account.")
                return -1
        
            if verbose == True:
                user_info = []
                user_info.append([user_name, self.users[user_name]['budget']])
                print(tabulate(user_info, headers=['User', 'Budget']))
                print("")
            return self.users[user_name]['budget']
        else:
            user_info = []
            total_budget = 0.0
            for name in self.users:
                total_budget += float(self.users[name]['budget'])
                if verbose == True:
                    user_info.append([name, self.users[name]['budget']])
            if verbose == True:
                print(tabulate(user_info, headers=['User', 'Budget']))
                print(f"Total: ${total_budget}")
            return total_budget

    def get_budget_api(self):
        '''
        get the budget from the cloud account API
        '''
        pass

    def get_cost_and_usage_from_db(self, user_name):
        '''
        compute the accumulating cost from the pkl database
        and the remaining balance
        '''
        accumulating_cost = 0
        remaining_balance = 0
        return accumulating_cost, remaining_balance

    # instance operations

    def list_nodes(self, show_protected_nodes=False, verbose=False):
        '''
        list all the running/stopped nodes (aka instances)
        '''
        pass

    def create_nodes(self, node_type: str, node_names = [], need_confirmation = True, walltime = None):
        '''
        create several nodes (aka instances) given a list of node names
        '''
        user_name = os.environ['USER']
        user_budget = self.get_budget(user_name=user_name, verbose=False)
        usage, remaining_balance = self.get_cost_and_usage_from_db(user_name=user_name)
        running_cost = self.get_running_cost(verbose=False)
        usage = usage + running_cost
        remaining_balance = user_budget - usage
        unit_price = self.vendor['node-types'][node_type]['price']
        if need_confirmation == True:
            print(f"User budget: ${user_budget:.3f}")
            print(f"+ Usage    : ${usage:.3f}")
            print(f"+ Available: ${remaining_balance:.3f}")
            response = input(f"Do you want to create an instance of type {node_type} (${unit_price}/hr)? (y/n) ")
            if response == 'n':
                return

        if walltime is None:
            walltime_str = "01:00:00"
        else:
            walltime_str = walltime
        
        ntasks_per_node = self.vendor['node-types'][node_type]['cores']
        memgb = self.vendor['node-types'][node_type]['memgb']

        count = len(node_names)
        if count <= 0:
            raise Exception(f'List of node names is empty.')
       
        cmd = f"salloc -A {self.account['account_id']} -N {count} --ntasks-per-node={ntasks_per_node} --mem={memgb}GB -t {walltime_str}' "
        print(f"{cmd}")
        os.system(cmd)

    def connect_node(self, node_name):
        '''
        connect to a node (aka instance) via SSH
        '''
        pass

    def destroy_nodes(self, node_names, need_confirmation=True):
        '''
        destroy several nodes (aka instances) given a list of node names
        '''
        pass

    def get_running_nodes(self, verbose=False):
        '''
        list all the running nodes (aka instances)
        '''
        pass

    def execute(self, node_name: str, **kwargs):
        '''
        execute commands on a node
        '''
        pass

    def get_host_ip(self, node_name):
        '''
        get the public IP of a node name
        '''
        pass

    def get_unit_price(self, node_type: str):
        '''
        get the unit price of a node object (inferring from its name and from the cloud.yaml file)
        '''
        if node_type in self.vendor['node-types']:
            return self.vendor['node-types'][node_type]['price']
        return -1.0

    def get_instances(self, filters = []):
        """Member function: get_instances
        Get a list of instance objects with give filters
        """
        user_name = os.environ['USER']

        nodes = []
            
        cmd = f"export SQUEUE_FORMAT=\"%13i %.4t %24j %13i %N 0.0 0.0\"; squeue -u {user_name}"
        proc = subprocess.Popen([cmd], stdout=subprocess.PIPE, shell=True)
        (out, err) = proc.communicate()
      
        # encode output as utf-8 from bytes, remove newline character
        m = out.decode('utf-8').strip()
        # convert to a list
        m = m.split()

        nodes = [m]

        return nodes