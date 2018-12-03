import boto3
import datetime
import numpy as np
import os
import math
import pytz
import threading
import time


####################################################################
# elb_name = 'ELB_NAME'
# elb_url = 'ELB_URL'
####################################################################

class AWSEnv(object):
    def __init__(self, as_group, elb, elb_url):
        self.as_client  = boto3.client('autoscaling')
        self.elb_client = boto3.client('elb')
        self.cw_client  = boto3.client('cloudwatch')
        self.as_group   = as_group
        self.devnull = open(os.devnull, 'w')
        self.elb_name = elb
        self.prev_utilization_sum = 0.0
        self.prev_network_packets_in_sum = 0
        self.prev_request_count_sum = 0
        self.prev_latency_sum = 0.0
        self.time_step = 300
        self.num_instances = 1

    def _set_num_instances(self, action, max):
        self.num_instances += action
        if self.num_instances < 1:
            self.num_instances = 1
        elif self.num_instances > max:
            self.num_instances = max
        
    def _scale_servers(self, num_instances):
        self.as_client.set_desired_capacity(AutoScalingGroupName=self.as_group, DesiredCapacity=num_instances, HonorCooldown=False)
    
    def instance_scale_up1():
        self._set_num_instances(1, max=5)
        self._scale_servers(self.num_instances)

    def instance_scale_up2():
        self._set_num_instances(2, max=5)
        self._scale_servers(self.num_instances)

    def instance_scale_down1():
        self._set_num_instances(-1, max=5)
        self._scale_servers(self.num_instances)

    def instance_scale_down2():
        self._set_num_instances(-2, max=5)
        self._scale_servers(self.num_instances)

    def neutron_lb_member_list_number():
        instance_ids = [x['InstanceId'] for x in self.elb_client.describe_instance_health(LoadBalancerName=self.elb_name)['InstanceStates']]
        if len(instance_ids) != self.num_instances:
            print('DEBUG: number of instances different from the instances in ASG: '+str(self.num_instances)+','+str(len(instance_ids)))
        return len(instance_ids)

     def _get_max_date(self, datapoints):
        dates = [x['Timestamp'] for x in datapoints]
        return max(dates)

    def _get_max_date_datapoint(self, datapoints, max_date):
        for datapoint in datapoints:
            if np.abs(datapoint['Timestamp'] - max_date) < datetime.timedelta(minutes=2):
                return datapoint
        return {'Average':0,'Sum':0}

    #Get Workload
    def ceilometer_connections_rate():
        end_time = datetime.datetime.utcnow().replace(tzinfo=pytz.UTC)
        start_time = end_time - datetime.timedelta(minutes=10)
        request_count_sum = 0
        cw_instance_count = 0 
        max_date = None

        cw_instance_count = len([x['InstanceId'] for x in self.elb_client.describe_instance_health(LoadBalancerName=self.elb_name)['InstanceStates']])

        request_count = self.cw_client.get_metric_statistics(Namespace='AWS/ELB',
                                                              MetricName='RequestCount',
                                                              Dimensions=[{'Name':'LoadBalancerName', 'Value':self.elb_name}],
                                                              Statistics=['Sum'],
                                                              Period=300,
                                                              StartTime=start_time, EndTime=end_time)
       
        if len(request_count['Datapoints']) > 0:
            if max_date == None:
                max_date = self._get_max_date(request_count['Datapoints'])
            request_count_sum = self._get_max_date_datapoint(request_count['Datapoints'], max_date)['Sum']
            self.prev_request_count_sum = request_count_sum
        else:
            request_count_sum = self.prev_request_count_sum
            print('DEBUG: Using previous request count value')
        return float(request_count_sum)/cw_instance_count
    

    


    
    