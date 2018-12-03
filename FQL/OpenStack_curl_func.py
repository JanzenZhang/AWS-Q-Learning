from __future__ import division

class pool_traffic_statistics_struct(object):
    def __init__(self):
        self.active_connections = -1
        self.bytes_in = -1
        self.bytes_out = -1
        self.total_connections = -1

class Active_VMs_struct(object):    
    def __init__(self):
        self.cnt = -1;
        self.ID = 'No ID'
        self.IP = 'No IP'

class catalog_list_struct(object):
    def __init__(self):
        self.heat = 'No url'
        self.nova = 'No url'
        self.neutron = 'No url'
        self.glance = 'No url'        
        self.ceilometer = 'No url'
        self.keystone = 'No url'

class config_struct(object):
    def __init__(self):
        self.lb_floating_IP = 'No IP'        
        self.OS_AUTH_URL = 'No url'
        self.scale_up1_url = 'No url'
        self.scale_down1_url = 'No url'
        self.scale_up2_url = 'No url'
        self.scale_down2_url = 'No url'        
        self.min_instances = -1
        self.max_instances = -1
        self.lb_pool_name = 'No name'
        self.lb_pool_id = 'No id'        
        self.url = []

config_param = []
# Active_VMs = []

json_payload = {
        "auth": {
            "tenantName": "demo",
            "passwordCredentials": {
                "username": "admin",
                "password": "mypassword"
            }
        }
    }


'''----------------------------------------------------------
    Read configure file inside of controller VM
-----------------------------------------------------------''' 
def read_local_config_file(file_name):
    config_param = config_struct()

    with open(file_name, 'r') as inF:
        for line in inF:
            if 'FloatingIP' in line:
                config_param.lb_floating_IP = inF.next().rstrip()
            elif "authentication " in line:
                config_param.OS_AUTH_URL = inF.next().rstrip()
            elif "scale up1" in line:
                config_param.scale_up1_url = inF.next().rstrip()
            elif "scale up2" in line:
                config_param.scale_up2_url = inF.next().rstrip()
            elif "scale down1" in line:
                config_param.scale_down1_url = inF.next().rstrip()
            elif "scale down2" in line:
                config_param.scale_down2_url = inF.next().rstrip()
            elif "Minimum" in line:
                config_param.min_instances = int(inF.next().rstrip())
            elif "Maximum" in line:
                config_param.max_instances = int(inF.next().rstrip())

    return config_param

'''----------------------------------------------------------
    Lunch 1 new VM
-----------------------------------------------------------''' 
def curl_XPOST_scale_up1():
    global config_param
    import requests
    import time
    
    url = config_param.scale_up1_url
    print 'wait for 1 new VM lunched...'        
    response = requests.post(url)
    if response.status_code == requests.codes.ok :
        print '1 new VM lunched...'            
    else :
        print('func curl_XPOST_scale_up1() : Something went wrong!')

'''----------------------------------------------------------
    Lunch 2 new VM
-----------------------------------------------------------''' 
def curl_XPOST_scale_up2():
    global config_param
    import requests
    import time
    
    url = config_param.scale_up2_url
    print 'wait for 2 new VM lunched...'        
    response = requests.post(url)
    if response.status_code == requests.codes.ok :
        print '2 new VM lunched...'            
    else :
        print('func curl_XPOST_scale_up2() : Something went wrong!')

'''----------------------------------------------------------
    Delete 1 VM
-----------------------------------------------------------''' 
def curl_XPOST_scale_down1():
    global config_param
    import requests
    import time
    
    url = config_param.scale_down1_url
    print 'wait for a VM deleted...'
    response = requests.post(url)    
    if response.status_code == requests.codes.ok :
        print 'a VM is deleted ...'        
    else :
        print('func curl_XPOST_scale_down1() : Something went wrong!')

'''----------------------------------------------------------
    Delete 2 VM
-----------------------------------------------------------''' 
def curl_XPOST_scale_down2():
    global config_param
    import requests
    import time
    
    url = config_param.scale_down2_url
    print 'wait for 2 VM deleted...'
    response = requests.post(url)
    if response.status_code == requests.codes.ok :
        print '2 VM is deleted ...'        
    else :
        print('func curl_XPOST_scale_down2() : Something went wrong!')

'''----------------------------------------------------------
    Gets an authentication token that permits access 
    to the OpenStack services REST API.
-----------------------------------------------------------'''
def get_token():
    global config_param
    global json_payload
    import requests
    import json

    token = []
    headers = {'content-type': 'application/json', 'accept': 'application/json'}
    url = config_param.OS_AUTH_URL + '/tokens'    
    response = requests.post(url, data=json.dumps(json_payload), headers=headers)

    if response.status_code == requests.codes.ok :
        res_str = response.json()
        token = res_str['access']['token']['id']
    else :
        print('func get_token() : Something went wrong!')

    if not config_param.url:
        config_param.url = catalog_list_struct()
        response_json = response.json()        
        for item in response_json['access']['serviceCatalog']:
            L = len(item['endpoints'][0]['adminURL'])
            if item['endpoints'][0]['adminURL'][L - 1] == '/':
                url = str(item['endpoints'][0]['adminURL'][0:L - 1])
            else:
                url = str(item['endpoints'][0]['adminURL'])

            if item['name'] == "nova":
                config_param.url.nova = url
            elif item['name'] == "heat":
                config_param.url.heat = url
            elif item['name'] == "neutron":
                config_param.url.neutron = url
            elif item['name'] == "glance":
                config_param.url.glance = url
            elif item['name'] == "ceilometer":
                config_param.url.ceilometer = url
            elif item['name'] == "keystone":
                config_param.url.keystone = url
        
        [config_param.lb_pool_name, config_param.lb_pool_id] = get_lb_pool_name_id()

    return token

