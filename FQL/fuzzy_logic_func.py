from __future__ import division

class FIS_structure(object):
        def __init__(self, name=None, type=None, version=None, andMethod=None, orMethod=None, impMethod=None,
                     aggMethod=None, defuzzMethod=None, input=None, output=None, rule=None):
            self.name = name
            self.type = type
            self.version = version
            self.andMethod = andMethod
            self.orMethod = orMethod
            self.impMethod = impMethod
            self.aggMethod = aggMethod
            self.defuzzMethod = defuzzMethod
            self.input = input
            self.output = output
            self.rule = rule
            
class FIS_input_output_structure(object):
    def __init__(self, name=None, range=None, mf=None):
        self.name = name
        self.range = range
        self.mf = mf

class membership_structure(object):
    def __init__(self, name=None, type=None, params=None):
        self.name = name
        self.type = type
        self.params = params 

class rule_structure(object):
    def __init__(self, antecedent=None, consequent=None, weight=None, connection=None):
        self.antecedent = antecedent
        self.consequent = consequent
        self.weight = weight
        self.connection = connection

             
def get_line (fid, line_num):
    fid.seek(0)
    for _ in xrange(line_num):
        line = fid.readline(); 
    return [line, line_num + 1]
        
'''----------------------------------------------------------
    Read the [System] section of the input file. Using the
    strings read from the input file, create a new FIS.
-----------------------------------------------------------'''    
def init_fis_struct(fid):
    import re
    # Read the [System] section.
    line_num = 1;
    [_, line_num] = get_line (fid, line_num)    
    [line, line_num] = get_line (fid, line_num)
    fis_name = re.search('Name=\'(.*)\'', line).group(1)    
    [line, line_num] = get_line (fid, line_num)
    fis_type = re.search('Type=\'(.*)\'', line).group(1)
    [line, line_num] = get_line (fid, line_num)
    fis_version = float(re.search('Version=(.*)', line).group(1))
    [line, line_num] = get_line (fid, line_num)
    num_inputs = int(re.search('NumInputs=(.*)', line).group(1))
    [line, line_num] = get_line (fid, line_num)
    num_outputs = int(re.search('NumOutputs=(.*)', line).group(1))
    [line, line_num] = get_line (fid, line_num)
    num_rules = int(re.search('NumRules=(.*)', line).group(1))
    [line, line_num] = get_line (fid, line_num)
    and_method = re.search('AndMethod=\'(.*)\'', line).group(1)
    [line, line_num] = get_line (fid, line_num)
    or_method = re.search('OrMethod=\'(.*)\'', line).group(1)    
    [line, line_num] = get_line (fid, line_num)
    imp_method = re.search('ImpMethod=\'(.*)\'', line).group(1)
    [line, line_num] = get_line (fid, line_num)
    agg_method = re.search('AggMethod=\'(.*)\'', line).group(1)
    [line, line_num] = get_line (fid, line_num)
    defuzz_method = re.search('DefuzzMethod=\'(.*)\'', line).group(1) 
       
    # Create a new FIS structure using the strings read from the
    # input file.      
    fis = FIS_structure(fis_name, fis_type, fis_version, and_method, or_method, imp_method, agg_method, defuzz_method, [], [], [])
    
    return [fis, num_inputs, num_outputs, num_rules, line_num]

'''----------------------------------------------------------
    Read the next [Input<i>] or [Output<i>] section of the
    input file. Using the info read from the input file, create
    a new FIS input or output structure.
-----------------------------------------------------------'''        
def get_next_fis_io (fid, line_num, i, in_or_out):
    import re
    # Read [Input<i>] or [Output<i>] section from file.
    [_, line_num] = get_line (fid, line_num)

    [line, line_num] = get_line (fid, line_num)
    
    var_name = re.search('Name=\'(.*)\'', line).group(1)
    
    [line, line_num] = get_line (fid, line_num)
    [range_low_str, range_high_str] = re.findall('[+-]?\d+', line)    
    range_low = int(range_low_str)
    range_high = int(range_high_str)
        
    [line, line_num] = get_line (fid, line_num)
    num_mfs = int(re.search('NumMFs=(.*)', line).group(1))
    
    # Create a new FIS input or output structure.
    next_fis_io = FIS_input_output_structure(var_name, [range_low, range_high], [])
    
    return [next_fis_io, num_mfs, line_num]

