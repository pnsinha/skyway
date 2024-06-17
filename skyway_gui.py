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
import subprocess
from datetime import datetime, timezone
from io import StringIO

import streamlit as st
from streamlit_autorefresh import st_autorefresh

import pandas as pd
#import nest_asyncio

class InstanceDescriptor:
    def __init__(self, jobname: str, account_name: str, node_type: str, walltime: str, vendor_name: str):
        self.jobname = jobname
        self.account_name = account_name
        self.node_type = node_type.split(' ')[0]
        self.walltime = walltime
        self.vendor_name = vendor_name

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
        if "midway3" in self.vendor_name:
            self.connectJob([self.jobname])
        else:
            print(f"creating node from {self.vendor_name} with account {self.account_name}")
            self.account.create_nodes(self.node_type, [self.jobname], need_confirmation=False, walltime=self.walltime)
        initializing = True
        return initializing

    def connectJob(self, node_names):
        '''
        only get on a on-premise compute node for now with rcc-staff
        '''
        ppn = 1
        mem = 4
        partition = "caslake"
        if "midway3" in self.vendor_name:
            if "t1" in self.node_type:
                ppn = 1
                mem = 4
            elif "c4" in self.node_type:
                ppn = 4
                mem = 16
            elif "c16" in self.node_type:
                ppn = 16
                mem = 64
            elif "c48" in self.node_type:
                ppn = 48
                mem = 128
            elif "bigmeme" in self.node_type:
                ppn = 16
                mem = 512
                partition = "bigmem"
            cmd = "gnome-terminal --title='Connecting to the node' -- bash -c "
            cmd += f" 'sinteractive -J {self.jobname} -A rcc-staff -p {partition} --nodes=1 --ntasks-per-node={ppn} --mem={mem}GB -t {self.walltime}' "
            os.system(cmd)

        elif "aws" in self.vendor_name:
            instanceID = self.account.get_instance_ID(self.jobname)
            self.account.connect_node(instanceID)

        elif "gcp" in self.vendor_name:
            instanceID = self.account.get_instance_ID(self.jobname)
            self.account.connect_node(instanceID)

    def terminateJob(self, node_names = []):
        st.write(f"Terminating instances {node_names}...")
        self.account.destroy_nodes(node_names=node_names, need_confirmation=False)

    def getBalance(self):
        # retrieve from database for the given account
        if "midway3" in self.vendor_name:

            cmd = "rcchelp balance -a rcc-staff | awk \'$1 == \"rcc-staff\" {print $4}\' "
            proc = subprocess.Popen([cmd], stdout=subprocess.PIPE, shell=True)
            (out, err) = proc.communicate()
            remaining_balance = float(out)
        else:
            #budget = self.account.get_budget(user_name=self.user, verbose=False)
            accumulating_cost, remaining_balance = self.account.get_cost_and_usage_from_db(user_name=self.user)
        return remaining_balance

    def getEstimateCost(self):
        pt = datetime.strptime(self.walltime, "%H:%M:%S")
        walltime_in_hours = int(pt.hour + pt.minute/60)
        if "midway3" in self.vendor_name:
            unit_price = 1.0
        else:
            unit_price = float(self.account.get_unit_price(self.node_type))
        cost = walltime_in_hours * unit_price
        return cost
  
    def list_nodes(self):
        if "midway3" in self.vendor_name:
            nodes = []
            cmd = f"squeue -u {self.user}"
            proc = subprocess.Popen([cmd], stdout=subprocess.PIPE, shell=True)
            (out, err) = proc.communicate()
            
            cmd = f"export SQUEUE_FORMAT=\"%13i %.4t %24j %13i %N 0.0 0.0\"; squeue -u {self.user} | tail -n1"
            proc = subprocess.Popen([cmd], stdout=subprocess.PIPE, shell=True)
            (out, err) = proc.communicate()
            # encode output as utf-8 from bytes, remove newline character
            m = out.decode('utf-8').strip()
            # convert to a list
            m = m.split()
            if len(m) == 7:
                m[0] = self.jobname
                m[2] = self.node_type
                nodes = [m]

        else:
            nodes, list_of_nodes = self.account.list_nodes(verbose=False) 
        return nodes