'''----------------------------------------------------------    
    To obtain a list of pool members, 
    use the Neutron lb-member-list command as follows:
                Syntax: lb-member-list [--pool-id=<POOL ID>]
    The returned list of pool members includes member details,
    such as the ID, address, protocol port, admin state, and status.
    Use --pool-id to return pool members in the specified pool only.
-----------------------------------------------------------''' 
def neutron_lb_member_list_number():
    global config_param
    global json_payload
    import requests
    import json

    token = get_token()
    headers = {'User-Agent': 'python-neutronclient', 'Accept': 'application/json', 'X-Auth-Token':token}
    url = config_param.url.neutron + '/v2.0/lb/members.json'
    response = requests.get(url, params=json.dumps(json_payload), headers=headers)

    Active_VMs = Active_VMs_struct()
    if response.status_code == requests.codes.ok :
        res_str = response.json()
        Active_VMs.ID = []
        Active_VMs.IP = []

        for item in res_str['members']:                        
            if item['weight'] == 1:
                Active_VMs.ID.append(str(item['id']))
                Active_VMs.IP.append(str(item['address']))            

        Active_VMs.cnt = len(Active_VMs.ID)
    else:
        print('func neutron_lb_member_list_number : Something went wrong!')

    return Active_VMs 

'''----------------------------------------------------------   
    To obtain a list of configured load balancer pools, 
    use the Neutron lb-pool-list as follows:
                Syntax: lb-pool-list
    The returned list includes details of pools in the 
    running tenant, such as ID, name, load balancing method,
    protocol, admin state, and status.
-----------------------------------------------------------'''
def get_lb_pool_name_id():
    global config_param
    global json_payload
    import requests
    import json

    token = get_token()
    headers = {'User-Agent': 'python-neutronclient', 'Accept': 'application/json', 'X-Auth-Token':token}
    url = config_param.url.neutron + '/v2.0/lb/pools.json'
    response = requests.get(url, params=json.dumps(json_payload), headers=headers)

    lb_pool_name = ''
    lb_pool_id = ''
    if response.status_code == requests.codes.ok :
        res_str = response.json()
        lb_pool_id = res_str['pools'][0]['id']
        lb_pool_name = res_str['pools'][0]['name']
    else:
        print('func get_lb_pool_name_id : Something went wrong!')

    return [lb_pool_name, lb_pool_id]

'''
---------------------------------------
        ceilometer_connections_rate
---------------------------------------        
'''
def ceilometer_connections_rate():
    global config_param
    global json_payload
    import requests
    import pprint
    import json

    token = get_token()    
    headers = {'User-Agent': 'python-ceilometerclient', 'X-Auth-Token':token}
    url = config_param.url.ceilometer + '/v2/meters/network.services.lb.total.connections.rate?limit=3'
    response = requests.get(url, headers=headers)
   
    rate_value = 0
    if response.status_code == requests.codes.ok:
        res_str = response.json()
        avg_rate = 0
        for item in res_str:            
            if item['counter_volume'] < 40:
                avg_rate = avg_rate + item['counter_volume']
            else:
                avg_rate = avg_rate + 40            
        rate_value = avg_rate/3.0
    else:        
        print('func ceilometer_connections_rate : Something went wrong!')        
    
    return rate_value

'''----------------------------------------------------------
    Display Configuration parameters
-----------------------------------------------------------''' 
def show_config_param():
    global config_param
    print 'show_config_params'
    print '\tNeutron FloatingIP:  ' + config_param.lb_floating_IP
    print '\tMaximum number of instances:  ' + str(config_param.max_instances)
    print '\tMinimum number of instances:  ' + str(config_param.min_instances)
    print '\theat:  ' + config_param.url.heat
    print '\tnova:  ' + config_param.url.nova
    print '\tneutron:  ' + config_param.url.neutron
    print '\tglance:  ' + config_param.url.glance
    print '\tceilometer:  ' + config_param.url.ceilometer
    print '\tkeystone:  ' + config_param.url.keystone
    print '\tlb_pool_name:  ' + config_param.lb_pool_name
    print '\tlb_pool_id:  ' + config_param.lb_pool_id
    print '-----------------------------------'
    
'''----------------------------------------------------------   
    initialization configuration parameters
-----------------------------------------------------------'''
def init_config_param():    
    global config_param
    config_param = read_local_config_file('config_param')    
    token = get_token()  # should be here to initi config_param.url
    show_config_param()
        
