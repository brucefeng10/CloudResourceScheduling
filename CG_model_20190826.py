import numpy as np
from gurobipy import *
import time
import csv
import matplotlib.pyplot as plt

input_file = '.\\resources\\Inputdata\\'


def read_data_mach():
    machine_dict1 = {}  # {code:name}
    machine_dict2 = {}  # {name:code}
    machine_att = []  # [CPU, Memory, Disk, P, M, PM]
    with open(input_file + 'scheduling_preliminary_machine_resources_20180606.csv',
              'rU') as fm:
        reader = csv.reader(fm)
        for i, row in enumerate(reader):
            machine_dict1[i] = row[0]
            machine_dict2[row[0]] = i
            machine_att.append([int(row[1]), int(row[2]), int(row[3]), int(row[4]), int(row[5]), int(row[6])])

    return np.array(machine_att)


def read_data_app():
    app_dict1 = {}  # {code:name}
    app_dict2 = {}  # {name:code}
    app_att = []  # [[disk, P, M, PM]]
    cpu_t = []
    cpu_sort = []
    mem_t = []
    with open(input_file + 'scheduling_preliminary_app_resources_20180606.csv', 'rU') as fa:
        reader = csv.reader(fa)
        for i, row in enumerate(reader):
            app_dict1[i] = row[0]
            app_dict2[row[0]] = i
            app_att.append([int(row[3]), int(row[4]), int(row[5]), int(row[6])])
            cpu0 = row[1].split('|')
            cpu1 = [float(v) for v in cpu0]
            cpu_t.append(cpu1)
            cpu_sort.append(sorted(cpu1))
            mem0 = row[2].split('|')
            cpu1 = [float(v) for v in mem0]
            mem_t.append(cpu1)

    return np.array(app_att), np.array(cpu_t), np.array(mem_t), cpu_sort


def read_data_inst1(inst_num, app_num):
    inst_dict1 = {}  # {code: name}
    inst_dict2 = {}  # {name: code}
    inst_app = np.zeros([inst_num, app_num])
    with open(input_file + 'scheduling_preliminary_instance_deploy_20180606.csv', 'rU') as fi:
        reader = csv.reader(fi)
        for i, row in enumerate(reader):
            inst_dict1[i] = row[0]
            inst_dict2[row[0]] = i
            inst_app[i, int(row[1].strip('app_')) - 1] = 1

    return inst_app


def read_data_inst2():
    app_inst_dict = {}  # {app_name: [inst1,inst2,...]}
    with open(input_file + 'scheduling_preliminary_instance_deploy_20180606.csv', 'rU') as fi:
        reader = csv.reader(fi)
        for row in reader:
            if row[1] in app_inst_dict:
                app_inst_dict[row[1]].append(row[0])
            else:
                app_inst_dict[row[1]] = [row[0]]

    return app_inst_dict


def read_data_app_inter():
    app_intf = []  # [app1, app2, interf_cnt] interference between two app
    with open(input_file + 'scheduling_preliminary_app_interference_20180606.csv', 'rU') as f3:
        reader = csv.reader(f3)
        for val in reader:
            app_a = int(val[0].strip('app_')) - 1
            app_b = int(val[1].strip('app_')) - 1
            app_intf.append([app_a, app_b, int(val[2])])

    return app_intf


def rmp_int():
    """Using column generation to solve initial mixed integer problem"""
    t0 = time.time()

    machine_att = read_data_mach()
    app_att, cpu_t, mem_t, cpu_sort = read_data_app()
    cpu_max, mem_max = np.max(cpu_t, 1), np.max(mem_t, 1)
    app_inst = read_data_inst2()
    inst_num = 600
    machine_num = 150
    app_num = 9338
    time_num = 98

    rmp_coeff = [0.0] * app_num
    for i in range(app_num):
        rmp_coeff[i] = int(min(0.5 * machine_att[5000, 0] / max(cpu_t[i, :]), machine_att[5000, 1] / max(mem_t[i, :]),
                               machine_att[5000, 2] / max(app_att[i, 0], 0.01),
                               machine_att[5000, 3] / max(app_att[i, 1], 0.01),
                               machine_att[5000, 4] / max(app_att[i, 2], 0.01),
                               machine_att[5000, 5] / max(app_att[i, 3], 0.01)))
    try:
        rmp = Model('mip-problem')
        rmp.Params.OutputFlag = 0
        # y[j] denotes the number of pattern0[j] to be used
        y = rmp.addVars(app_num, lb=0, vtype=GRB.INTEGER, name='y')

        obj = quicksum(y[j] for j in range(app_num))
        rmp.setObjective(obj, GRB.MINIMIZE)

        for i in range(app_num):
            rmp.addConstr(rmp_coeff[i] * y[i] >= len(app_inst['app_' + str(i + 1)]))

        rmp.optimize()

        print('Objective: ', rmp.objVal)
        rmp.printAttr('X')

        if rmp.status == GRB.OPTIMAL:
            print('\n***   Successful! We have found the optimal cutting solution.   ***')

    except GurobiError as e:
        print('Error of master-problem reported: ')
        print(e)

    t1 = time.time()
    print('Total elapsed time: ', t1-t0)