'''----------------------------------------------------------
    Read information specifying the jth membership function for
    Input<i> or Output<i> (if in_or_out is 'input' or 'output',
    respectively) from the input file. Create a new membership
    function structure using the info read.
-----------------------------------------------------------'''     
def get_next_mf (fid, line_num, i, j, in_or_out):
    import re
    # Read membership function info for the new FIS input or output
    # from file.
    [line, line_num] = get_line (fid, line_num)
    tmp = line.rstrip().replace(",", "").replace(":", "").replace(":", "").split('\'')
    
    mf_name = tmp[1]
    mf_type = tmp[3]
    mf_params = map(int, re.findall('[+-]?\d+', tmp[4]))
    
    # Create a new membership function structure.
    next_mf = membership_structure(mf_name, mf_type, mf_params)
    
    return [next_mf, line_num]

'''----------------------------------------------------------
    For each FIS input, read the [Input<number>] section from
    file. Add each new input and its membership functions to
    the FIS structure.
-----------------------------------------------------------'''     
def read_fis_inputs(fid, fis, num_inputs, line_num):    
    for i in xrange(num_inputs):
        line_num = line_num + 1
        [next_fis_input, num_mfs, line_num] = get_next_fis_io (fid, line_num, i, 'input')
        fis.input.append(next_fis_input)
        
        # Read membership function info for the current FIS input from
        # file. Add each new membership function to the FIS structure
        for j in xrange(num_mfs):
            [next_mf, line_num] = get_next_mf (fid, line_num, i, j, 'input')
            fis.input[i].mf.append(next_mf)
        
    return [fis , line_num]
 
'''----------------------------------------------------------
    For each FIS output, read the [Output<number>] section from
    file. Add each new output and its membership functions to
    the FIS structure.
-----------------------------------------------------------''' 
def read_fis_outputs(fid, fis, num_outputs, line_num):    
    for i in xrange(num_outputs):
        line_num = line_num + 1
        [next_fis_output, num_mfs, line_num] = get_next_fis_io (fid, line_num, i, 'output')
        fis.output.append(next_fis_output)
        
        # Read membership function info for the current FIS output from
        # file. Add each new membership function to the FIS struct.
        for j in xrange(num_mfs):
            [next_mf, line_num] = get_next_mf (fid, line_num, i, j, 'input')
            fis.output[i].mf.append(next_mf)
        
    return [fis , line_num]

'''----------------------------------------------------------
    Read the next rule from the input file. Create a struct for
    the new rule.
-----------------------------------------------------------''' 
def get_next_rule (fid, line_num, num_inputs, num_outputs):
    import re
    [line, line_num] = get_line (fid, line_num)
    tmp = map(int, re.findall('[+-]?\d+', line))
    
    # Read antecedent
    antecedent = [i - 1 for i in tmp[0:2]]
    # Read consequent   
    consequent = [i - 1 for i in tmp[2:3]] 
    # Read weight
    weight = tmp[3]
    # Read connection
    connection = tmp[4]
    
    # Create a new rule struct.
    next_rule = rule_structure(antecedent, consequent, weight, connection)
    return [next_rule, line_num]
    
'''----------------------------------------------------------
    Read the [Rules] section from file, and add the rules to
    the new rule.
-----------------------------------------------------------''' 
def read_rules (fid, fis, num_inputs, num_outputs, num_rules, line_num):
    [_, line_num] = get_line (fid, line_num)
    for _ in xrange(num_rules):
        [next_rule, line_num] = get_next_rule (fid, line_num, num_inputs, num_outputs)
        fis.rule.append(next_rule)
    
    return fis

'''----------------------------------------------------------
    Open the input file specified by the filename.
    Return an fid
-----------------------------------------------------------''' 
def open_input_file (filename):
    # Open input file.
    fid = open(filename, 'r')
    return fid

'''----------------------------------------------------------
    Read the information in an FIS file, and using this
    information, create and return an FIS structure    
-----------------------------------------------------------'''         
def readfis(filename):
    
    # Open the input file
    fid = open_input_file (filename)
     
    # Read the [System], [Input<number>], [Output<number>], and [Rules]
    # sections of the input file.    
    [fis, num_inputs, num_outputs, num_rules, line_num] = init_fis_struct (fid)
    
    [fis, line_num] = read_fis_inputs (fid, fis, num_inputs, line_num)
    [fis, line_num] = read_fis_outputs (fid, fis, num_outputs, line_num)
    
    fis = read_rules (fid, fis, num_inputs, num_outputs, num_rules, line_num + 1)
    
    # Close the input file
    fid.close()
    
    return fis

