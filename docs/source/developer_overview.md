# Developer Guide
<!-- From these links:
https://cloud-skyway.rcc.uchicago.edu/ -->

This documentation provides information for admins and developers to install and deploy Skyway on the login node of a HPC system. 

## Pre-requisites

* Python 3.x

## Installation

Installing Skyway is straightforward

``` py linenums="1"
  git clone https://github.com/ndtrung81/skyway
  cd skyway
  python3 -m venv skyway-env
  source skyway-env/bin/activate 
  pip install -r requirements.txt
  export SKYWAYROOT=/path/to/skyway
  export PATH=$SKYWAYROOT:$PATH
```

Line 1: Check out the GitHub repo

Lines 3-4: Create a virtual environment and activate it

Line 5: Install the required packages into the environment

Lines 6-7: Set the environment variable `SKYWAYROOT` and preppend it to `PATH`

## Configuration

Under the `SKYWAYROOT` folder, create a folder structure
```
  etc/
    - accounts/
        - rcc-aws.yaml
    - cloud.yaml
```

where the content of the file `cloud.yaml` includes the following:
``` py linenums="1"
aws:
    master_access_key_id: 'AKIA--------------'
    master_secret_access_key: '7bqh-------------'

    username: ec2-user
    key_name: rcc-skyway
    ami_id : ami-0b9c9831f6e1cc731
    io-node: 18.224.41.227
    grace_sec: 300

    node-types:
        t1:  { name: t2.micro,    price: 0.0116, cores: 1,  memgb: 1 }
        c1:  { name: c5.large,    price: 0.085,  cores: 1,  memgb: 3.5 }
        c8:  { name: c5.4xlarge,  price: 0.68,   cores: 8,  memgb: 32 }
        g1:  { name: p3.2xlarge,  price: 3.06,   cores: 4,  memgb: 61,  gpu: 1 }
```

This file lists all the supported cloud vendors such as `aws` and their node (VM) types.

The file `rcc-aws.yaml` lists all the users allowed to access the cloud account `rcc-aws`.


``` py linenums="1"
cloud: aws
group: rcc
account:
     access_key_id: 'AKIA53-------------'
    secret_access_key: '34oXS-------------'
    region: us-east-2
    security_group: ['sg-0a79--------------']
    protected_nodes: ['rcc-io']
    account_id: '3910-------------'
    role_name: rcc-skyway
    ami_id: 'ami-0fbfb390428631854'
    key_name: rcc-aws
nodes:
    c1:   4
    c36:  2
    g1:   2
users:
    user1: { budget: 100 } 
    user2: { budget: 150 }
```

The `skyway` Python package is light weight

```
skyway/
   - cloud/
      - aws.py
      - azure.py
      - gcp.py
      - oci.py
      - slurm.py
   - __init__.py
   - account.py
   - utils.py
docs/
examples/
```