def col_gen():
    """Column Generation process."""

    t0 = time.time()

    # read data
    # inst_num = 68219
    # app_num = 9338
    # machine_num = 6000
    # time_num = 98
    machine_att = read_data_mach()
    app_att, cpu_t, mem_t, cpu_sort = read_data_app()
    cpu_max, mem_max = np.max(cpu_t, 1), np.max(mem_t, 1)
    app_inst = read_data_inst2()
    inst_num = 600
    machine_num = 150
    app_num = 1500
    time_num = 98
    max_cpu = 1.0

    rmp_coeff = [0.0] * app_num
    for i in range(app_num):
        rmp_coeff[i] = int(min(max_cpu * machine_att[5000, 0]/max(cpu_t[i, :]), machine_att[5000, 1]/max(mem_t[i, :]),
                             machine_att[5000, 2]/max(app_att[i, 0], 0.01), machine_att[5000, 3]/max(app_att[i, 1], 0.01),
                             machine_att[5000, 4]/max(app_att[i, 2], 0.01), machine_att[5000, 5]/max(app_att[i, 3], 0.01)))
    try:
        rmp = Model('Linear restricted master problem')
        sub = Model('Sub problem')
        rmp.Params.OutputFlag = 0
        sub.Params.OutputFlag = 0

        # initialize rmp
        # add variables
        rmp_vars = []
        for i in range(app_num):
            rmp_vars.append(rmp.addVar(lb=0.0, vtype=GRB.CONTINUOUS, name="rmp_" + str(i)))

        # add constraints
        rmp_constr = []
        for i in range(app_num):
            rmp_constr.append(rmp.addConstr(rmp_coeff[i] * rmp_vars[i] >= len(app_inst['app_' + str(i + 1)]), 'rmpcon_' + str(i)))

        rmp.setObjective(quicksum(rmp_vars[j] for j in range(app_num)), GRB.MINIMIZE)
        # initialize rmp end

        # initialize sub
        sub_vars = []
        for i in range(app_num):
            sub_vars.append(sub.addVar(lb=0.0, vtype=GRB.INTEGER, name="sub_" + str(i)))

        for t in range(time_num):
            sub.addConstr(quicksum(cpu_t[k, t] * sub_vars[k] for k in range(app_num)) <= max_cpu * machine_att[5000, 0])
            sub.addConstr(quicksum(mem_t[k, t] * sub_vars[k] for k in range(app_num)) <= machine_att[5000, 1])

        sub.addConstr(quicksum(app_att[k, 0] * sub_vars[k] for k in range(app_num)) <= machine_att[5000, 2])
        sub.addConstr(quicksum(app_att[k, 1] * sub_vars[k] for k in range(app_num)) <= machine_att[5000, 3])
        sub.addConstr(quicksum(app_att[k, 2] * sub_vars[k] for k in range(app_num)) <= machine_att[5000, 4])
        sub.addConstr(quicksum(app_att[k, 3] * sub_vars[k] for k in range(app_num)) <= machine_att[5000, 5])
        # initialize sub end

        print('         *****Column Generation Iteration*****          \n')

        max_itr = 3000
        itr = 0
        stop_ind = True
        rmp_objvals = []  # objective value of rmp in each iteration

        while itr < max_itr and stop_ind:
            itr += 1
            print('current iteration time: ', itr)

            rmp.update()
            rmp.optimize()
            rmp_objvals.append(rmp.objval)
            print('Current rmp objval: ', rmp.objval)

            sub.setObjective(quicksum(rmp_constr[i].pi * sub_vars[i] for i in range(app_num)), GRB.MAXIMIZE)
            sub.update()
            sub.optimize()
            if sub.status != GRB.status.OPTIMAL:
                raise Exception("Pricing-Problem can not reach optimal!")
            reduced_cost = 1 - sub.objval
            print('reduced cost', reduced_cost)
            if reduced_cost < -0.001:
                new_col = sub.getAttr("X", sub.getVars())
                # new_col = [sub_var[i].x for i in range(nwidth)]
                rmp_col = Column()
                rmp_col.addTerms(new_col, rmp_constr)
                rmp_vars.append(rmp.addVar(lb=0.0, obj=1.0, vtype=GRB.CONTINUOUS, name="cg_" + str(itr), column=rmp_col))
            else:
                stop_ind = False

            if itr % 100 == 0:
                rmp.write("model.mps")  # write a model

            print('\n')
        t1 = time.time()
        print('Iteration elapsed time: ', t1 - t0)
        print('         *****Column Generation Iteration End*****          \n')
        print('   ****************************************   ')
        print('   **********Get the final result**********   ')
        print('   ****************************************   ')
        rmp.update()
        rmp.write("model.mps")  # write a model
        mip_var = rmp.getVars()
        for i in range(rmp.numVars):
            mip_var[i].setAttr("VType", GRB.INTEGER)
        # rmp.update()
        rmp.optimize()
        if rmp.status == GRB.OPTIMAL:
            var = rmp.getVars()
            for i in range(rmp.numVars):
                print(var[i].varName, " = ", var[i].x)

            print("Best MIP Solution: ", rmp.objVal, " machines\n")

        print('Total iteration: ', itr)
        t1 = time.time()
        print('Total elapsed time: ', t1 - t0)

        plt.plot(rmp_objvals)
        plt.show()

    except GurobiError as e:
        print('Error code ' + str(e.errno) + ": " + str(e))

    except AttributeError:
        print('Encountered an attribute error')


