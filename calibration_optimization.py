from gurobipy import * # Requires Gurobi installed
import numpy as np

def run_model2(run_no,params): ## solve optimization problem for each user
    x_values= []
    for u in range(0,params['U']): ## this loop could be distributed to several machines, solve for every user u
        mm = Model('Opt')
        strii = str("mylog"+str(run_no)+".txt")
        mm.setParam(GRB.Param.TimeLimit, 600) # Time limit can be included 
        
        x = [] # decision variable of offering an item i to user u
        y = [] # auxiliary decision variable of weighted total variation penalty
        I = params["I"]; R = params["R"]
        x = mm.addVars(1,I, obj=params["u"][u*I:(u+1)*I], vtype=GRB.BINARY, name = "x") 
        y = mm.addVars(R,1, lb=0.0, obj= (params['calib'][:,u]+1)*params["alpha"]/2, vtype=GRB.CONTINUOUS, name = "y") 
        
        
        ####CONSTRAINTS
        mm.addConstr(quicksum(x[0,i] for i in range(I)) == params["k"]) ###Top-k selection constraint
        for r in range(R): ## trick for minimizing absolute value, could be a way to do faster without creating new decision variables.
            mm.addConstr(y[r,0]  >=  params['calib'][r,u]*params["k"]   - quicksum(x[0,i]*params["genre_fuzz"][r,i] for i in range(I)) )
            mm.addConstr(y[r,0]  >= -params['calib'][r,u]*params["k"]   + quicksum(x[0,i]*params["genre_fuzz"][r,i] for i in range(I)) )                    
                     
        mm.optimize()
        x_values.append(mm.x)
#        np.save('./Solution_of_user_' + str(u), mm.x)

    return mm, x_values
    
def main2(run_no, alpha_value, params_k, initial_calibrations, genre_fuzz):
    
    params = {}    
    params["u"] = np.load('utility_file.npy') ## utility between user and item (matrix |U|x|I|)
    params["k"] = params_k; params["alpha"] =  alpha_value

    params["U"] = len(params["u"]) #6040 # number of users
    params["I"] = len(params["u"][0]) # number of items
    params["R"] = 19 # number of genres
    params['calib'] = initial_calibrations; params['genre_fuzz'] = genre_fuzz
    
    
    cutoff = -9999
    params["u"] = [0 if params["u"][j,i] < cutoff else -params["u"][j,i]*(1-params["alpha"])  for j in range(params["U"]) for i in range(params["I"])]
    ## give 0 utility (and then ignore) if utility is under certain threshold
    
    model, dvar = run_model2(run_no,params)

    return model, dvar, params

count=0
for run_no in range(1): ## Can be run with multiple seeds provided
    ### these two files will be required:
    initial_calibrations = np.load('Calibration_file.npy') #Genre times User: 
    ##Percentage of each genre for every user that we are trying to match. Comes from user history.
    
    genre_fuzzy = np.load('genre_file.npy') # Genre times Item, percentage of genre for each item
    ##If a movie has two tags Action and Adventure, scores of Action and Adventure are 0.5 and the rest are 0. 

    for  params_k in [10]:  #top - k list
        for  alpha_value in [0.99]:  #weight selection
            np.random.seed(run_no)
            model, dvar, params = main2(run_no, alpha_value, params_k, initial_calibrations, genre_fuzzy)
#            np.save('./all_solutions, dvar)

### All the genres:
### {'Action','Adventure','Animation','Children','Comedy','Crime','Documentary','Drama','Fantasy','Film-Noir','Horror',
### 'IMAX','Musical','Mystery','Romance','Sci-Fi','Thriller','War','Western'}
