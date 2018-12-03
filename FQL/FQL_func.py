from __future__ import division

FIS = []
LAMBDA = 0.8;  # discount factor
NS = -1  # number of states
NA = -1  # number of actions
DESIRED_RT = 40 # response time SLO in millisecond, SLA(index), index is the index for specific SLO such as rt
W = [1, 1]  # weight values used in the reward function
ARCHIVEFOLDER = 'myarchive'  # name of the folder used for archiving unused rule bases
FISFILENAME = 'robust2scalesg.fis'  # name of the current rule base useing for reasoning
# name of rule base transfered from design-time
FISTEMPFILENAME = 'robust2scalesg9_hamid.fis'

'''----------------------------------------------------------   
    read_FIS
-----------------------------------------------------------'''
def read_FIS():
    import fuzzy_logic_func
    global FIS , NS , NA , FISTEMPFILENAME
    FIS = []
    FIS = fuzzy_logic_func.readfis(FISTEMPFILENAME)
    NS = len(FIS.rule)
    NA = len(FIS.output[0].mf)

'''----------------------------------------------------------   
    approximate_q_function : This function approximate the Q function from the current q-values and the degree of truth of the rules
-----------------------------------------------------------'''
def approximate_q_function(Q, current_state, ais):
    import fuzzy_logic_func
    global FIS, NS 
    # determine the number of antecedents of the rules in the knowledge base of the fuzzy logic controller
    number_of_input = len(FIS.input)
    
    # initialize the activation function or degree of truth of the rules in the
    # knowledge base, again number of rules is equal to number of states in MDP
    alpha = [1 for _ in range(NS)]
    
    # initialize q-value
    q = 0
    
    for i in range(NS):  # number of rules
        for j in range(number_of_input) :  # number of antecedents
            # if the antecedent MF exists in the associated rule
            if FIS.rule[i].antecedent[j] > 0:
                # calculate the activation function
                alpha[i] = alpha[i] * fuzzy_logic_func.evalmf(current_state[j],
                                             FIS.input[j].mf[FIS.rule[i].antecedent[j]].params,
                                             FIS.input[j].mf[FIS.rule[i].antecedent[j]].type)[0]        
        # calculate the q-value
        q = q + alpha[i] * Q[i][ais[i]];
    
    return q
    
'''----------------------------------------------------------   
    error_signal_calculator_Q_learning
-----------------------------------------------------------'''    
def error_signal_calculator_Q_learning(Q, current_state, next_state, ais):
    global LAMBDA
    
    delta_q = reward_calculator(current_state, next_state) \
                + LAMBDA * value_function_calculator(Q, next_state) \
                - approximate_q_function(Q, current_state, ais)
    
    return delta_q
    
'''----------------------------------------------------------   
    error_signal_calculator_SARSA
-----------------------------------------------------------'''      
def error_signal_calculator_SARSA(Q, current_state, next_state, ais):
    global LAMBDA
    
    delta_q = reward_calculator(current_state, next_state) \
                + LAMBDA * approximate_q_function(Q, next_state, ais) \
                - approximate_q_function(Q, current_state, ais)
    
    return delta_q

