from gurobipy import *



def lp():
    try:
        mod = Model('lp')
        lp_vars = []
        for i in range(3):
            lp_vars.append(mod.addVar(lb=0, vtype=GRB.CONTINUOUS, name='x_%s' % i))

        lp_cons = []
        lp_cons.append(mod.addConstr(lp_vars[0] + lp_vars[1] + 2*lp_vars[2] >= 2, name='con0'))  #
        lp_cons.append(mod.addConstr(3*lp_vars[0] - 2*lp_vars[1] + lp_vars[2] >= 3, name='con1'))  #
        # mod.setAttr("ModelSense", GRB.MAXIMIZE)
        mod.setObjective(2*lp_vars[0] + lp_vars[1] + lp_vars[2], GRB.MINIMIZE)  #

        # col = Column([2, 1], lp_cons)
        # mod.addVar(0.0, GRB.INFINITY, 1.0, GRB.CONTINUOUS, "cg_" + str(i), col)

        # col = Column([2.0, 1.0], lp_cons)
        # col.remove(lp_cons)
        mod.update()
        print(mod.getVars())
        mod.remove(mod.getVars()[2])
        # mod.update()
        mod.optimize()

        print('Objective: ', mod.objVal)
        mod.printAttr('X')

    except GurobiError as e:

        print('Error code ' + str(e.errno) + ": " + str(e))

    except AttributeError:

        print('Encountered an attribute error')

lp()