'''----------------------------------------------------------
    Calculate and return the y values of the membership function on
    the domain x. First, get the value of the membership function
    without correcting for the hedge and not_flag. Then, for non-linear
    functions, adjust the function values for non-zero hedge and
     not_flag
-----------------------------------------------------------'''
def evalmf (x, params, mf_type, hedge=0, not_flag=False):
       
    if mf_type == 'constant':
        y = eval_constant (x, params)
        if not_flag:
            for i in range(len(y)):
                y[i] = 1 - y[i]
                                
    elif mf_type == 'linear':
        y = eval_linear (x, params)
            
    elif mf_type == 'trimf':
        y = trimf(x, params)        
        if hedge != 0:
            for i in range(len(y)):
                y[i] = y[i] * y[i]
        if not_flag:
            for i in range(len(y)):
                y[i] = 1 - y[i]
                        
    elif mf_type == 'trapmf':
        y = trapmf(x, params)
        if hedge != 0:
            for i in range(len(y)):
                y[i] = y[i] * y[i]
        if not_flag:
            for i in range(len(y)):
                y[i] = 1 - y[i]
    
    return y

'''----------------------------------------------------------
    For the parameters [a ... c]), return the y-values
    corresponding to the linear function y = a*x + c, where x
    takes on the the x-values in the domain.
-----------------------------------------------------------'''
def eval_linear (x, params):
    if len(params) == 1:
        a = 0
        c = params
    else:
        a = params[0]
        c = params[len(params) - 1]
    
    y = [[0 for _ in range(len(x))] for _ in range(len(x))]
    for i in range(len(x)):
        y[i] = a * x[i] + c
        
    return y

'''----------------------------------------------------------
    Return the y-values corresponding to the x-values in
    the domain for the constant function specified by the
    parameter c.
-----------------------------------------------------------'''
def eval_constant (x, c):    
    y = [0 for i in range(len(x))]
    delta = x[1] - x[0];
    for i in range(len(x)):
        y[i] = (abs(c[0] - x[i]) < delta) * 1
        
    return y

'''----------------------------------------------------------
    For a given domain x and parameters params (or [a b c d]),
    return the corresponding y values for the trapezoidal membership
    function. The argument x must be a real number or a non-empty
    vector of strictly increasing real numbers, and parameters a, b,
    c, and d must satisfy the inequalities: a < b <= c < d
    None of the parameters a, b, c and d are required to be in the
    domain x. The minimum and maximum values of the trapezoid are
    assumed to be 0 and 1.
    The parameters [a b c d] correspond to the x values of the 
    corners of the trapezoid:
                                1-|      --------
                                  |     /        \
                                  |    /          \
                                  |   /            \
                                0-----------------------
                                     a   b      c   d    
-----------------------------------------------------------'''
def trapmf(x, params):
    # Calculate and return the y values of the trapezoid on the domain x.
    a = params[0]
    b = params[1]
    c = params[2]
    d = params[3]
    
    b_minus_a = b - a
    d_minus_c = d - c
    
    # if the x input is not a list
    if (type(x) is not list):
        x = [x]
            
    y = [0 for _ in range(len(x))]
    for i in range(len(x)):
        try:
            p1 = (x[i] - a) / b_minus_a
        except ZeroDivisionError:
            p1 = (x[i] - a) * float("inf")

        try:
            p2 = (d - x[i]) / d_minus_c
        except ZeroDivisionError:
            p2 = (d - x[i]) * float("inf")

        y[i] = max (0, min (min (1, p1), p2))
        
    return y

'''----------------------------------------------------------
    The argument x must be a real number or a non-empty vector of
    strictly increasing real numbers, and parameters a, b, and c 
    must be real numbers that satisfy : a < b < c. 
    None of the parameters a, b, and c are required to be in the
    domain x. The minimum and maximum values of the triangle are
    assumed to be 0 and 1.
    The parameters [a b c] correspond to the x values of the
    vertices of the triangle:
                                1-|         /\
                                  |        /  \
                                  |       /    \
                                  |      /      \
                                0-----------------------
                                         a   b   c
-----------------------------------------------------------'''    
def trimf(x, params):    
    # Calculate and return the y values of the triangle on the domain x.
    a = params[0]
    b = params[1]
    c = params[2]
    
    b_minus_a = b - a
    c_minus_b = c - b
    
    # if the x input is not a list
    if (type(x) is not list):
        x = [x]
        
    y = [0 for i in range(len(x))]
    for i in range(len(x)):
        try:
            p1 = (x[i] - a) / b_minus_a
        except ZeroDivisionError:
            p1 = (x[i] - a) * float("inf")  
        try:
            p2 = (c - x[i]) / c_minus_b
        except ZeroDivisionError:
            p2 = (c - x[i]) * float("inf")

        y[i] = max (0, min (min (1, p1), p2))
        
    return y

