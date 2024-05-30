#import nest_asyncio

import skyway
from skyway.cloud.aws import *
from skyway.cloud.gcp import *
from skyway.cloud.azure import *

import os
from datetime import datetime, timezone
import streamlit as st

class InstanceDescriptor:
  def __init__(self, jobname: str, account_name: str, node_type: str, gpus: int, walltime: str):
    self.jobname = jobname
    self.account_name = account_name
    self.node_type = node_type.split(' ')[0]
    self.gpus = gpus
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
    self.account.create_nodes(self.node_type, ['node1'], walltime=self.walltime)
    st.success('Your job has been submitted!')
    pending = True
    return pending

  def getBalance(self):
    # retrieve from database for the given account
    return self.account.get_budget(user_name=self.user)

  def get_estimate_cost(self):
    pt = datetime.strptime(self.walltime, "%H:%M:%S")
    walltime_in_hours = int(pt.hour + pt.minute/60)
    unit_price = float(self.account.get_unit_price(self.node_type))
    cost = walltime_in_hours * unit_price
    return cost
  
  def list_nodes(self):
    nodes, list_of_nodes = self.account.list_nodes(verbose=False) 
    return list_of_nodes

#nest_asyncio.apply()

st.set_page_config(layout='wide')

logo_file = os.path.join(os.path.dirname(__file__), 'logo.png')
if os.path.isfile(logo_file):
    st.image(logo_file,width=750)

#st.markdown("### 📘 RCC User Guide Chatbot 🤖")
st.markdown("## 📘 Skyway GUI")

col1, col2 = st.columns((1,1))

with col1:
  st.markdown("#### Requested resources")
  job_name = st.text_input(r"$\textsf{\large Job name}$", "your_run")
  allocation = st.text_input(r"$\textsf{\large Allocation}$", "ndtrung-aws")

  node_type = st.selectbox(r"$\textsf{\large Node type}$", ('t1 (single core)', 'c1 (single core)', 'c36 (36-core)', 'g1 (1 GPU)'))
  walltime = st.text_input(r"$\textsf{\large Walltime (HH:MM:SS)}$", "02:00:00")
  gpus = st.text_input(r"$\textsf{\large Number of GPUs per node}$", "0")

  envs = st.selectbox(r"$\textsf{\large Running environments}$", ('CLI', 'GUI'))
  if envs == 'CLI':
      cmd = ""
  elif envs == 'GUI':
      cmd = ""      
  else:
      cmd = ""

with col2:
  
  account_name = allocation.lower()

  # estimate number of SUs
  instanceDescriptor = InstanceDescriptor(job_name, account_name, node_type, gpus, walltime)
  estimatedSU = instanceDescriptor.get_estimate_cost()

  st.markdown("#### Estimated cost")
  st.markdown("$" + str(estimatedSU), help="Estimated based on the requested cloud resource and walltime")
  balance = instanceDescriptor.getBalance()
  st.markdown("Current balance: $" + str(balance))
  st.markdown("Balance after job completion: $" + str(balance-estimatedSU))
  
  pending = False
  if st.button('Submit', type='primary', on_click=instanceDescriptor.submitJob):
    st.markdown("#### Job status")
    jobs = st.empty()
    jobs.write("Your job is pending..")

  st.markdown("#### Running instances")
  instance_list = st.empty() 
  instance_list.write(instanceDescriptor.list_nodes())
  

st.markdown("""Made with ❤️ by the RCC team""")
