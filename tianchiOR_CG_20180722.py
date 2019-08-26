# -*- coding: utf-8 -*-

import numpy as np
from gurobipy import *
import time
import csv
import matplotlib.pyplot as plt

input_file = 'C:\Bee\ProjectFile\Tianchi_scheduling_20180614\Inputdata\\'


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


def read_data_inst1():
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
    app1_app2 = []  # [app1, app2, interf_cnt] interference between two app
    app_app = []  # constraint of an app itself
    with open(input_file + 'scheduling_preliminary_app_interference_20180606.csv', 'rU') as fai:
        reader = csv.reader(fai)
        for i, row in enumerate(reader):
            if row[0] == row[1]:
                app_app.append([int(row[0].strip('app_')) - 1, int(row[2])])
            else:
                app1_app2.append([int(row[0].strip('app_')) - 1, int(row[1].strip('app_')) - 1, int(row[2])])

    return app1_app2, app_app


def sche_rlmp_int(patt):
    """Using column generation to solve cutting stock problem -- restricted linear master problem"""
    print('*******Start real master problem!********')
    patt_num = int(patt.shape[1])
    print('Found pattern number: ', patt_num)

    try:
        rlmp = Model('master-problem')
        # y[j] denotes the number of pattern0[j] to be used
        y = rlmp.addVars(patt_num, lb=0, vtype=GRB.INTEGER, name='y')

        obj = quicksum(y[j] for j in range(patt_num))
        rlmp.setObjective(obj, GRB.MINIMIZE)

        for i in range(app_num):
            rlmp.addConstr(quicksum(patt[i, j] * y[j] for j in range(patt_num)) >= len(app_inst['app_' + str(i + 1)]))

        rlmp.optimize()

        print('Objective: ', rlmp.objVal)
        rlmp.printAttr('X')

        if rlmp.status == GRB.OPTIMAL:
            print('\n***   Successful! We have found the optimal cutting solution.   ***')

    except GurobiError as e:
        print('Error of master-problem reported: ')
        print(e)


def sche_rlmp(patt):
    """Using column generation to solve cutting stock problem -- restricted linear master problem"""
    print('*******Start rlmp problem!********')
    patt_num = int(patt.shape[1])
    print('Found pattern number: ', patt_num)
    objval, shadow_price = None, None
    try:
        rlmp = Model('master-problem')
        # y[j] denotes the number of pattern0[j] to be used
        y = rlmp.addVars(patt_num, lb=0, vtype=GRB.CONTINUOUS, name='y')
        obj = quicksum(y[j] for j in range(patt_num))
        rlmp.setObjective(obj, GRB.MINIMIZE)

        for i in range(app_num):
            rlmp.addConstr(quicksum(patt[i, j] * y[j] for j in range(patt_num)) >= len(app_inst['app_' + str(i + 1)]))

        rlmp.Params.OutputFlag = 0
        rlmp.optimize()

        objval = rlmp.objVal
        print('Objective: ', objval)
        rlmp.printAttr('X')

        if rlmp.status == GRB.OPTIMAL:
            # shadow_price = rlmp.getAttr('Pi', rlmp.getConstrs())
            shadow_price = rlmp.getAttr(GRB.Attr.Pi)
            # print('Shadow price of constraints: ', shadow_price, '\n')

    except GurobiError as e:
        print('Error of master-problem reported: ')
        print(e)

    return objval, shadow_price


