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

# list all the node types available
#aws_account.node_types()

# list all the users in this account
#aws_account.group_members()

# check if the current user is valid (and able to submit jobs)
#user = os.environ['USER']
#aws_account.check_valid_user(user)

# create 1 node (instance)
#nodes = aws_account.create_nodes('t1',['node1'])

# list all the nodes (instances)
nodes = aws_account.list_nodes(verbose=True)
#nodes = aws_account.running_nodes(verbose=True)

# connect to an instance via SSH
# NOTE: 
#   + module unload python/anaconda-2021.05 to avoid OpenSSL conflict
#   + once on the node, can mount the storage (see  /skyway/post/rcc-aws.sh)
#       sudo mount -t nfs 172.31.47.245:/skyway /home
#       sudo mount -t nfs 172.31.47.245:/software /software
#       sudo mkdir /cloud
#       sudo mkdir /cloud/rcc-aws
#       sudo mount -t nfs 172.31.47.245:/cloud/rcc-aws /cloud/rcc-aws
# where 172.31.47.245 is the private IP4 address of the rcc-io instance (18.224.41.227)

#aws_account.connect_node('i-08889d84cf1ec9eba')


# get the current cost of all the running instances
#aws_account.get_running_cost()

# terminate an instance
#aws_account.destroy_nodes(['i-08889d84cf1ec9eba'])