'''----------------------------------------------------------   
    fuzzy_Q_learn : This function implements Fuzzy Q-Learning
-----------------------------------------------------------'''
def fuzzy_Q_learn(Q, current_state, next_state, ais):    
    # initializations
    global FIS, NS, NA
    import fuzzy_logic_func

    
    # determine the number of antecedents of the rules in the knowledge base of the fuzzy logic controller
    number_of_input = len(FIS.input)
    
    # initialize the activation function or degree of truth of the rules in the knowledge base, again number of rules is equal to number of states in MDP
    alpha = [1 for _ in range(NS)]
    
    # initialize the matrix that maintain the number of updates for each q-value corresponding to Q lookup table
    LEARN = [[0 for _ in range(NA)] for _ in range(NS)]

    # constant learning rate
    learn_rate = 0.1
    
    # Value iteration update rule (learning process)
    for i in range(NS):
        for j in range(number_of_input):
            # if the antecedent MF exists in the associated rule
            if FIS.rule[i].antecedent[j] > 0:
                # calculate the activation function
                alpha[i] = alpha[i] * fuzzy_logic_func.evalmf(current_state[j],
                                             FIS.input[j].mf[FIS.rule[i].antecedent[j]].params,
                                             FIS.input[j].mf[FIS.rule[i].antecedent[j]].type)[0]
                
        
        ai = ais[i]  # select an action (for each activated rule!)
        if (alpha[i] != 0) :
            # update q-values by an ordinary gradient descent method
            Q[i][ai] = Q[i][ai] + learn_rate * error_signal_calculator_Q_learning(Q, current_state, next_state, ais) * alpha[i];
            # update the state for maintaining the number of updates of the q-values
            LEARN[i][ai] = LEARN[i][ai] + 1.0
            
    return [Q, LEARN]
    
'''----------------------------------------------------------   
    fuzzy_action_calculator
-----------------------------------------------------------'''    
def fuzzy_action_calculator(Q, ststem_state, epsilon):
    import fuzzy_logic_func
    global FIS, NS
    
    # determine the number of antecedents of the rules in the knowledge base of
    # the fuzzy logic controller
    number_of_input = len(FIS.input)
    
    # initialize the activation function or degree of truth of the rules in the
    # knowledge base, again number of rules is equal to number of states in MDP
    alpha = [1 for _ in range(NS)]
    
    # initialize vector that stores ai (action selected for each activated rul)
    ais = [1 for _ in range(NS)]
    
    # initialize output action to execute
    action = 0
        
    for i in range(NS):  # number of rules
        for j in range(number_of_input) :  # number of antecedents
            # if the antecedent MF exists in the associated rule
            if FIS.rule[i].antecedent[j] > 0:
                # calculate the activation function
                alpha[i] = alpha[i] * fuzzy_logic_func.evalmf(ststem_state[j],
                                             FIS.input[j].mf[FIS.rule[i].antecedent[j]].params,
                                             FIS.input[j].mf[FIS.rule[i].antecedent[j]].type)[0]
    
        
        ais[i] = fuzzy_action_selector(Q, i, epsilon)
        #  calculate the action
        action = action + alpha[i] * FIS.output[0].mf[ais[i]].params[0]
    
    # fit ScalingDecision in range [2,-2]
    if action > 2:
        action = 2
    elif action < -2:
        action = -2

    return [round(action), ais]

'''----------------------------------------------------------   
    fuzzy_action_selector : returns the next selected actions using epsilon-greedy policy
-----------------------------------------------------------'''  
def fuzzy_action_selector(Q, rule_number, epsilon):
    global NA
    import random
    from math import floor
    
    # Random float x, 0.0 <= x < 1.0
    ran = random.random()
    
    #epsilon = 1.0
    # setting the exploration probability
    exploitation_probability = 1 - epsilon
    
    if ran < exploitation_probability :
        # exploit
        maxQfactor = max(Q[rule_number])
        index = Q[rule_number].index(maxQfactor)
        action = index
    else:
        # explore
        action = floor(random.random() * NA)
    
    return int(action)

'''----------------------------------------------------------   
    init_knowledge_base : initializing the rule base
-----------------------------------------------------------''' 
def init_knowledge_base():
    global FIS, ARCHIVEFOLDER, FISFILENAME
    import fuzzy_logic_func
    
    import os    
    # create archive folder
    if not os.path.exists(ARCHIVEFOLDER):
        os.makedirs(ARCHIVEFOLDER)
    
    # create the current rule base using for reasoning
    read_FIS()

'''----------------------------------------------------------   
    initq : initialize the q-values in the look up table
-----------------------------------------------------------''' 
def initq():
    global NA, NS

    Q = [[0 for _ in range(NA)] for _ in range(NS)]
    
    # return Q table
    return Q
    
