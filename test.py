# module load python/anaconda-2021.05
# python -m venv skyway-env
# source activate skyway-env
# pip install pandas pyyaml pymysql tabulate boto3 apache-libcloud cryptography paramiko
# export SKYWAYROOT=/home/ndtrung/Codes/skyway-github
# export SKYWAYROOT=/project/rcc/trung/skyway-github

# for PI-test to create nodes: needs an ami-id and a security group, and a key pair 

import skyway
from skyway import account
from skyway import billing

import subprocess

from skyway import cloud
#from skyway.cloud import aws
#from skyway.cloud import gcp
from skyway.cloud.aws import *
from skyway.cloud.gcp import *
from skyway.cloud.azure import *
from skyway.cloud.slurm import *
from skyway.cloud.oci import *

from datetime import datetime, timezone

from skyway import service
from skyway.service import core

# Test account
#account.list()
#account.show("ndtrung-aws")
#account.show("ndtrung-gcp")
#account.show("ndtrung-azure")

# Test billing
#b = billing.Billing("ndtrung-aws")
#u = b.usages(verbose=True)

# Test service
#service.core.register("cloud-rcc-aws")
#service.core.start("cloud-rcc-aws")
#service.core.stop("cloud-rcc-aws")
#service.core.get_status("cloud-rcc-aws")
#service.core.list_all()

# Test cloud nodes
#account = AWS('rcc-aws')
#account = GCP('rcc-gcp')
#account = GCP('ndtrung-gcp')
#account = AZURE('rcc-azure')
account = OCI('ndtrung-oci')

#account = SLURMCluster('rcc-slurm')

# list all the node types available
account.get_node_types()

# list all the users in this account
#account.get_group_members()

# check if the current user is valid (and able to submit jobs)
user_name = os.environ['USER']
#account.check_valid_user(user_name)
#account.get_budget()

# create 1 node (instance)
#nodes = account.create_nodes('t1', ['your-run'], walltime="00:15:00")
#account.get_all_images()

# list all the nodes (instances)
nodes, output_str = account.list_nodes(verbose=True)


#account.get_cost_and_usage("2024-05-30", "2024-06-04", verbose=True)
#account.get_budget_api()
#nodes = account.get_running_nodes(verbose=True)

# connect to an instance via SSH
# NOTE: this is for the rcc-aws account
#   + module unload python/anaconda-2021.05 to avoid OpenSSL conflict
#   + once on the node, can mount the storage (see  /skyway/post/rcc-aws.sh)
#       sudo mount -t nfs 172.31.47.245:/skyway /home
#       sudo mount -t nfs 172.31.47.245:/software /software
#       sudo mkdir /cloud
#       sudo mkdir /cloud/rcc-aws
#       sudo mount -t nfs 172.31.47.245:/cloud/rcc-aws /cloud/rcc-aws
# where 172.31.47.245 is the private IP4 address of the rcc-io instance (18.224.41.227)
# For ndtrung-aws, 172.31.47.245 is not visible, whereas 18.224.41.227 gives access denied

#account.connect_node('node1')
#account.connect_node('midway3-0038')

# get the current cost of all the running instances
#account.get_running_cost()

# terminate an instance
#account.destroy_nodes(node_names=['yourRun'])
#account.destroy_nodes(IDs=['i-06fc520e0c8e6fd34'])

# Slurm service needs job IDs
#account.destroy_nodes(IDs=['21138341'])





