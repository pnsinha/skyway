#!/usr/bin/env python
import os
import sys
import yaml
import subprocess
import pandas
from subprocess import PIPE, Popen

import skyway
from skyway.cloud.aws import *
from skyway.cloud.gcp import *
from skyway.cloud.azure import *
from skyway.cloud.slurm import *

from datetime import datetime, timezone
from io import StringIO
import argparse

# export SKYWAYROOT=/project/rcc/trung/skyway-github
#./skyway_batch.py --account=rcc-aws --constraint=t1 --walltime=01:00:00 --script=run.sh

class InstanceDescriptor:
    def __init__(self, jobname: str, account_name: str, node_type: str, walltime: str, vendor_name: str):
        self.jobname = jobname
        self.account_name = account_name
        self.node_type = node_type
        self.walltime = walltime
        self.vendor_name = vendor_name

        self.account = None
        if 'aws' in vendor_name:
            self.account = AWS(account_name)
        elif 'gcp' in vendor_name:
            self.account = GCP(account_name)
        elif 'azure' in vendor_name:
            self.account = AZURE(account_name)
        elif 'midway3' in vendor_name:
            self.account = SLURMCluster(account_name)

        self.user = os.environ['USER']

    def submitJob(self, script_name=None):
        print(f"creating node from {self.vendor_name} with account {self.account_name}")
        nodes = self.account.create_nodes(self.node_type, [self.jobname], need_confirmation=False, walltime=self.walltime)
        
        if script_name is not None:
            if "midway3" in self.vendor_name:
                # for on-premises like midway3 instanceID is the host ip (which happens to be the node name)
                instanceID = self.account.get_host_ip(self.jobname)
                self.account.execute_script(instanceID, script_name)

            elif "aws" in self.vendor_name:
                instanceID = self.account.get_instance_ID(self.jobname)
                self.account.execute_script(instanceID, script_name)

            elif "gcp" in self.vendor_name:
                instanceID = self.account.get_instance_ID(self.jobname)
                self.account.execute_script(instanceID, script_name)

        return nodes

    def connectJob(self, node_names):
        '''
        only get on a on-premise compute node for now with rcc-staff
        '''
        
        if "midway3" in self.vendor_name:
            # for on-premises like midway3 instanceID is the host ip (which happens to be the node name)
            instanceID = self.account.get_host_ip(self.jobname)
            self.account.connect_node(instanceID)

        elif "aws" in self.vendor_name:
            instanceID = self.account.get_instance_ID(self.jobname)
            self.account.connect_node(instanceID)

        elif "gcp" in self.vendor_name:
            instanceID = self.account.get_instance_ID(self.jobname)
            self.account.connect_node(instanceID)

    def terminateJob(self, node_names = []):
        if "midway3" in self.vendor_name:
            instanceID = self.account.get_instance_ID(self.jobname)
            self.account.destroy_nodes(IDs=[instanceID], need_confirmation=False)
        else:
            self.account.destroy_nodes(node_names=node_names, need_confirmation=False)

    def getBalance(self):
        # retrieve from database for the given account
        accumulating_cost, remaining_balance = self.account.get_cost_and_usage_from_db(user_name=self.user)
        return remaining_balance

    def getEstimateCost(self):
        pt = datetime.strptime(self.walltime, "%H:%M:%S")
        walltime_in_hours = int(pt.hour + pt.minute/60)
        if "midway3" in self.vendor_name:
            unit_price = 1.0 # float(self.account.get_unit_price(self.node_type))
        else:
            unit_price = float(self.account.get_unit_price(self.node_type))
        cost = walltime_in_hours * unit_price
        return cost
  
    def list_nodes(self):
        nodes, list_of_nodes = self.account.list_nodes(verbose=False) 
        return nodes

if __name__ == "__main__":

    msg = "Skyway batch mode"
    parser = argparse.ArgumentParser(description=msg)
    parser.add_argument('-J', dest='jobname', default="your-run", help="Job name")
    parser.add_argument('--account', dest='account', default="", help="Account name")
    parser.add_argument('--provider', dest='provider', default="", help="Vendor name: AWS, GCP, Azure, or RCC Midway")
    parser.add_argument('--partition', dest='partition', default="", help="Partition")
    parser.add_argument('--constraint', dest='constraint', default="", help="Node type")
    parser.add_argument('--walltime', dest='walltime', default="", help="Walltime")
    parser.add_argument(dest='script', nargs='*', default="", help="Script to run")
    
    args = parser.parse_args()

    job_name = args.jobname
    account_name = args.account
    node_type = args.constraint
    walltime = args.walltime
    provider = args.provider.lower()
    script = args.script
    
    if provider == "":
        # try to infer the vendor name from account
        if 'aws' in account_name:
            vendor_name = "aws"
        elif 'gcp' in account_name:
            vendor_name = "gcp"
        elif 'azure' in account_name:
            vendor_name = "azure"
        elif 'midway3' in account_name or 'rcc-staff' in account_name:
            vendor_name = "rcc-midway3"
    else:
        vendor_name = provider

    # get the env variable SKYWAYROOT
    skywayroot = os.environ['SKYWAYROOT']
    if skywayroot == "":
        raise Exception("SKYWAYROOT is not defined.")

    # create an instance descriptor (like with the dashboard)
    instanceDescriptor = InstanceDescriptor(job_name, account_name, node_type, walltime, vendor_name)

    # submit job
    instanceDescriptor.submitJob(script_name=script)