'''----------------------------------------------------------   
    reward_calculator
-----------------------------------------------------------'''     
def reward_calculator(current_state, next_state):
    global DESIRED_RT, W
    MAX_VM = 5
        
    if next_state[1] < DESIRED_RT:
        slaFactor = 0
    else:
        if next_state[1] > 2 * DESIRED_RT:
            slaFactor = 1
        else:
            slaFactor = (next_state[1] - DESIRED_RT) / DESIRED_RT
        
    Ut_1 = W[0] * (1 - next_state[2] / MAX_VM) + W[1] * (1 - slaFactor)

    if current_state[1] < DESIRED_RT:
        slaFactor = 0
    else:
        if current_state[1] > 2 * DESIRED_RT:
            slaFactor = 1
        else:
            slaFactor = (current_state[1] - DESIRED_RT) / DESIRED_RT
            
    Ut = W[0] * (1 - current_state[2] / MAX_VM) + W[1] * (1 - slaFactor)
    
    reward = Ut_1 - Ut;

    return reward

'''----------------------------------------------------------   
    update_fis : updates the rule base of the fuzzy logic controller according to the Q-values
-----------------------------------------------------------''' 
def update_fis(Q):
    global FIS, NS
    # initialize FIS
    fis = FIS
    for rule_number in xrange(NS):
        # choose the value and index of the optimum Q
        maxQfactor = max(Q[rule_number])
        index = Q[rule_number].index(maxQfactor)
        
        fis.rule[rule_number].consequent[0] = index

    return fis

'''----------------------------------------------------------   
    update_knowledge_base
-----------------------------------------------------------''' 
def update_knowledge_base(Q):
    global ARCHIVEFOLDER, FISFILENAME
    from shutil import copyfile
    from time import gmtime, strftime
    import fuzzy_logic_func
    
    # update the rule base
    fis = update_fis(Q)
    
    # archive the old rule base of FLC in place
    cp_add = ARCHIVEFOLDER + "/" + FISFILENAME.replace(".fis", strftime("-%Y-%m-%d-%H-%M-%S", gmtime()) + ".fis")
    copyfile(FISFILENAME, cp_add)
    
    # replace the rule base with the updated version
    fuzzy_logic_func.writefis(fis, FISFILENAME)

'''----------------------------------------------------------   
    value_function_calculator
-----------------------------------------------------------''' 
def value_function_calculator(Q, next_state):    
    global FIS, NS
    import fuzzy_logic_func
    # determine the number of antecedents of the rules in the knowledge base of
    # the fuzzy logic controller
    number_of_input = len(FIS.input)
    
    # initialize the activation function or degree of truth of the rules in the
    # knowledge base, again number of rules is equal to number of states in MDP
    alpha = [1 for _ in range(NS)]
    
    # initialize q-value
    v = 0;
    
    for i in range(NS):  # number of rules
        for j in range(number_of_input) :  # number of antecedents
            # if the antecedent MF exists in the associated rule
            if FIS.rule[i].antecedent[j] > 0:
                # calculate the activation function
                alpha[i] = alpha[i] * fuzzy_logic_func.evalmf(next_state[j],
                                             FIS.input[j].mf[FIS.rule[i].antecedent[j]].params,
                                             FIS.input[j].mf[FIS.rule[i].antecedent[j]].type)[0]
                        
        # note that max/min should be in accordance with reward/cost as reinforcement signal
        maxQfactor = max(Q[i])
        
        # calculate the value of the new state
        v = v + alpha[i] * maxQfactor;
    
    return v

'''----------------------------------------------------------   
    ScaleData
-----------------------------------------------------------''' 
def ScaleData(data_in, min_value, max_value, range_value):
    data_out = 0
    
    if data_in <= range_value:
        data_out = data_in
        data_out = (data_out / range_value) * (max_value - min_value)
        data_out = data_out + min_value
    else:
        data_out = max_value
    
    return data_out  

