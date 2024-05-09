# module load python/anaconda-2021.05
# python -m venv skyway-env
# source activate skyway-env
# pip install pandas pyyaml pymysql tabulate boto3
# export SKYWAYROOT=/home/ndtrung/Codes/skyway-dev

import skyway
from skyway import account
from skyway import billing

from skyway import cloud
from skyway.cloud import aws
from skyway.cloud.aws import *

from datetime import datetime, timezone

from skyway import service
from skyway.service import core

from skyway import utils
from skyway import cfg

import pandas as pd
from tabulate import tabulate

# Test account
#account.list()
#account.show("rcc-aws")

# Test billing
#b = billing.Billing("rcc-aws")
#u = b.usages()

#print("Summary")
#print("Budget:       $%0.3f (started from %s)" % (u['budget']['amount'], u['budget']['startdate']))
#print("Maximum Rate: $%0.3f/hour" % (u['budget']['rate']))
#print("Current Rate: $%0.3f/hour" % (u['rate']))
#print("Total Cost:   $%0.3f" % (u['total']))
#print("Balance:      $%0.3f" % (u['budget']['amount'] - u['total']))
#print("Status:       %s\n" % (u['status'].upper()))

# Test service
#service.core.register("cloud-rcc-aws")
#service.core.start("cloud-rcc-aws")
#service.core.stop("cloud-rcc-aws")
#service.core.get_status("cloud-rcc-aws")
#service.core.list_all()

# Test cloud nodes
aws_account = AWS('rcc-aws')

# create 1 node (instance)
#aws_account.create_nodes('t1',['test'])

# list all the nodes (instances)
nodes = aws_account.list_nodes(verbose=True)
#nodes = aws_account.running_nodes(verbose=True)

# connect to an instance via SSH
#aws_account.connect_node('i-05b1fecb479b09722')

# get the current cost of all the running instances
#aws_account.get_running_cost()

# terminate an instance
#aws_account.destroy_nodes(['i-01a3d974d12c9d4e6'])




