# Copyright (c) 2019-2024 The University of Chicago.
# Part of skyway, released under the BSD 3-Clause License.

# Maintainer: Yuxing Peng, Trung Nguyen

"""@package docstring
Documentation for AWS Class
"""
import os
from tabulate import tabulate
from .core import Cloud
from .. import utils

from datetime import datetime, timezone

import boto3

class AWS(Cloud):
    """Documentation for AWS Class
    This Class is used as the driver to operate Cloud resource for [Demo]
    """
    
    def __init__(self, account):
        """Constructor:
        The construct initialize the connection to the cloud platform, by using
        setting informations passed by [cfg], such as the credentials.        

        account [string]
        """

        #super().__init__(vendor_cfg, kwargs)

        # load [account].yaml under $SKYWAYROOT/etc/accounts
        path = os.environ['SKYWAYROOT'] + '/etc/accounts/'
        account_cfg = utils.load_config(account, path)
        if account_cfg['cloud'] != 'aws' :
            raise Exception(f'Cloud vendor aws is not associated with this account.')

        for k, v in account_cfg.items():
            setattr(self, k.replace('-','_'), v)

        # load cloud.yaml under $SKYWAYROOT/etc/
        path = os.environ['SKYWAYROOT'] + '/etc/'
        vendor_cfg = utils.load_config('cloud', path)
        if 'aws' not in vendor_cfg:
            raise Exception(f'Cloud vendor aws is undefined.')

        self.vendor = vendor_cfg['aws']
        self.account_name = account

        # This is how the existing skyway creates the ec2 resource without master
        #self.ec2 = boto3.resource('ec2',
        #    aws_access_key_id = self.account['access_key_id'],
        #    aws_secret_access_key = self.account['secret_access_key'],
        #    region_name = self.account['region'])

        # This is how the testing skyway (midway3 VM) uses the IAM rcc-skyway from the RCC-Skyway account (391009850283)
        self.client = boto3.client('sts',
            aws_access_key_id = self.vendor['master_access_key_id'],
            aws_secret_access_key = self.vendor['master_secret_access_key'])

        self.assumed_role = self.client.assume_role(
            RoleArn = "arn:aws:iam::%s:role/%s" % (self.account['account_id'], self.account['role_name']), 
            RoleSessionName = "RCCSkyway"
        )
        
        credentials = self.assumed_role['Credentials']
        
        self.ec2 = boto3.resource('ec2',
            aws_access_key_id = credentials['AccessKeyId'],
            aws_secret_access_key = credentials['SecretAccessKey'],
            aws_session_token= credentials['SessionToken'],
            region_name = self.account['region'])

        return

    def list_nodes(self, verbose=False):
        """Member function: list_nodes
        Get a list of all existed instances
        
        Return: a list of multiple turple. Each turple has four elements:
                (1) instance name (2) state (3) type (4) identifier
        """
        
        instances = self.get_instances()
        nodes = []
        
        for instance in instances:
            if instance.state['Name'] != 'terminated':
                nodes.append([self.get_instance_name(instance),
                              instance.state['Name'], 
                              instance.instance_type, 
                              instance.instance_id,
                              instance.public_ip_address])
        
        if verbose == True:
            print(tabulate(nodes, headers=['Name', 'Status', 'Type', 'Instance ID', 'Host']))
            print("")
        return nodes

    def create_nodes(self, node_type: str, node_names = []):
        """Member function: create_compute
        Create a group of compute instances(nodes, servers, virtual-machines 
        ...) with the given type.
        
         - node_type: instance type information from the Skyway definitions
         - node_names: a list of names for the nodes, to get the number of nodes
        
        Return: a dictionary of instance ID (i.e., names) for created instances.
        """
        unit_price = self.vendor['node-types'][node_type]['price']
        response = input(f"Do you want to create an instance of type {node_type} (${unit_price}/hr)? (y/n) ")
        if response == 'n':
            return

        count = len(node_names)      
        name = node_names[0]

        # ImageID and KeyName provided by the account then user can connect to the running node
        #   if ImageID is from the vendor, KeyName from the account, ssh connections is denied
        instances = self.ec2.create_instances(
            ImageId          = self.account['ami_id'],    # self.vendor['ami_id']
            KeyName          = self.account['key_name'],  # self.vendor['key_name']
            SecurityGroupIds = self.account['security_group'],
            InstanceType     = self.vendor['node-types'][node_type]['name'],
            MaxCount         = count,
            MinCount         = count,
            TagSpecifications=[
                {
                    'ResourceType' : 'instance',
                    'Tags' : [
                         {
                            'Key' : 'Name',
                            'Value' : name
                         }
                    ]
                },

            ])

        for instance in instances:
            instance.wait_until_running()
        
        nodes = {}

        path = os.environ['SKYWAYROOT'] + '/etc/accounts/'
        pem_file_full_path = path + self.account['key_name'] + '.pem'
        username = self.vendor['username']
        region = self.account['region']

        for inode, instance in enumerate(instances):
            instance.load()
            nodes[node_names[inode]] = [str(instance.id), str(instance.public_ip_address)]

            # perform post boot tasks on each node
            #   + mounting storage (/home, /software) from io-server 172.31.47.245
            #   + executing custom scripts
            #    + 
            ip = instance.public_ip_address
            ip_converted = ip.replace('.','-')
            
            cmd = f"ssh -i {pem_file_full_path} {username}@ec2-{ip_converted}.{region}.compute.amazonaws.com -t 'sudo mount -t nfs 172.31.47.245:/skyway /home' "
            print(f"{cmd}")
            os.system(cmd)


        return nodes

    def connect_node(self, instance_ID):
        """
        Connect to an instance using account's pem file
        [account_name].pem file should be under $SKYWAYROOT/etc/accounts
        It is important to create the node using the account's key-name.
        """
        print(f"Instance ID: {instance_ID}")
        ip = self.get_host_ip(instance_ID)
        print(f"Connect to instance public IP address: {ip}")

        path = os.environ['SKYWAYROOT'] + '/etc/accounts/'
        pem_file_full_path = path + self.account['key_name'] + '.pem'
        username = self.vendor['username']
        region = self.account['region']
        ip_converted = ip.replace('.','-')
        
        cmd = f"ssh -i {pem_file_full_path} {username}@ec2-{ip_converted}.{region}.compute.amazonaws.com -t 'echo \"Welcome to AWS EC2!\"; bash -l' "
        #print(f"{cmd}")
        os.system(cmd)

    def destroy_nodes(self, IDs = []):
        """Member function: destroy nodes
        Destroy a group of compute instances
        NOTE: should store the running cost and time before terminating the node(s)

         - IDs: a group of identifiers of instances to be destroyed
        """
        
        instances = []
        
        for ID in IDs:
        
            instance = self.ec2.Instance(ID)
            
            if self.get_instance_name(instance) in self.account['protected_nodes']:
                continue
            
            running_time = datetime.now(timezone.utc) - instance.launch_time
            instance_unit_cost = self.get_unit_price(instance)
            running_cost = running_time.seconds/3600.0 * instance_unit_cost
            #print(f"Instance {ID} running cost: ")

            response = input(f"Do you want to terminate the instance {ID} (running cost ${running_cost:0.5f})? (y/n) ")
            if response == 'y':
                # record the running time and cost
                running_time = datetime.now(timezone.utc) - instance.launch_time
                instance_unit_cost = self.get_unit_price(instance)
                running_cost = running_time.seconds/3600.0 * instance_unit_cost
                
                
                instance.terminate()
                instances.append(instance)
        
        for instance in instances:
            instance.wait_until_terminated()
        
        return

    def check_valid_user(self, user_name, verbose=False):
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

    def get_running_nodes(self, verbose=False):
        """Member function: running_nodes
        Return identifiers of all running instances
        """

        instances = self.get_instances(filters = [{
            "Name" : "instance-state-name",
            "Values" : ["running"]
        }])
        
        nodes = []
        
        for instance in instances:
            nodes.append([self.get_instance_name(instance),
                              instance.state['Name'], 
                              instance.instance_type, 
                              instance.instance_id])
        
        if verbose == True:
            print(tabulate(nodes, headers=['Name', 'Status', 'Type', 'Instance ID', 'Host IP']))
            print("")


        return nodes

    def get_host_ip(self, instance_ID):
        """Member function: SSH to a remote instance
        This function prepare the IP address and SSH to the node with the
        given identifier.
        
         - ID: instance identifier
        """
        
        if instance_ID[0:2] == 'i-':
            instances = self.get_instances(filters = [{
                "Name" : "instance-id",
                "Values" : [instance_ID]
            }])
        else:
            instances = self.get_instances(filters = [{
                "Name" : "tag:Name",
                "Values" : [instance_ID]
            }])
        
        return list(instances)[0].public_ip_address


    def get_all_images(self, owners=['self']):
        try:
            # Describe images to get all AMIs
            images = self.ec2.images.filter(Owners=owners)

            for image in images:
                print(f"Image ID: {image.id}, Name: {image.name}, Description: {image.description}")

        except Exception as e:
            print(f"An error occurred: {e}")

    def get_instance_name(self, instance):
        """Member function: get_instance_name
        Get the name information from the instance with given ID.
        Note: AWS doesn't use unique name for instances, instead, name is an
        attribute stored in the tags.
        
         - instance: an instance self.ec2.Instance()
        """
        
        if instance.tags is None: return ''

        for tag in instance.tags:
            if tag['Key'] == 'Name':
                return tag['Value']
        
        return ''


    def get_instances(self, filters = []):
        """Member function: get_instances
        Get a list of instance objects with give filters
        """
        
        return self.ec2.instances.filter(Filters = filters)


    def get_cost(self, start, end):
        
        pass

    def get_unit_price(self, instance):
        """
        Get the per-hour price of an instance depending on its instance_type (e.g. t2.micro)
        """
        for node_type in self.vendor['node-types']:
            if self.vendor['node-types'][node_type]['name'] == instance.instance_type:
                instance_type = self.vendor['node-types'][node_type]['name']
                unit_price = self.vendor['node-types'][node_type]['price']
                return unit_price

    def get_running_cost(self):
        instances = self.get_instances()

        nodes = []
        for instance in instances:
            
            if self.get_instance_name(instance) in self.account['protected_nodes']:
                continue

            if instance.state['Name'] == 'running':
                running_time = datetime.now(timezone.utc) - instance.launch_time
                instance_unit_cost = self.get_unit_price(instance)
                running_cost = running_time.seconds/3600.0 * instance_unit_cost

                nodes.append([self.get_instance_name(instance),
                                    instance.state['Name'], 
                                    instance.instance_type, 
                                    instance.instance_id,
                                    running_time,
                                    running_cost])

        print(tabulate(nodes, headers=['Name', 'Status', 'Type', 'Instance ID', 'ElapsedTime', 'RunningCost']))
