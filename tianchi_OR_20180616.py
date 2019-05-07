# _*-coding: utf-8-*-

import csv
import numpy as np
from gurobipy import *
import time


def read_data_mach():
    machine_dict1 = {}  # {code:name}
    machine_dict2 = {}  # {name:code}
    machine_att = []  # [CPU, Memory, Disk, P, M, PM]
    with open(r'C:\Bee\ProjectFile\Tianchi_scheduling_20180614\scheduling_preliminary_machine_resources_20180606.csv',
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
    with open(r'C:\Bee\ProjectFile\Tianchi_scheduling_20180614\scheduling_preliminary_app_resources_20180606.csv',
              'rU') as fa:
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
    with open(r'C:\Bee\ProjectFile\Tianchi_scheduling_20180614\scheduling_preliminary_instance_deploy_20180606.csv',
              'rU') as fi:
        reader = csv.reader(fi)
        for i, row in enumerate(reader):
            inst_dict1[i] = row[0]
            inst_dict2[row[0]] = i
            inst_app[i, int(row[1].strip('app_')) - 1] = 1

    return inst_app


def read_data_inst2():
    app_inst_dict = {}  # {app_name: [inst1,inst2,...]}
    with open(r'C:\Bee\ProjectFile\Tianchi_scheduling_20180614\scheduling_preliminary_instance_deploy_20180606.csv',
              'rU') as fi:
        reader = csv.reader(fi)
        for row in reader:
            if row[1] in app_inst_dict:
                app_inst_dict[row[1]].append(row[0])
            else:
                app_inst_dict[row[1]] = [row[0]]

    return app_inst_dict


def read_data_app_inter():
    app1_app2 = []  # constraint between two app
    app_app = []  # constraint of an app itself
    with open(r'C:\Bee\ProjectFile\Tianchi_scheduling_20180614\scheduling_preliminary_app_interference_20180606.csv',
              'rU') as fai:
        reader = csv.reader(fai)
        for i, row in enumerate(reader):
            if row[0] == row[1]:
                app_app.append([int(row[0].strip('app_')) - 1, int(row[2])])
            else:
                app1_app2.append([int(row[0].strip('app_')) - 1, int(row[1].strip('app_')) - 1, int(row[2])])

    return app1_app2, app_app


# inst attributes
# cpu=np.dot(inst_app,cpu_t)
# mem=np.dot(inst_app,mem_t)
# disk=np.dot(inst_app,app_att[:,0])
# P=np.dot(inst_app,app_att[:,1])
# M=np.dot(inst_app,app_att[:,2])
# PM=np.dot(inst_app,app_att[:,3])



def scheduling1():
    try:
        # create model
        mod = Model('Mixed_Integer')
        print('s')
        # define variables
        x = mod.addVars(inst_num, machine_num, vtype=GRB.BINARY, name='x')
        print('x')
        y = mod.addVars(app_num, machine_num, vtype=GRB.BINARY, name='y')
        print('y')
        alp = mod.addVars(time_num, machine_num, vtype=GRB.BINARY, name='alpha')
        bet = mod.addVars(time_num, machine_num, vtype=GRB.BINARY, name='beta')
        # gam=mod.addVars(time_num,machine_num,vtype=GRB.BINARY,name='gama')
        utl = mod.addVars(time_num, machine_num, vtype=GRB.CONTINUOUS, lb=0, ub=1, name='utilization')
        print((1))
        # set objective
        obj = 0
        for t in range(time_num):
            obj += quicksum(10 * utl[t, j] - 2.5 * bet[t, j] - 5 * alp[t, j] for j in range(machine_num))

        # adding constraints
        for i in range(inst_num):
            mod.addConstr(quicksum(x[i, j] for j in range(machine_num)) == 1)

        for t in range(time_num):
            for j in range(machine_num):
                mod.addConstr(quicksum(cpu[i, t] * x[i, j] for i in range(inst_num)) <= machine_att[j, 0])
                mod.addConstr(quicksum(mem[i, t] * x[i, j] for i in range(inst_num)) <= machine_att[j, 1])

        print((2))
        for j in range(machine_num):
            mod.addConstr(quicksum(disk[i] * x[i, j] for i in range(inst_num)) <= machine_att[j, 2])
            mod.addConstr(quicksum(P[i] * x[i, j] for i in range(inst_num)) <= machine_att[j, 3])
            mod.addConstr(quicksum(M[i] * x[i, j] for i in range(inst_num)) <= machine_att[j, 4])
            mod.addConstr(quicksum(PM[i] * x[i, j] for i in range(inst_num)) <= machine_att[j, 5])

        for k in range(app_num):
            for j in range(machine_num):
                mod.addConstr(y[k, j] <= quicksum(inst_app[i, k] * x[i, j] for i in range(inst_num)))
                mod.addConstr(y[k, j] >= 0.00001 * quicksum(inst_app[i, k] * x[i, j] for i in range(inst_num)))
        print((3))
        for j in range(machine_num):
            for v in app1_app2:
                pass
                # mod.addConstr(quicksum(inst_app[i,v[1]]*x[i,j] for i in range(inst_num))<=v[2]+10000*(1-y[v[0],j]))

            for w in app_app:
                pass
                # mod.addConstr(quicksum(inst_app[i,w[0]]*x[i,j] for i in range(inst_num))<=w[1])
        print((4))
        for t in range(time_num):
            for j in range(machine_num):
                mod.addConstr(
                    utl[t, j] == quicksum(cpu[i, t] * x[i, j] for i in range(inst_num)) / (machine_att[j, 0] + 0.0))
                mod.addConstr(utl[t, j] >= 10 * (1 - alp[t, j]))
                mod.addConstr(utl[t, j] <= 1 - 10 * alp[t, j])
                mod.addConstr(utl[t, j] - 0.5 >= 0.0001 - 10 * bet[t, j])
                mod.addConstr(utl[t, j] - 0.5 <= 10 * (1 - bet[t, j]))
                mod.addConstr(alp[t, j] + bet[t, j] <= 1)
        print((5))
        mod.Params.TimeLimit = 300
        # mod.Params.MIPFocus=1
        # mod.Params.ImproveStartGap=0.4
        mod.Params.MIPGap = 0.01
        mod.optimize()

        # print 'Objective: ', mod.objVal
        mod.printAttr('X')


    except GurobiError:
        print('Error Reported')


def scheduling2():
    try:
        # create model
        mod = Model('Mixed_Integer')
        print('s')
        # define variables
        x = mod.addVars(app_num, machine_num, vtype=GRB.INTEGER, lb=0, name='x')
        print('x')
        y = mod.addVars(app_num, machine_num, vtype=GRB.BINARY, name='y')
        print('y')
        alp = mod.addVars(time_num, machine_num, vtype=GRB.BINARY, name='alpha')
        bet = mod.addVars(time_num, machine_num, vtype=GRB.BINARY, name='beta')
        # gam=mod.addVars(time_num,machine_num,vtype=GRB.BINARY,name='gama')
        utl = mod.addVars(time_num, machine_num, vtype=GRB.CONTINUOUS, lb=0, ub=1, name='utilization')
        print('utl')

        # set objective
        obj = 0
        for t in range(time_num):
            obj += quicksum(10 * utl[t, j] - 2.5 * bet[t, j] - 5 * alp[t, j] for j in range(machine_num))
        mod.setObjective(obj, GRB.MINIMIZE)

        # adding constraints
        for k in range(app_num):
            # print 'app_'+str(k+1), len(app_inst['app_'+str(k+1)])
            mod.addConstr(quicksum(x[k, j] for j in range(machine_num)) == len(app_inst['app_' + str(k + 1)]))

        print(1)
        machine_att[:4, 2] = 1024  # app_30 has 4 instances with disk 1024
        for j in range(machine_num):
            mod.addConstr(quicksum(cpu_max[k] * x[k, j] for k in range(app_num)) <= machine_att[j, 0])
            mod.addConstr(quicksum(mem_max[k] * x[k, j] for k in range(app_num)) <= machine_att[j, 1])
            mod.addConstr(quicksum(app_att[k, 0] * x[k, j] for k in range(app_num)) <= machine_att[j, 2])
            mod.addConstr(quicksum(app_att[k, 1] * x[k, j] for k in range(app_num)) <= machine_att[j, 3])
            mod.addConstr(quicksum(app_att[k, 2] * x[k, j] for k in range(app_num)) <= machine_att[j, 4])
            mod.addConstr(quicksum(app_att[k, 3] * x[k, j] for k in range(app_num)) <= machine_att[j, 5])
        print(2)

        for k in range(app_num):
            for j in range(machine_num):
                mod.addConstr(y[k, j] <= x[k, j])
                mod.addConstr(y[k, j] >= 0.00001 * x[k, j])
        print(3)
        for j in range(machine_num):
            for v in app1_app2:
                # pass
                if v[0] <= app_num - 1 and v[1] <= app_num - 1:
                    # print v[0],v[1],v[2]
                    mod.addConstr(x[v[1], j] <= v[2] + 10000 * (1 - y[v[0], j]))

            for w in app_app:
                # pass
                if w[0] <= app_num - 1:
                    # print w[0],w[1]
                    mod.addConstr(x[w[0], j] <= w[1] + 1)
        print(4)
        for t in range(time_num):
            for j in range(machine_num):
                mod.addConstr(
                    utl[t, j] == quicksum(cpu_t[k, t] * x[k, j] for k in range(app_num)) / (machine_att[j, 0] + 0.0))
                mod.addConstr(utl[t, j] <= 1 - alp[t, j])
                mod.addConstr(utl[t, j] - 0.5 <= 1 - bet[t, j])
                mod.addConstr(alp[t, j] + bet[t, j] <= 1)
        print(5)
        mod.Params.TimeLimit = 1000
        # mod.Params.MIPFocus=1
        # mod.Params.ImproveStartGap=0.4
        mod.Params.MIPGap = 0.01
        mod.optimize()

        print('Objective: ', mod.objVal)
        # mod.printAttr('X')

        used_machine = 0
        for j in range(machine_num):
            a = 0
            for t in range(time_num):
                a += 1 - alp[t, j].x
            if a > 0:
                used_machine += 1
        print('Total used machines: ', used_machine)


    except GurobiError:
        print('Error Reported')


def scheduling3(runtime):
    try:
        # create model
        mod = Model('Mixed_Integer')
        print('s')
        # define variables
        x = mod.addVars(app_num, machine_num, vtype=GRB.INTEGER, lb=0, name='x')
        print('x')
        # y=mod.addVars(app_num,machine_num,vtype=GRB.BINARY,name='y')
        print('y')
        alp = mod.addVars(machine_num, vtype=GRB.BINARY, name='alpha')

        utl = mod.addVars(machine_num, vtype=GRB.CONTINUOUS, lb=0, ub=1, name='utilization')
        mu = mod.addVars(machine_num, vtype=GRB.CONTINUOUS, lb=0, ub=0.5, name='mu')
        print('utl')

        # set objective
        obj = 0
        for t in range(time_num):
            obj += quicksum(15 * mu[j] + 1 - alp[j] for j in range(machine_num))
        mod.setObjective(obj, GRB.MINIMIZE)

        # adding constraints
        for k in range(app_num):
            # print 'app_'+str(k+1), len(app_inst['app_'+str(k+1)])
            mod.addConstr(quicksum(x[k, j] for j in range(machine_num)) == len(app_inst['app_' + str(k + 1)]))

        print(1)
        machine_att[:40, 0] = 92  # app_30 has 4 instances with cpu 92
        machine_att[:40, 1] = 288  # app_30 has 4 instances with memory 288
        machine_att[:40, 2] = 1024  # app_30 has 4 instances with disk 1024
        for j in range(machine_num):
            for t in range(time_num):
                mod.addConstr(quicksum(cpu_t[k, t] * x[k, j] for k in range(app_num)) <= machine_att[j, 0])
                mod.addConstr(quicksum(mem_t[k, t] * x[k, j] for k in range(app_num)) <= machine_att[j, 1])

            mod.addConstr(quicksum(app_att[k, 0] * x[k, j] for k in range(app_num)) <= machine_att[j, 2])
            mod.addConstr(quicksum(app_att[k, 1] * x[k, j] for k in range(app_num)) <= machine_att[j, 3])
            mod.addConstr(quicksum(app_att[k, 2] * x[k, j] for k in range(app_num)) <= machine_att[j, 4])
            mod.addConstr(quicksum(app_att[k, 3] * x[k, j] for k in range(app_num)) <= machine_att[j, 5])
        print(2)

        # for k in range(app_num):
        #     for j in range(machine_num):
        #         mod.addConstr(y[k,j]<=x[k,j])
        #         mod.addConstr(y[k, j] >= 0.0001 * x[k, j])
        print(3)
        # for j in range(machine_num):
        #     for v in app1_app2:
        #         # pass
        #         if v[0]<=app_num-1 and v[1]<=app_num-1:
        #             # print v[0],v[1],v[2]
        #             mod.addConstr(x[v[1], j] <= v[2]+10000*(1-y[v[0], j]))
        #
        #     for w in app_app:
        #         # pass
        #         if w[0]<=app_num-1:
        #             # print w[0],w[1]
        #             mod.addConstr(x[w[0], j] <= w[1]+1)
        print(4)

        for j in range(machine_num):
            mod.addConstr(
                utl[j] == quicksum(cpu_sort[k][80] * x[k, j] for k in range(app_num)) / (machine_att[j, 0] + 0.0))
            mod.addConstr(utl[j] <= 1 - alp[j])
            mod.addConstr(mu[j] >= 0)
            mod.addConstr(mu[j] >= utl[j] - 0.5)
        print(5)

        # for j in range(3000-1):
        #     mod.addConstr(alp[j]<=alp[j+1])
        #     mod.addConstr(alp[j+3000] <= alp[j + 3001])

        mod.Params.TimeLimit = runtime
        # mod.Params.MIPFocus=1
        # mod.Params.ImproveStartGap=0.4
        mod.Params.MIPGap = 0.01
        mod.optimize()

        print('Objective: ', mod.objVal)
        # mod.printAttr('X')

        used_machine = 0
        for j in range(machine_num):
            if alp[j].x == 0:
                print('machine', j)
                used_machine += 1
        print('Total used machines: ', used_machine)


    except GurobiError:
        print('Error Reported')


def scheduling4(runtime):
    try:
        # create model
        mod = Model('Mixed_Integer')
        print('s')
        # define variables
        x = mod.addVars(app_num, machine_num, vtype=GRB.INTEGER, lb=0, name='x')
        print('x')
        # y=mod.addVars(app_num,machine_num,vtype=GRB.BINARY,name='y')
        print('y')
        alp = mod.addVars(machine_num, vtype=GRB.BINARY, name='alpha')

        # utl=mod.addVars(machine_num,vtype=GRB.CONTINUOUS,lb=0,ub=1,name='utilization')
        # mu = mod.addVars(machine_num, vtype=GRB.CONTINUOUS, lb=0, ub=0.5, name='mu')
        print('utl')

        # set objective
        obj = 0
        for t in range(time_num):
            obj += quicksum(1 - alp[j] for j in range(machine_num))
        mod.setObjective(obj / time_num, GRB.MINIMIZE)

        # adding constraints
        for k in range(app_num):
            # print 'app_'+str(k+1), len(app_inst['app_'+str(k+1)])
            mod.addConstr(quicksum(x[k, j] for j in range(machine_num)) == len(app_inst['app_' + str(k + 1)]))

        print(1)

        for j in range(machine_num):
            for t in range(time_num):
                mod.addConstr(quicksum(cpu_t[k, t] * x[k, j] for k in range(app_num)) <= 0.5 * machine_att[j, 0])
                mod.addConstr(quicksum(mem_t[k, t] * x[k, j] for k in range(app_num)) <= machine_att[j, 1])

            mod.addConstr(quicksum(app_att[k, 0] * x[k, j] for k in range(app_num)) <= machine_att[j, 2])
            mod.addConstr(quicksum(app_att[k, 1] * x[k, j] for k in range(app_num)) <= machine_att[j, 3])
            mod.addConstr(quicksum(app_att[k, 2] * x[k, j] for k in range(app_num)) <= machine_att[j, 4])
            mod.addConstr(quicksum(app_att[k, 3] * x[k, j] for k in range(app_num)) <= machine_att[j, 5])
        print(2)

        # for k in range(app_num):
        #     for j in range(machine_num):
        #         mod.addConstr(y[k,j]<=x[k,j])
        #         mod.addConstr(y[k, j] >= 0.0001 * x[k, j])
        print(3)
        # for j in range(machine_num):
        #     for v in app1_app2:
        #         # pass
        #         if v[0]<=app_num-1 and v[1]<=app_num-1:
        #             # print v[0],v[1],v[2]
        #             mod.addConstr(x[v[1], j] <= v[2]+10000*(1-y[v[0], j]))
        #
        #     for w in app_app:
        #         # pass
        #         if w[0]<=app_num-1:
        #             # print w[0],w[1]
        #             mod.addConstr(x[w[0], j] <= w[1]+1)
        print(4)

        for j in range(machine_num):
            # mod.addConstr(utl[j] == quicksum(cpu_sort[k][80] * x[k, j] for k in range(app_num)) / (machine_att[j, 0] + 0.0))
            mod.addConstr(0.0001 * quicksum(x[k, j] for k in range(app_num)) <= 1 - alp[j])
            # mod.addConstr(mu[j]>=0)
            # mod.addConstr(mu[j]>=utl[j]-0.5)
        print(5)

        for j in range(machine_num - 1):
            mod.addConstr(alp[j] <= alp[j + 1])
        # mod.addConstr(alp[j+3000] <= alp[j + 3001])

        mod.Params.TimeLimit = runtime
        # mod.Params.MIPFocus=1
        # mod.Params.ImproveStartGap=0.4
        mod.Params.MIPGap = 0.01
        mod.optimize()

        print('Objective: ', mod.objVal)
        # mod.printAttr('X')
        # opt_pat = np.zeros([app_num, 31])
        opt_pat = [[0] * 31 for ii in range(app_num)]
        for i in range(app_num):
            for j in range(31):
                opt_pat[i][j] = abs(x[i, j].x)
        print('best pattern: ', opt_pat)
        used_machine = 0
        for j in range(machine_num):
            if alp[j].x == 0:
                print('machine', j)
                used_machine += 1
        print('Total used machines: ', used_machine)


    except GurobiError:
        print('Error Reported')


if __name__ == '__main__':
    t0 = time.time()

    # inst_num=68219
    app_num = 9338
    machine_num = 6000
    time_num = 98

    machine_att = read_data_mach()
    machine_att[:50, 0] = 32  # app_30 has 4 instances with cpu 92
    machine_att[:50, 1] = 64  # app_30 has 4 instances with memory 288
    machine_att[:50, 2] = 1024  # app_30 has 4 instances with disk 1024
    print('machine')

    app_att, cpu_t, mem_t, cpu_sort = read_data_app()
    cpu_max, mem_max = np.max(cpu_t, 1), np.max(mem_t, 1)
    print('app number', len(cpu_max))
    print('t number', len(cpu_sort[0]))
    # print cpu_t[19,:]
    # print cpu_sort[19]

    # inst_app=read_data_inst()
    app_inst = read_data_inst2()
    print('inst')

    app1_app2, app_app = read_data_app_inter()
    print('app-app')
    print('app1_app2 ', len(app1_app2))
    print('app_app ', len(app_app))

    # inst_num=600
    machine_num = 150
    app_num = 100
    print(app_num, machine_num)
    print(app_inst['app_500'])

    scheduling4(runtime=5000)

    t1 = time.time()
    print('Total elapsed time: ', t1 - t0)