def col_gen_inference():
    """Column Generation with interference constraints."""

    t0 = time.time()

    # read data
    # inst_num = 68219
    # app_num = 9338
    # machine_num = 6000
    # time_num = 98
    machine_att = read_data_mach()
    app_att, cpu_t, mem_t, cpu_sort = read_data_app()
    cpu_max, mem_max = np.max(cpu_t, 1), np.max(mem_t, 1)
    app_inst = read_data_inst2()
    app_intf = read_data_app_inter()
    inst_num = 600
    machine_num = 150
    app_num = 1000
    time_num = 98

    rmp_coeff = [0.0] * app_num
    for i in range(app_num):
        rmp_coeff[i] = int(min(0.5 * machine_att[5000, 0]/max(cpu_t[i, :]), machine_att[5000, 1]/max(mem_t[i, :]),
                             machine_att[5000, 2]/max(app_att[i, 0], 0.01), machine_att[5000, 3]/max(app_att[i, 1], 0.01),
                             machine_att[5000, 4]/max(app_att[i, 2], 0.01), machine_att[5000, 5]/max(app_att[i, 3], 0.01)))
    try:
        rmp = Model('Linear restricted master problem')
        sub = Model('Sub problem')
        rmp.Params.OutputFlag = 0
        sub.Params.OutputFlag = 0

        # initialize rmp
        # add variables
        rmp_vars = []
        for i in range(app_num):
            rmp_vars.append(rmp.addVar(lb=0.0, vtype=GRB.CONTINUOUS, name="rmp_" + str(i)))

        # add constraints
        rmp_constr = []
        for i in range(app_num):
            rmp_constr.append(rmp.addConstr(rmp_coeff[i] * rmp_vars[i] >= len(app_inst['app_' + str(i + 1)]), 'rmpcon_' + str(i)))

        rmp.setObjective(quicksum(rmp_vars[j] for j in range(app_num)), GRB.MINIMIZE)
        # initialize rmp end

        # initialize sub
        sub_vars = []
        # suby_i: integer, number of instance i in an app
        # subz_i: binary, whether instance i is in an app
        for i in range(app_num):
            sub_vars.append(sub.addVar(lb=0.0, vtype=GRB.INTEGER, name="suby_" + str(i)))
        for i in range(app_num):
            sub_vars.append(sub.addVar(lb=0.0, vtype=GRB.BINARY, name="subz_" + str(i)))

        # cpu and memory limit
        for t in range(time_num):
            sub.addConstr(quicksum(cpu_t[k, t] * sub_vars[k] for k in range(app_num)) <= 0.5 * machine_att[5000, 0])
            sub.addConstr(quicksum(mem_t[k, t] * sub_vars[k] for k in range(app_num)) <= machine_att[5000, 1])
        # disk, p, m pm limit
        sub.addConstr(quicksum(app_att[k, 0] * sub_vars[k] for k in range(app_num)) <= machine_att[5000, 2])
        sub.addConstr(quicksum(app_att[k, 1] * sub_vars[k] for k in range(app_num)) <= machine_att[5000, 3])
        sub.addConstr(quicksum(app_att[k, 2] * sub_vars[k] for k in range(app_num)) <= machine_att[5000, 4])
        sub.addConstr(quicksum(app_att[k, 3] * sub_vars[k] for k in range(app_num)) <= machine_att[5000, 5])
        # interference constraint
        for val in app_intf:
            app_a, app_b = val[0], val[1]
            if app_a >= app_num or app_b >= app_num:
                continue
            if app_a == app_b:
                sub.addConstr(sub_vars[app_a] <= val[2] + 1)
            else:
                sub.addConstr(sub_vars[app_b] <= val[2] + 1000 * (1 - sub_vars[app_a+app_num]))

        for j in range(app_num):
            sub.addConstr(sub_vars[j+app_num] <= sub_vars[j])
            sub.addConstr(sub_vars[j+app_num] >= 0.001 * sub_vars[j])
        # initialize sub end

        print('         *****Column Generation Iteration*****          \n')

        max_itr = 100
        itr = 0
        stop_ind = True
        rmp_objvals = []  # objective value of rmp in each iteration

        while itr < max_itr and stop_ind:
            itr += 1
            print('current iteration time: ', itr)

            rmp.update()
            rmp.optimize()
            rmp_objvals.append(rmp.objval)
            print('Current rmp objval: ', rmp.objval)

            sub.setObjective(quicksum(rmp_constr[i].pi * sub_vars[i] for i in range(app_num)), GRB.MAXIMIZE)
            sub.update()
            sub.optimize()
            if sub.status != GRB.status.OPTIMAL:
                raise Exception("Pricing-Problem can not reach optimal!")
            reduced_cost = 1 - sub.objval
            print('reduced cost', reduced_cost)
            if reduced_cost < -0.001:
                # new_col = sub.getAttr("X", sub.getVars())
                new_col = [sub_vars[i].x for i in range(app_num)]
                rmp_col = Column()
                rmp_col.addTerms(new_col, rmp_constr)
                rmp_vars.append(rmp.addVar(lb=0.0, obj=1.0, vtype=GRB.CONTINUOUS, name="cg_" + str(itr), column=rmp_col))
            else:
                stop_ind = False

            print('\n')

        print('         *****Column Generation Iteration End*****          \n')
        print('   ****************************************   ')
        print('   **********Get the final result**********   ')
        print('   ****************************************   ')
        rmp.update()
        mip_var = rmp.getVars()
        for i in range(rmp.numVars):
            mip_var[i].setAttr("VType", GRB.INTEGER)
        # rmp.update()
        rmp.optimize()
        if rmp.status == GRB.OPTIMAL:
            print("Best MIP Solution: ", rmp.objVal, " machines\n")
            var = rmp.getVars()
            for i in range(rmp.numVars):
                print(var[i].varName, " = ", var[i].x)

        print('Total iteration: ', itr)
        t1 = time.time()
        print('Total elapsed time: ', t1 - t0)

        plt.plot(rmp_objvals)
        plt.show()

    except GurobiError as e:
        print('Error code ' + str(e.errno) + ": " + str(e))

    except AttributeError:
        print('Encountered an attribute error')


if __name__ == '__main__':
    # rmp_int()
    col_gen()
    # col_gen_inference()







