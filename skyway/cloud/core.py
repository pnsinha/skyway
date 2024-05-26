# Copyright (c) 2019-2024 The University of Chicago.
# Part of skyway, released under the BSD 3-Clause License.

# Maintainer: Yuxing Peng, Trung Nguyen

import os
from .. import utils

# Provide the API for child classes to override

class Cloud():
    
    @staticmethod
    def create(vendor: str, kwargs):
        print(f"Vendor: {vendor}")
        vendor = vendor.lower()
        # load cloud.yaml under $SKYWAYROOT/etc/
        vendor_cfg = utils.load_config('cloud')
        print(f"Vendor cfg: {vendor_cfg}")
        if vendor not in vendor_cfg:
            raise Exception(f'Cloud vendor {vendor} is undefined.')

        from importlib import import_module
        module = import_module('skyway.cloud.' + vendor)
        cloud_class = getattr(module, vendor.upper())
        return cloud_class(vendor_cfg[vendor], kwargs)
    
    def __init__(self, vendor_cfg, kwargs):
        self.vendor = vendor_cfg
        
        for k, v in kwargs.items():
            setattr(self, k.replace('-','_'), v)
    
    def list_nodes(self, verbose=False):
        '''
        list all the running/stopped nodes (aka instances)
        '''
        pass

    def create_nodes(self, node_type: str, node_names = []):
        '''
        create several nodes (aka instances) given a list of node names
        '''
        pass

    def connect_node(self, node_name):
        '''
        connect to a node (aka instance) via SSH
        '''
        pass

    def destroy_nodes(self, node_names):
        '''
        destroy several nodes (aka instances) given a list of node names
        '''
        pass

    def check_valid_user(self, user_name, verbose=False):
        '''
        check if a user name is in the cloud account
        '''
        pass

    def get_budget(self, user_name=None, verbose=True):
        '''
        get the current budget of the whole account, or of a user name
        '''
        pass

    def get_node_types(self):
        '''
        get the node types available to the account
        '''
        pass

    def get_group_members(self):
        '''
        get all the user names in this account (listed in the .yaml file)
        '''
        pass

    def get_running_nodes(self, verbose=False):
        '''
        list all the running nodes (aka instances)
        '''
        pass

    def get_host_ip(self, node_name):
        '''
        get the public IP of a node name
        '''
        pass

    def get_unit_price(self, node):
        '''
        get the unit price of a node object (inferring from its name and from the cloud.yaml file)
        '''
        pass

    def get_instance_name(self, node):
        '''
        get the name of a node object (from the vendor API)
        '''
        pass

    def get_instances(self, filters = []):
        '''
        get the reference to the node (aka instance) object (from the vendor API)
        '''
        pass

    def get_running_cost(self, verbose=True):
        '''
        get the running cost of all the nodes (aka instances) (from the vendor API for running time and the unit cost)
        '''
        pass