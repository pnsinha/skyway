# Copyright (c) 2019-2024 The University of Chicago.
# Part of skyway, released under the BSD 3-Clause License.

# Maintainer: Trung Nguyen
"""@package docstring
Documentation for Azure Class
"""
import os
import logging
from tabulate import tabulate
from datetime import datetime, timezone

from .core import Cloud
from .. import utils

from azure.identity import ClientSecretCredential
from azure.mgmt.compute import ComputeManagementClient
from azure.mgmt.network import NetworkManagementClient
from azure.mgmt.resource import ResourceManagementClient

from libcloud.compute.types import Provider
from libcloud.compute.providers import get_driver
from libcloud.compute.drivers.azure_arm import AzureImage, NodeAuthSSHKey

class AZURE(Cloud):

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
        if account_cfg['cloud'] != 'azure' :
            raise Exception(f'Cloud vendor azure is not associated with this account.')

        for k, v in account_cfg.items():
            setattr(self, k.replace('-','_'), v)

        # load cloud.yaml under $SKYWAYROOT/etc/
        path = os.environ['SKYWAYROOT'] + '/etc/'
        vendor_cfg = utils.load_config('cloud', path)
        if 'azure' not in vendor_cfg:
            raise Exception(f'Cloud vendor azure is undefined.')
      
        self.vendor = vendor_cfg['azure']
        self.account_name = account
        
        self.credentials = ClientSecretCredential(client_id=self.account['client_id'],
                                                  client_secret=self.account['client_secret'],
                                                  tenant_id=self.account['tenant_id'])

        try:
            Azure = get_driver(Provider.AZURE_ARM)
            self.driver = Azure(tenant_id=self.credentials._tenant_id,
                                subscription_id=self.account['subscription_id'],
                                key=self.credentials._client_id,
                                secret=self.account['client_secret'])

        except Exception as e:
            print(f"An error occurred: {e}")
        
        assert(self.driver != False)
        return

    def list_nodes(self, verbose=False):
        """Member function: list_nodes
        Get a list of all existed instances
        
        Return: a list of multiple turple. Each turple has four elements:
                (1) instance name (2) state (3) type (4) identifier
        """
        nodes = []
        current_time = datetime.now(timezone.utc)
        for node in self.driver.list_nodes():

            # Get the creation time of the instance
            creation_time_str = node.extra.get('properties')['timeCreated']  # Azure
            if creation_time_str:
                # Convert the creation time from string to datetime object
                creation_time = datetime.strptime(creation_time_str, '%Y-%m-%dT%H:%M:%S.%f%z')
                
                # Calculate the running time
                running_time = current_time - creation_time               
                nodes.append([node.name, node.state, node.size, node.id, node.public_ips[0], running_time])

        if verbose == True:
            print(tabulate(nodes, headers=['Name', 'Status', 'Type', 'Instance ID', 'Host', 'Running Time']))
            print("")


    def create_nodes(self, node_type: str, node_names = []):
        user_name = os.environ['USER']

        nodes = {}

        node_cfg = self.vendor['node-types'][node_type]
        size_name = node_cfg['name']           # e.g. "Standard_DS1_v2"
        
        for node_name in node_names:
            location_name = 'East US'  # Replace with your desired location
            locations = self.driver.list_locations()
            location = next((loc for loc in locations if loc.name == location_name), None)
            if location is None:
                raise ValueError(f"Location '{location_name}' not found.")

            # authentication with public key on this machine per-user (id_rsa_azure.pub)
            auth = NodeAuthSSHKey('ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAACAQDXzS0IuhNV3EyNkUXRV0yML0Fi+r+7qkqQqC7Ahe239ct3wwj1uwFnHo6UxF7zH7i33rtP/0YX5aV0l1fxp/7S3pF7Y0ZQDYryW15DxDxxjHkbNEssZjQ0XYWtf6g6VD5v8UWZAFvctqytbE2f39xDRimvifQMh8ogG45zRquKfuZ1vmtT/ls/7iW4cRtVjXNhN+lEmggZ+183akqDE0OJ01SM0aVNULxo/CB/nZFibgZ6YgQ8Ak/h5d3cHRH2YHQE6Szqi9+jYn/+99xLzQTfu6fF4uV2xw7BJ+O6UKvvJhYQMS/LUV14xmWfwJxJX/4lUh3Yc58kWZp4GSTpdyMByU/ejrvsrDkbzmjwu/TgSrAADfMxBMnVHkLhg9hhCmYDAtlY79OxMPt5WQtIZcZJbBJNW5d6fuOM6dEvw7p3Qu/QNhgEbYXYnlW+izPVhcuqe2YvmnnLKYERPSQS4VAsZhboRilmCotfJXxSC7Uf4oDbRdBxnZRvwC6vssj3tIiBY9sHXSFZyOH1d0MhmrQzwt09L0GrMgdthVPdhWW/V19pvhFnV8UNpanJXy09IiuCrJsKYz7k4YfPiCJppPU9xXMcYyZ9QOLKDmPZbUpEySZAPf77AaeUnp6xcDb9zF7+iOx4xjw3ZzMuCQfWhefu7kLOPHml+OukupmPCP6jyQ== ndtrung@fedora')
            resource_group = "rg_skyway"

            # Initialize Azure management clients
            resource_client = ResourceManagementClient(self.credentials, self.subscription_id)
            network_client = NetworkManagementClient(self.credentials, self.subscription_id)
            compute_client = ComputeManagementClient(self.credentials, self.subscription_id)

            
            sizes = self.driver.list_sizes(location=location)
            size = next((s for s in sizes if s.name == size_name), None)
            if size is None:
                raise ValueError(f"Size '{size_name}' not found.")

            publisher = 'Canonical'
            offer = 'UbuntuServer'
            sku = '18.04-LTS'
            version = 'latest'
            image = AzureImage(version=version, publisher=publisher, sku=sku, offer=offer, driver=self.driver, location=location)

            # Step 2: Create a resource group if it doesn't exist    
            resource_client.resource_groups.create_or_update(resource_group, {"location": location_name})

            # Step 3: Create Virtual Network and Subnet if they don't exist
            vnet_name = "vnet-{}-{}".format(user_name, node_name)
            subnet_name = "subnet-{}-{}".format(user_name, node_name)
            vnet_params = {
                "location": location_name,
                "address_space": {"address_prefixes": ["10.0.0.0/16"]}
            }
            network_client.virtual_networks.begin_create_or_update(resource_group, vnet_name, vnet_params).result()

            subnet_params = {
                "address_prefix": "10.0.0.0/24"
            }
            network_client.subnets.begin_create_or_update(resource_group, vnet_name, subnet_name, subnet_params).result()

            # Step 4: Create a network interface
            nic_name = "my-nic-{}".format(node_name)
            public_ip = self.driver.ex_create_public_ip(name=f'my_public_ip-{node_name}',
                                                        resource_group=resource_group,
                                                        location=location)
            ip_config = {
                "name": "ipconfig1",
                "subnet": {"id": f"/subscriptions/{self.subscription_id}/resourceGroups/{resource_group}/providers/Microsoft.Network/virtualNetworks/{vnet_name}/subnets/{subnet_name}"},
                'public_ip': public_ip
            }
        
            nic_params = {
                "location": location_name,
                "ip_configurations": [ip_config]
            }
            network_interface = network_client.network_interfaces.begin_create_or_update(resource_group, nic_name, nic_params).result()

            # Step 5: Create the instance          
            try:
                node = self.driver.create_node(name=node_name,
                                               size=size,
                                               image=image,
                                               auth=auth,
                                               location=location,
                                               ex_resource_group=resource_group,
                                               ex_nic=network_interface,
                                               ex_use_managed_disks=True)
            except Exception as ex:
                logging.info("Failed to create %s. Reason: %s" % (node_name, str(ex)))

            nodes[node_name] = [node_name, node.public_ips[0]]

        return nodes

    def connect_node(self, node_name):
        pass

    def destroy_node(self, node_names):
        if isinstance(node_names, str): node_names = [node_names]
        
        for name in node_names:
            try:
                node = self.driver.ex_get_node(name)
                self.driver.destroy_node(node)
            except:
                continue
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
            
    def get_host_ip(self, node_name):
        pass