if __name__ == "__main__":

    #nest_asyncio.apply()    
    st.set_page_config(layout='wide')
    logo_file = os.path.join(os.path.dirname(__file__), 'logo.png')
    if os.path.isfile(logo_file):
        st.image(logo_file,width=450)

    # autorefresh every 30 seconds, maximum 200 times
    count = st_autorefresh(interval=30000, limit=200, key="autorefreshcounter")

    #st.markdown("### :blue_book:  RCC User Guide Chatbot 🤖") 
    st.markdown("## Skyway Dashboard")

    col1, col2, col3 = st.columns((1,2,3))

    with col1:
        st.markdown("Instances")
        st.markdown("Usage")

    with col2:
        st.markdown("#### Requested resources")
        job_name = st.text_input(r"$\textsf{\large Job name}$", "yourRun")
        
        vendor = st.selectbox(r"$\textsf{\large Service provider}$", ('Amazon Web Services (AWS)', 'Google Cloud Platform (GCP)', 'Microsoft Azure', 'RCC Midway3'), help='Cloud vendors or on-premise clusters')

        # populate this select box depending on the allocation (account.yaml)
        vendor_name = vendor.lower()
        if 'aws' in vendor_name:
            node_types = ('t1 (t2.micro, 1-core CPU)', 'c1 (c5.large, 1-core CPU)', 'c36 (c5.18xlarge, 36-core CPU)', 'g1 (p3.2xlarge, 1 V100 GPU)')
            vendor_short = "aws"
            accounts = ('rcc-aws', 'ndtrung-aws')
        elif 'gcp' in vendor_name:
            node_types = ('c1 (n1-standard-1, 1-core CPU)', 'c4 (c2-standard-8, 4-core CPU)', 'g1 (n1-standard-8, 4-core CPU)')
            vendor_short = "gcp"
            accounts = ('rcc-gcp', 'ndtrung-gcp')
        elif 'azure' in vendor_name:
            node_types = ('c1 (Standard_DS1_v2, 1-core CPU)', 'b4 (Standard_B2ts_v2, 2-core CPU)', 'b32 (Standard_B32ls_v2, 32-core)', 'g1 (Standard_NC6s_A100_v3, 1 A100 GPU)')
            vendor_short = "azure"
            accounts = ('rcc-azure', 'ndtrung-azure')
        elif 'midway3' in vendor_name:
            node_types = ('t1 (1 CPU core + 4 GB RAM)', 'c4 (4 CPU cores + 16 GB RAM)', 'c16 (16 CPU cores + 64 GB RAM)', 'c48 (48 CPU cores + 128 GB RAM)', 'g1 (8 CPU cores + 1 V100 GPU)', 'bigmem (16 CPU cores + 512 GB RAM)')
            accounts = ('rcc-staff',)
            vendor_short = "midway3"

        # account or allocation
        #allocation = st.text_input(r"$\textsf{\large Account}$", "rcc-aws", key='account', help='Your cloud account (e.g. rcc-aws) or on-premises allocation (e.g. rcc-staff)')
        allocation = st.selectbox(r"$\textsf{\large Account}$", accounts, key='account', help='Your cloud account (e.g. rcc-aws) or on-premises allocation (e.g. rcc-staff)')
        node_type = st.selectbox(r"$\textsf{\large Node type}$", node_types, help='Instance type, or node configuration')
        walltime = st.text_input(r"$\textsf{\large Walltime (HH:MM:SS)}$", "02:00:00", help='Max walltime for the instance')

        envs = st.selectbox(r"$\textsf{\large Interaction with the node}$", ('Command Line Interface', 'Graphical User Interface'), help='Whether a CLI or GUI image should be loaded on the instance.')
        if envs == 'Command Line Interface':
            cmd = ""
        elif envs == 'Graphical User Interface':
            cmd = ""      
        else:
            cmd = ""

        uploaded_file = st.file_uploader(r"$\textsf{\large Choose a script to be executed on the node}$", help='The script contains the body of the job script.')
        if uploaded_file is not None:
            # To read file as bytes:
            bytes_data = uploaded_file.getvalue()
            st.write(bytes_data)

            # To convert to a string based IO:
            stringio = StringIO(uploaded_file.getvalue().decode("utf-8"))
            st.write(stringio)

            # To read file as string:
            string_data = stringio.read()
            st.write(string_data)

            # Can be used wherever a "file-like" object is accepted:
            #dataframe = pd.read_csv(uploaded_file)
            #st.write(dataframe)
    

    with col3:
      
        account_name = allocation.lower()

        # estimate number of SUs
        instanceDescriptor = InstanceDescriptor(job_name, account_name, node_type, walltime, vendor_name)
        estimatedSU = instanceDescriptor.getEstimateCost()

        st.markdown("#### Estimated cost for the node")
        balance = instanceDescriptor.getBalance()
        if "midway3" in vendor_name.lower():
            st.markdown(f"{int(estimatedSU)} SUs", help="Estimated based on the requested node type and walltime")
            st.markdown(f"Current balance: {int(balance)} SUs")
            st.markdown(f"Balance after job completion would be: {int(balance - estimatedSU)} SUs")
        else:
            st.markdown(f"${estimatedSU:0.3f}", help="Estimated based on the requested node type and walltime")
            st.markdown(f"Current balance: ${balance:0.3f}")
            st.markdown(f"Balance after job completion would be: ${balance - estimatedSU:0.3f}")

        pending = False
        jobs = st.empty()
        if st.button('Submit', type='primary', help='Create a cloud node or a compute node', on_click=instanceDescriptor.submitJob):
            #st.markdown("#### Job status")
            jobs.write("Node initializing..")

        st.markdown("#### Running nodes")
        headers=['Name', 'Status', 'Type', 'Instance ID', 'Host', 'Elapsed Time', 'Running Cost']
        
        nodes = instanceDescriptor.list_nodes()

        df = pd.DataFrame(nodes, columns=headers)
        df.style.hide(axis="index")
        st.table(df)

        if st.button('Connect', type='primary', help="Create an interactive session on the instance"):
            instanceDescriptor.connectJob(node_names=['your_run'])
        st.markdown("NOTE: Only support interactive sessions on the nodes provided by AWS, GCP and RCC Midway3 for now.")

        if st.button('Terminate', help=f'Destroy the instance named {job_name}', type='primary'):
            instanceDescriptor.terminateJob(node_names=[job_name])


        #st.markdown("#### Usage statistics")

    st.markdown("""Developed by the UChicago Research Computing Center""")
