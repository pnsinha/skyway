# Copyright (c) 2019-2024 The University of Chicago.
# Part of skyway, released under the BSD 3-Clause License.

# Maintainer: Yuxing Peng, Trung Nguyen

import os
from .. import utils

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
        pass

    def create_nodes(self, node_type: str, node_names = []):
        pass

    def connect_node(self, node_name):
        pass

    def destroy_node(self, node_name):
        pass

    def check_valid_user(self, user_name, verbose=False):
        pass

    def get_node_types(self):
        pass

    def get_running_nodes(self, verbose=False):
        pass

    def get_host_ip(self, node_name):
        pass