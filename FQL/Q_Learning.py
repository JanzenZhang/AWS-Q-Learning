from __future__ import division
from aws_util import AWSEnv


as_group  = 'AUTOSCALING_GROUP'
elb_name  = 'ELB_NAME'
elb_url   = 'ELB_URL'
epsilon = -1
class siege_log_struct(object):
    def __init__(self):
        self.succ = -1.0
        self.Response_time = -1.0
'''----------------------------------------------------------
    read_siege_log
-----------------------------------------------------------''' 
def read_siege_log(file_name):
    siege_log = siege_log_struct()

    f = open(file_name)
    lines=f.readlines()
    tmp_str = lines[1].rstrip().split(',')
    Resp_Time = float(tmp_str[4])
    OKAY = float(tmp_str[8])
    Failed = float(tmp_str[9])
    siege_log.succ = (OKAY / (OKAY + Failed))*100.0
    siege_log.Response_time = Resp_Time
    f.close()
    return siege_log

'''----------------------------------------------------------
    get_system_status
-----------------------------------------------------------''' 
def get_system_status(time_sleep,test_time_period,test_concurrent_number):
    global epsilon
   # import OpenStack_curl_func
    import FQL_func
    import subprocess
    import os
    import time

    time.sleep(time_sleep)

    siege_log_file_name = "siege_output.log"
    # calcualte response time based on siege
    if os.path.isfile(siege_log_file_name):
        os.remove(siege_log_file_name)    

    bashCommand = "siege -q -d3 -c%d -t%dS  %s  --log=%s " %(test_concurrent_number,test_time_period,elb_url,siege_log_file_name)
    subprocess.check_output(['bash','-c', bashCommand])
    siege_log = read_siege_log(siege_log_file_name)

    # calcualte VMs number
    #curr_Active_VMs = OpenStack_curl_func.neutron_lb_member_list_number()
    #VMs_number = curr_Active_VMs.cnt
    VMs_number = env.neutron_lb_member_list_number()

    # calcualte workload
    # active_connections = OpenStack_curl_func.ceilometer_connections_rate()
    active_connections = env.ceilometer_connections_rate()
    workload = FQL_func.ScaleData(active_connections, 0, 100, 40)

    # calcualte response Time
    avg_response_Time = siege_log.Response_time
    response_Time = FQL_func.ScaleData(avg_response_Time, 0, 100, 30)
    
    # system_state = [workload_number, response_Time, VMs_number]
    system_state = [ workload, response_Time , VMs_number]

    # return system state
    return system_state

'''--------------------------------------------------------
      main 
-----------------------------------------------------------''' 
def main():

    global epsilon
    global as_group
    global elb_name
    global elb_url
    import random
    import FQL_func
    import os
    




    
    #OpenStack_curl_func.init_config_param()
    global env
    env = AWSEnv(as_group=as_group, elb=elb_name, elb_url=elb_url)


    #Active_VMs = OpenStack_curl_func.neutron_lb_member_list_number()
    Active_VMs = env.neutron_lb_member_list_number()

    MAX_VMs_number = 5
    MIN_VMs_number = 1
    
    # initialize parameters
    VMs_number = MIN_VMs_number
    system_state = []
    current_state = []
    currentAction = []
    epsilon = 1.0
    LEARN = []
    epoch = 0
    canUpdate = False
    currentais = []
    Q = []
    
    # initializing knowledge base
    FQL_func.init_knowledge_base()
    
    # initialize Q table    
    if not Q:
        Q = FQL_func.initq()    

    test_concurrent_number = 5
    test_time_period = 20
    time_sleep = 10

    
    current_state = get_system_status(time_sleep,test_time_period,test_concurrent_number)


    exit_flag = 0
    while exit_flag == 0:        
        
        # read FIS
        FQL_func.read_FIS()
            
        if (os.path.isfile('stop.txt')):
            break;        

        # choos action a from state s using policy e-greedy
        [ScalingDecision, ais] = FQL_func.fuzzy_action_calculator(Q, current_state, epsilon)

        
        can_be_applied = False
        # calcualte VMs number
        # curr_Active_VMs = OpenStack_curl_func.neutron_lb_member_list_number()
        # VMs_number = curr_Active_VMs.cnt
        VMs_number = env.neutron_lb_member_list_number()
        print ' curr_Active_VMs = ' + str(VMs_number)

        # check to see if the chosen action could be applied in system or not
        if MIN_VMs_number <= ScalingDecision + VMs_number <= MAX_VMs_number and ScalingDecision != 0:
            can_be_applied = True

        # take action a, observe new state s' and reward r
        if can_be_applied:
            # apply ScalingDecision
            VMs_number = VMs_number + ScalingDecision
            
            if ScalingDecision == 1:
                #OpenStack_curl_func.curl_XPOST_scale_up1()
                env.instance_scale_up1()
            elif ScalingDecision == 2:
                env.instance_scale_up2()
            elif ScalingDecision == -1:
                env.instance_scale_down1()
            elif ScalingDecision == -2:
                env.instance_scale_down2()
            
            UP_DOWN = []
            if ScalingDecision > 0:
                UP_DOWN = ' ++++ UP ++++ '
            else:
                UP_DOWN = ' --- DOWN --- '           
            print 'ScalingDecision = ' + str(ScalingDecision) + UP_DOWN + ' is applied . . new VMs number = ' + str(VMs_number)
            
            currentAction = ScalingDecision
            currentais = ais

        else: # can_be_applied == False
            error_str = 'ScalingDecision cloud not be applied because '
            if ScalingDecision == 0:
                error_str = error_str + 'ScalingDecision == 0'
            else:
                error_str = error_str + ' out of range  ' + str(MIN_VMs_number) + ' <= ' \
                    + str(ScalingDecision + VMs_number) + ' <= ' + str(MAX_VMs_number)                
            print error_str 


        next_state = get_system_status(time_sleep,test_time_period,test_concurrent_number)


        # learn, i.e., update q-values if the chosen action was applied 
        if can_be_applied:

            # if a change is enacted to the environment and if the change is the action that has been issued previously, then the reward has been received

            if next_state[2] != current_state[2] and currentAction == next_state[2] - current_state[2]:
                # update Q table
                [Q, currentLEARN] = FQL_func.fuzzy_Q_learn(Q, current_state, next_state, currentais)
                # add current state to the accumulated one or initialize for the first time
                if not LEARN:
                    LEARN = currentLEARN
                else:
                    for row in range(len(LEARN)):
                        for col in range(len(LEARN[0])):
                            LEARN[row][col] = LEARN[row][col] + currentLEARN[row][col]
                
                # update learning cycle number
                epoch = epoch + 1
                canUpdate = True
        
        # exploration/exploitation strategy enforcer: after enough epoches of learning, 
        # change exploration rate and update knowledge base of the controller, 
        if epoch % 30 == 0 and canUpdate :
            FQL_func.update_knowledge_base(Q)

            # in each learning epoch decrease epsilon until it reaches a predetermined balance 
            # between exploration and exploitation, here 0.3
            if epsilon >= 0.4 :
                epsilon = epsilon - 0.1
            
            canUpdate = False
                

        system_state = current_state
        
    # end of for step_number    

if __name__ == '__main__':
    main()