'''----------------------------------------------------------
    Write [Rules] section to output file.
-----------------------------------------------------------'''
def write_rules_section (fid, fis):
    num_inputs = len(fis.input)
    num_outputs = len(fis.output)
    num_rules = len(fis.rule)
    
    fid.write('[Rules]\n')
    
    for i in range(num_rules):
        next_ant = [w + 1 for w in fis.rule[i].antecedent]
        next_con = [w + 1 for w in fis.rule[i].consequent]     
        
        next_wt = fis.rule[i].weight
        next_connect = fis.rule[i].connection

        # Print membership functions for the inputs
        if num_inputs > 0:
            if isinstance(next_ant[0], int):
                fid.write('%d' % (next_ant[0]))
            else:
                fid.write('%.2f' % (next_ant[0]))
        
        for j in range(1, num_inputs):
            if isinstance(next_ant[j], int):
                fid.write(' %d' % (next_ant[j]))
            else:
                fid.write(' %.2f' % (next_ant[j]))
                        
        fid.write(', ')
        
        # Print membership functions for the outputs
        for j in range(num_outputs):            
            if isinstance(next_con[j], int):
                fid.write('%d ' % (next_con[j]))
            else:
                fid.write('%.2f ' % (next_con[j]))
        
        # Print the weight in parents
        if isinstance(next_wt, int):
            fid.write('(%d) : ' % (next_wt))
        else:
            fid.write('(%.4f) : ' % (next_wt))
        
        # Print the connection and a newline
        fid.write('%d\n' % (next_connect))

'''----------------------------------------------------------
    For each FIS output, write [Output<number>] section to
    output file.
-----------------------------------------------------------'''        
def write_output_sections (fid, fis):
    num_outputs = len(fis.output)
    
    for i in range(num_outputs):
        num_mfs = len(fis.output[i].mf)
        fid.write('[Output%d]\n' % (i + 1))
        fid.write('Name=\'%s\'\n' % (fis.output[i].name))
        fid.write('Range=[%d %d]\n' % (fis.output[i].range[0] , fis.output[i].range[1]))
        fid.write('NumMFs=%d\n' % (num_mfs))
        for j in range(num_mfs):
            fid.write('MF%d=\'%s\':\'%s\',[%s]\n' % (j + 1, fis.output[i].mf[j].name, fis.output[i].mf[j].type, ' '.join(str(x) for x in fis.output[i].mf[j].params))) 
            
        fid.write("\n") 
            
'''----------------------------------------------------------
    For each FIS output, write [Input<number>] section to
    output file.
-----------------------------------------------------------'''              
def write_input_sections (fid, fis):
    num_inputs = len(fis.input)
    
    for i in range(num_inputs):
        num_mfs = len(fis.input[i].mf)
        fid.write('[Input%d]\n' % (i + 1))
        fid.write('Name=\'%s\'\n' % (fis.input[i].name))
        fid.write('Range=[%d %d]\n' % (fis.input[i].range[0] , fis.input[i].range[1]))
        fid.write('NumMFs=%d\n' % (num_mfs))
        for j in range(num_mfs):
            fid.write('MF%d=\'%s\':\'%s\',[%s]\n' % (j + 1, fis.input[i].mf[j].name, fis.input[i].mf[j].type, ' '.join(str(x) for x in fis.input[i].mf[j].params)))            
        fid.write("\n")   
    
'''----------------------------------------------------------
    Write [System] section of the output file.
-----------------------------------------------------------'''     
def write_system_section (fid, fis):

    fid.write("[System]\n")
    fid.write('Name=\'%s\'\n' % (fis.name))
    fid.write('Type=\'%s\'\n' % (fis.type))
    fid.write('Version=%0.1f\n' % (fis.version))
    fid.write('NumInputs=%d\n' % len(fis.input))
    fid.write('NumOutputs=%d\n' % len(fis.output))
    fid.write('NumRules=%d\n' % len(fis.rule))
    fid.write('AndMethod=\'%s\'\n' % (fis.andMethod))
    fid.write('OrMethod=\'%s\'\n' % (fis.orMethod))
    fid.write('ImpMethod=\'%s\'\n' % (fis.impMethod))
    fid.write('AggMethod=\'%s\'\n' % (fis.aggMethod))
    fid.write('DefuzzMethod=\'%s\'\n' % (fis.defuzzMethod))
    fid.write("\n")
    
'''----------------------------------------------------------
    Open the output file and Return the fid
-----------------------------------------------------------'''      
def open_output_file (filename):
    fid = open(filename, 'w')
    return fid

'''----------------------------------------------------------
    Save the specified FIS currently to a file 
    named by the user
-----------------------------------------------------------''' 
def writefis(fis, filename='filename.fis'):
    # Open the output file
    fid = open_output_file (filename)
    
    # Write the [System], [Input<number>], [Output<number>], and [Rules]
    # sections of the output file
    write_system_section (fid, fis)
    write_input_sections (fid, fis)
    write_output_sections (fid, fis)
    write_rules_section (fid, fis)
    
    # Close the output file
    fid.close()