def sche_subp(pi):
    """Using column generation to solve cutting stock problem -- sub-problem"""
    print('*******Start sub problem!********')
    new_pat = np.ones([app_num, 1])  # newly generated pattern in the sub-problem
    try:
        subp = Model('sub-problem')
        # x[i] denotes the number of piece[i] cut in this pattern
        x = subp.addVars(app_num, lb=0, vtype=GRB.INTEGER, name='x')

        obj = quicksum(pi[i] * x[i] for i in range(app_num))
        subp.setObjective(obj, GRB.MAXIMIZE)

        for t in range(time_num):
            subp.addConstr(quicksum(cpu_t[k, t] * x[k] for k in range(app_num)) <= 0.5 * machine_att[5000, 0])
            subp.addConstr(quicksum(mem_t[k, t] * x[k] for k in range(app_num)) <= machine_att[5000, 1])

        subp.addConstr(quicksum(app_att[k, 0] * x[k] for k in range(app_num)) <= machine_att[5000, 2])
        subp.addConstr(quicksum(app_att[k, 1] * x[k] for k in range(app_num)) <= machine_att[5000, 3])
        subp.addConstr(quicksum(app_att[k, 2] * x[k] for k in range(app_num)) <= machine_att[5000, 4])
        subp.addConstr(quicksum(app_att[k, 3] * x[k] for k in range(app_num)) <= machine_att[5000, 5])

        subp.Params.OutputFlag = 0
        subp.optimize()

        print('Objective: ', subp.objVal)
        subp.printAttr('X')

        for i in range(app_num):
            new_pat[i][0] = x[i].x
        # print('new pattern: ', new_pat.T)
        if subp.status == GRB.OPTIMAL:
            # shadow_price = subp.getAttr('Pi', subp.getConstrs())
            # print 'Shadow price of constraints: ', shadow_price
            print('\n')
            print('***  sub-problem optimal.  ***')

    except GurobiError as e:
        print('Error of sub-problem reported: ')
        print(e)

    return new_pat


if __name__ == '__main__':

    t0 = time.time()

    inst_num = 68219
    app_num = 9338
    machine_num = 6000
    time_num = 98

    machine_att = read_data_mach()
    # machine_att[:50, 0] = 32  # app_30 has 4 instances with cpu 92
    # machine_att[:50, 1] = 64  # app_30 has 4 instances with memory 288
    # machine_att[:50, 2] = 1024  # app_30 has 4 instances with disk 1024
    # print('machine')

    app_att, cpu_t, mem_t, cpu_sort = read_data_app()
    cpu_max, mem_max = np.max(cpu_t, 1), np.max(mem_t, 1)
    print('app number', len(cpu_max))
    print('t number', len(cpu_sort[0]))

    # inst_app=read_data_inst()
    app_inst = read_data_inst2()

    inst_num = 600
    machine_num = 150
    app_num = 1000
    print(app_num, machine_num)

    pattern0 = np.eye(app_num, app_num)
    for i in range(app_num):
        pattern0[i, i] = int(min(0.5 * machine_att[5000, 0]/max(cpu_t[i, :]), machine_att[5000, 1]/max(mem_t[i, :]),
                             machine_att[5000, 2]/max(app_att[i, 0], 0.01), machine_att[5000, 3]/max(app_att[i, 1], 0.01),
                             machine_att[5000, 4]/max(app_att[i, 2], 0.01), machine_att[5000, 5]/max(app_att[i, 3], 0.01)))
    pattern = pattern0
    print('initial pattern: ', pattern0)

    stop_ind = True
    max_itr = 100
    rlmp_objval = []  # objective value of rlmp in each iteration
    itr = 0
    while itr < max_itr and stop_ind:
        objv, pi = sche_rlmp(pattern)
        rlmp_objval.append(objv)
        new_pat = sche_subp(pi)
        prof = 0
        for ii in range(app_num):
            prof += pi[ii] * new_pat[ii][0]
        print('checking parameter: ', 1 - prof)
        if 1 - prof >= -1e-2:
            stop_ind = False
        else:
            pattern = np.concatenate((pattern, new_pat), axis=1)

        itr += 1
        print('current iteration time: ', itr)

    print('\n')
    print('   ****************************************   ')
    print('   **********Get the final result**********   ')
    print('   ****************************************   ')

    sche_rlmp_int(pattern)

    print('Total iteration: ', itr)
    t1 = time.time()
    print('Total elapsed time: ', t1 - t0)

    plt.plot(rlmp_objval)
    plt.show()


