# Skyway Dashboard
# Contact: Trung Nguyen (ndtrung@uchicago.edu)
# module load python/anaconda-2021.05
# python -m venv skyway-env
# source activate skyway-env
# pip install pandas pyyaml pymysql tabulate boto3 apache-libcloud cryptography paramiko streamlit
# export SKYWAYROOT=/home/ndtrung/Codes/skyway-github
# export SKYWAYROOT=/project/rcc/trung/skyway-github

import skyway
from skyway.cloud.aws import *
from skyway.cloud.gcp import *
from skyway.cloud.azure import *

import os
from datetime import datetime, timezone
import streamlit as st
import pandas as pd
#import nest_asyncio

class InstanceDescriptor:
    def __init__(self, jobname: str, account_name: str, node_type: str, walltime: str):
        self.jobname = jobname
        self.account_name = account_name
        self.node_type = node_type.split(' ')[0]
        self.walltime = walltime

        self.account = None
        if 'aws' in account_name:
            self.account = AWS(account_name)
        elif 'gcp' in account_name:
            self.account = GCP(account_name)
        elif 'azure' in account_name:
            self.account = AZURE(account_name)

        self.user = os.environ['USER']

    def submitJob(self):
        #st.warning("Do you want to create this instance?")
        #if st.button("Yes"):
        self.account.create_nodes(self.node_type, [job_name], need_confirmation=False, walltime=self.walltime)
        initializing = True   
        return initializing

    def terminateJob(self, node_names = []):
        st.write(f"Terminating instances {node_names}...")
        self.account.destroy_nodes(node_names=node_names, need_confirmation=False)

    def getBalance(self):
        # retrieve from database for the given account
        return self.account.get_budget(user_name=self.user, verbose=False)

    def getEstimateCost(self):
        pt = datetime.strptime(self.walltime, "%H:%M:%S")
        walltime_in_hours = int(pt.hour + pt.minute/60)
        unit_price = float(self.account.get_unit_price(self.node_type))
        cost = walltime_in_hours * unit_price
        return cost
  
    def list_nodes(self):
        nodes, list_of_nodes = self.account.list_nodes(verbose=False) 
        return nodes


if __name__ == "__main__":

    #nest_asyncio.apply()    
    st.set_page_config(layout='wide')
    logo_file = os.path.join(os.path.dirname(__file__), 'logo.png')
    if os.path.isfile(logo_file):
        st.image(logo_file,width=450)

    #st.markdown("### :blue_book:  RCC User Guide Chatbot 🤖") 
    st.markdown("## Skyway Dashboard")

    col1, col2, col3 = st.columns((1,2,2))

    with col1:
        st.markdown("Instances")
        st.markdown("Usage")

    with col2:
        st.markdown("#### Requested resources")
        job_name = st.text_input(r"$\textsf{\large Job name}$", "your_run")
        allocation = st.text_input(r"$\textsf{\large Allocation}$", "ndtrung-aws")
        vendor = st.selectbox(r"$\textsf{\large Vendor}$", ('Amazon Web Services (AWS)', 'Google Cloud Platform (GCP)', 'Microsoft Azure'))

        # populate this select box depending on the allocation (account.yaml)
        vendor_name = vendor.lower()
        if 'aws' in vendor_name:
            node_types = ('t1 (t2.micro, 1-core CPU)', 'c1 (c5.large, 1-core CPU)', 'c36 (c5.18xlarge, 36-core CPU)', 'g1 (p3.2xlarge, 1 V100 GPU)')
        elif 'gcp' in vendor_name:
            node_types = ('c1 (n1-standard-1, 1-core CPU)', 'c4 (c2-standard-8, 4-core CPU)', 'g1 (n1-standard-8, 4-core CPU)')
        elif 'azure' in vendor_name:
            node_types = ('c1 (Standard_DS1_v2, 1-core CPU)', 'b4 (Standard_B2ts_v2, 2-core CPU)', 'b32 (Standard_B32ls_v2, 32-core)', 'g1 (Standard_NC6s_A100_v3, 1 A100 GPU)')

        node_type = st.selectbox(r"$\textsf{\large Node type}$", node_types)
        walltime = st.text_input(r"$\textsf{\large Walltime (HH:MM:SS)}$", "02:00:00")

        envs = st.selectbox(r"$\textsf{\large Interaction with the node}$", ('Command Line Interface', 'Graphical User Interface'))
        if envs == 'Command Line Interface':
            cmd = ""
        elif envs == 'Graphical User Interface':
            cmd = ""      
        else:
            cmd = ""

    with col3:
      
        account_name = allocation.lower()

        # estimate number of SUs
        instanceDescriptor = InstanceDescriptor(job_name, account_name, node_type, walltime)
        estimatedSU = instanceDescriptor.getEstimateCost()

        st.markdown("#### Estimated cost")
        st.markdown("$" + str(estimatedSU), help="Estimated based on the requested node type and walltime")
        balance = instanceDescriptor.getBalance()
        st.markdown("Current balance: $" + str(balance))
        st.markdown("Balance after job completion would be: $" + str(balance - estimatedSU))

        pending = False
        jobs = st.empty()
        if st.button('Submit', type='primary', on_click=instanceDescriptor.submitJob):
            #st.markdown("#### Job status")
            jobs.write("Node initializing..")

        st.markdown("#### Running instances")
        headers=['Name', 'Status', 'Type', 'Instance ID', 'Host', 'Elapsed Time', 'Running Cost']
        
        nodes = instanceDescriptor.list_nodes()

        df = pd.DataFrame(nodes, columns=headers)
        df.style.hide(axis="index")
        st.table(df)

        if st.button('Terminate', type='primary'):
            instanceDescriptor.terminateJob(node_names=['your_run'])

        st.markdown("#### Usage statistics")

    st.markdown("""Developed by the UChicago Research Computing Center""")
