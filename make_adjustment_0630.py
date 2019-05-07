# -*- coding: utf-8 -*-

import time
import csv
from gurobipy import *
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt


def read_data(data_code, data_date):
    """Reading data that will be used in the model."""
    inst_app = {}  # {inst: app,...}
    app_inst = {}  # {app1: [inst1, inst2], ...}
    app_resource = {}  # {app1: [[cpu_t], [mem_t], disk, p, m, pm], ...}
    app_intf = []  # [[app_a, app_b, lmt], ...]

    with open(
                    r'C:\Bee\ProjectFile\Tianchi_scheduling_20180614\Inputdata\scheduling_preliminary_%sinstance_deploy_%s.csv' % (
            data_code, data_date), 'rU') as f1:
        reader = csv.reader(f1)
        for val in reader:
            inst_app[val[0]] = val[1]
            if val[1] in app_inst:
                app_inst[val[1]].append(val[0])
            else:
                app_inst[val[1]] = [val[0]]

    with open(
                    r'C:\Bee\ProjectFile\Tianchi_scheduling_20180614\Inputdata\scheduling_preliminary_%sapp_resources_%s.csv' % (
            data_code, data_date), 'rU') as f2:
        reader = csv.reader(f2)
        for val in reader:
            cpu = val[1].split('|')
            cpu1 = [float(x) for x in cpu]
            mem = val[2].split('|')
            mem1 = [float(x) for x in mem]
            app_resource[val[0]] = [cpu1, mem1, float(val[3]), int(val[4]), int(val[5]), int(val[6])]

    with open(
                    r'C:\Bee\ProjectFile\Tianchi_scheduling_20180614\Inputdata\scheduling_preliminary_%sapp_interference_%s.csv' % (
            data_code, data_date), 'rU') as f3:
        reader = csv.reader(f3)
        for val in reader:
            app_a = int(val[0].strip('app_')) - 1
            app_b = int(val[1].strip('app_')) - 1
            app_intf.append([app_a, app_b, int(val[2])])

    print(len(app_inst), len(app_resource), len(app_intf))
    return inst_app, app_inst, app_resource, app_intf


def initial_pattern(file_name):
    ini_pat1 = []
    ini_pat2 = []
    mach_app = {}
    with open(r'C:\Bee\ProjectFile\Tianchi_scheduling_20180614\results\%s.csv' % file_name, 'rU') as fi:
        reader = csv.reader(fi)
        for val in reader:
            mach = val[1]
            app = inst_app[val[0]]
            app_ind = int(app.strip('app_')) - 1
            if mach in mach_app:
                mach_app[mach][app_ind] += 1
            else:
                mach_app[mach] = [0] * order_cnt
                mach_app[mach][app_ind] += 1
    for val in list(mach_app.items()):
        if int(val[0].strip('machine_')) <= 3000:
            ini_pat1.append(val[1])
        else:
            ini_pat2.append(val[1])

    return [ini_pat1, ini_pat2]


def ip_model(pat1, pat2):
    """Using column generation to solve cutting stock problem -- Integer master problem"""
    print('\n*******Start the Integer Master Problem!********')
    pat_cnt_resp = [len(pat1), len(pat2)]
    pat_cnt_acm = [0, len(pat1)]
    pat = pat1 + pat2
    pat_cnt = len(pat)
    using_pat = []
    using_num = []
    print('Found pattern number: ', pat_cnt)
    try:
        mod = Model('master-problem')
        # y[j] denotes the number of pattern0[j] to be used
        y = mod.addVars(pat_cnt, lb=0, vtype=GRB.INTEGER, name='y')

        obj = 0
        for j in range(len(pat_cnt_resp)):
            for i in range(pat_cnt_resp[j]):
                obj += pr[j] * y[i + pat_cnt_acm[j]]

        mod.setObjective(obj, GRB.MINIMIZE)

        # for j in range(order_cnt):
        #     mod.addConstr(quicksum(pat[i][j] * y[i] for i in range(pat_cnt)) >= demands[j])
        for j in range(order_cnt):
            sum1 = 0
            for i in range(pat_cnt):
                if pat[i][j] > 0:
                    sum1 += pat[i][j] * y[i]
            mod.addConstr(sum1 >= demands[j])

        for j in range(len(pat_cnt_resp)):
            mod.addConstr(quicksum(y[i + pat_cnt_acm[j]] for i in range(pat_cnt_resp[j])) <= ln_lmt[j])

        # mod.Params.TimeLimit = 260
        mod.Params.MIPGap = 0.001
        mod.optimize()

        print('Objective: ', mod.objVal)
        mod.printAttr('X')

        for i in range(pat_cnt):
            if y[i].x > 0:
                using_pat.append(pat[i])
                using_num.append(y[i].x)

        if mod.status == GRB.OPTIMAL:
            print('\n')
            print('***   Successful! We have found the optimal cutting solution.   ***')
            return mod.objVal, using_pat, using_num

    except GurobiError as e:
        print('Error of master-problem reported: ')
        print(e)


def rlmp(pat1, pat2):
    """The restricted linear master problem."""

    pat_cnt_resp = [len(pat1), len(pat2)]
    pat_cnt_acm = [0, len(pat1)]
    pat = pat1 + pat2
    pat_cnt = len(pat)

    try:
        rlmp = Model('Master problem')

        # x[i] denotes the number of pattern i that will be used
        x = rlmp.addVars(pat_cnt, lb=0, vtype=GRB.CONTINUOUS, name='x')

        obj = 0
        for j in range(len(pat_cnt_resp)):
            for i in range(pat_cnt_resp[j]):
                obj += pr[j] * x[i + pat_cnt_acm[j]]

        rlmp.setObjective(obj, GRB.MINIMIZE)

        # it takes a long time to read this constraint
        # for j in range(order_cnt):
        #     rlmp.addConstr(quicksum(x[i] * pat[i][j] for i in range(pat_cnt)) >= demands[j])
        for j in range(order_cnt):
            sum1 = 0
            for i in range(pat_cnt):
                if pat[i][j] > 0:
                    sum1 += x[i] * pat[i][j]
            rlmp.addConstr(sum1 >= demands[j])

        # for j in range(len(pat_cnt_resp)):
        #     rlmp.addConstr(quicksum(x[i + pat_cnt_acm[j]] for i in range(pat_cnt_resp[j])) <= ln_lmt[j])


        rlmp.optimize()

        print('Objective: ', rlmp.objVal)
        # rlmp.printAttr('X')

        if rlmp.status == GRB.OPTIMAL:
            shadow_price = rlmp.getAttr('Pi', rlmp.getConstrs())
            # print '\nShadow price of constraints: ', shadow_price, '\n'
            # print '***   Successful! We have found the optimal cutting solution.   ***'
            return shadow_price[:order_cnt], rlmp.objval


    except GurobiError as e:
        print('Error of master-problem reported: ')
        print(e)


def sub(pi, mach_res, raw_cost):
    """Sub problem of column generation."""

    print('*' * 10, 'Start solving sub problem... ', '*' * 10)
    new_pat = [0] * order_cnt
    try:
        subp = Model('sub problem')
        # y[i] denotes the number of order i in the new pattern
        y = subp.addVars(order_cnt, vtype=GRB.INTEGER, name='y')
        z = subp.addVars(order_cnt, vtype=GRB.BINARY, name='z')

        obj = raw_cost - quicksum(y[i] * pi[i] for i in range(order_cnt))
        subp.setObjective(obj, GRB.MINIMIZE)

        for t in range(time_num):
            # cpu and memory limit
            subp.addConstr(quicksum(y[i] * app_res[i][0][t] for i in range(order_cnt)) <= 0.5 * mach_res[0])
            subp.addConstr(quicksum(y[i] * app_res[i][1][t] for i in range(order_cnt)) <= mach_res[1])

        # disk, p, m pm limit
        subp.addConstr(quicksum(y[i] * app_res[i][2] for i in range(order_cnt)) <= mach_res[2])
        subp.addConstr(quicksum(y[i] * app_res[i][3] for i in range(order_cnt)) <= mach_res[3])
        subp.addConstr(quicksum(y[i] * app_res[i][4] for i in range(order_cnt)) <= mach_res[4])
        subp.addConstr(quicksum(y[i] * app_res[i][5] for i in range(order_cnt)) <= mach_res[5])

        # interference constraint
        for val in app_intf:
            app_a, app_b = val[0], val[1]
            if app_a >= order_cnt or app_b >= order_cnt:
                continue
            if app_a == app_b:
                subp.addConstr(y[app_a] <= val[2] + 1)
            else:
                subp.addConstr(y[app_b] <= val[2] + 1000 * (1 - z[app_a]))

        for j in range(order_cnt):
            subp.addConstr(z[j] <= y[j])
            subp.addConstr(z[j] >= 0.001 * y[j])

        subp.optimize()

        print('Objective: ', subp.objVal)
        # subp.printAttr('X')

        for i in range(order_cnt):
            new_pat[i] = y[i].x
        # print 'new pattern: ', new_pat
        if subp.status == GRB.OPTIMAL:
            # print '\n'
            # print '***  Successful! We have found a better cutting solution.  ***'
            return subp.objVal, new_pat

    except GurobiError as e:
        print('Error of sub-problem reported: ')
        print(e)


def distinct(lst):
    """Remove the repetitive elements of a list."""
    lst_out = []
    for v in lst:
        if v in lst_out:
            pass
        else:
            lst_out.append(v)

    return lst_out


if __name__ == '__mai__':
    """We are using CG to solve the scheduling problem with two types of raw material and resource limit."""
    t0 = time.time()

    # data_code = 'b_'
    # data_date = '20180726'
    data_code = ''
    data_date = '20180606'
    initial_file = 'improve_20180724 125606'
    inst_app, app_inst, app_resource, app_intf = read_data(data_code, data_date)
    order_cnt = len(app_inst)

    ln_lmt = [30000, 30000]
    ln = [[32, 64, 600, 7, 3, 7], [92, 288, 1024, 7, 7, 9]]  # [cpu, mem, disk, p, m, pm]
    raw_typ = len(ln)
    pr = [1, 1]  # price of each raw material
    demands = [0] * order_cnt
    app_res = [0] * order_cnt
    for val in app_inst:
        app_ind = int(val.strip('app_')) - 1
        demands[app_ind] = len(app_inst[val])

    for val in app_resource:
        app_ind = int(val.strip('app_')) - 1
        app_res[app_ind] = app_resource[val]
    time_num = len(app_res[0][0])

    pattern_catg = initial_pattern(file_name=initial_file)
    print('initial pattern number small/large: ', len(pattern_catg[0]), len(pattern_catg[1]))
    pattern_catg = [distinct(pattern_catg[0]), distinct(pattern_catg[1])]
    print('distinct pattern number small/large: ', len(pattern_catg[0]), len(pattern_catg[1]))
    # print 'initial patterns: ', pattern
    # print 'categoried patterns: '
    # print pattern_catg[0]
    # print pattern_catg[1]

    objv_rec = []
    max_itr = 2000
    itr = 0
    while itr < max_itr:
        tt0 = time.time()
        print('\n', '*' * 30, 'master problem', '*' * 30)
        pi, objv = rlmp(pattern_catg[0], pattern_catg[1])
        objv_rec.append(objv)
        sigm123 = [0, 0]
        new_pat123 = [0, 0]
        print('\n', '*' * 30, 'sub problem 1', '*' * 30)
        sigm123[0], new_pat123[0] = sub(pi, ln[0], pr[0])  # solve sub-p for raw1
        print('\n', '*' * 30, 'sub problem 2', '*' * 30)
        sigm123[1], new_pat123[1] = sub(pi, ln[1], pr[1])  # solve sub-p for raw2
        # sigm = min(sigm123)  # choose the minimal sigma
        # print '\nChecking parameter value: ', sigm
        # ind = sigm123.index(sigm)
        # new_pat = new_pat123[ind]
        stop_ind = 0
        if sigm123[0] >= 0 - 1e-6:
            # break
            stop_ind += 1
        else:
            pattern_catg[0].append(new_pat123[0])
        if sigm123[1] >= 0 - 1e-6:
            # break
            stop_ind += 1
        else:
            pattern_catg[1].append(new_pat123[1])
        if stop_ind == 2:
            break

        itr += 1
        tt1 = time.time()
        print('@' * 30, 'iteration%s time:' % itr, tt1 - tt0, '@' * 30)

    print('\n')
    print('=' * 50)
    print('   Get the final result...   ')
    print('=' * 50)
    print('\nEach category of patterns are as follows: ')
    print('Number of pattern1: ', len(pattern_catg[0]))
    print('Number of pattern2: ', len(pattern_catg[1]))

    optval, using_pat, using_num = ip_model(pattern_catg[0], pattern_catg[1])
    print('Optimal objective value: ', optval)
    print('Patter using number: \n', using_num)
    run_time = time.strftime("%Y%m%d %H%M%S", time.localtime())
    with open(r'C:\Bee\ProjectFile\Tianchi_scheduling_20180614\results\CG_result\columns%s.csv' % run_time, 'wb') as fo:
        writer = csv.writer(fo)
        for val in using_pat:
            writer.writerow(val)

    t1 = time.time()
    print('Total iteration: ', itr)
    print('Total elapsed time: ', t1 - t0)

    print('\nShow the objective value evolution of the relaxed master problem...')
    plt.plot(objv_rec)
    plt.show()


def initial_pattern2(file_name, app_num):
    """use a small number of apps."""
    ini_pat1 = []
    ini_pat2 = []
    mach_app = {}
    with open(r'C:\Bee\ProjectFile\Tianchi_scheduling_20180614\results\%s.csv' % file_name, 'rU') as fi:
        reader = csv.reader(fi)
        for val in reader:
            mach = val[1]
            app = inst_app[val[0]]
            app_ind = int(app.strip('app_')) - 1
            if app_ind < app_num:
                if mach in mach_app:
                    mach_app[mach][app_ind] += 1
                else:
                    mach_app[mach] = [0] * app_num
                    mach_app[mach][app_ind] += 1
    for val in list(mach_app.items()):
        if int(val[0].strip('machine_')) <= 3000:
            ini_pat1.append(val[1])
        else:
            ini_pat2.append(val[1])

    return [ini_pat1, ini_pat2]


def initial_pattern3(file_name, app_num):
    """use a small number of apps."""
    ini_pat1 = []
    ini_pat2 = []
    mach_app = {}
    with open(r'C:\Bee\ProjectFile\Tianchi_scheduling_20180614\results\CG_result\%s.csv' % file_name, 'rU') as fi:
        reader = csv.reader(fi)
        for val in reader:
            vl = [int(val[i]) for i in range(order_cnt)]
            if int(val[order_cnt]) == 1:
                ini_pat1.append(vl)
            else:
                ini_pat2.append(vl)

    return [ini_pat1, ini_pat2]


if __name__ == '__main__':
    """Use a small number of apps to test column generation."""
    t0 = time.time()

    # data_code = 'b_'
    # data_date = '20180726'
    data_code = ''
    data_date = '20180606'
    initial_file = 'half_pat_20180805 094755'
    inst_app, app_inst, app_resource, app_intf = read_data(data_code, data_date)
    app_num = 2000
    order_cnt = app_num

    ln_lmt = [30000, 30000]
    ln = [[32, 64, 600, 7, 3, 7], [92, 288, 1024, 7, 7, 9]]  # [cpu, mem, disk, p, m, pm]
    raw_typ = len(ln)
    pr = [1, 1]  # price of each raw material
    demands = [0] * order_cnt
    app_res = [0] * order_cnt
    for val in app_inst:
        app_ind = int(val.strip('app_')) - 1
        if app_ind < app_num:
            demands[app_ind] = len(app_inst[val])

    for val in app_resource:
        app_ind = int(val.strip('app_')) - 1
        if app_ind < app_num:
            app_res[app_ind] = app_resource[val]
    time_num = len(app_res[0][0])

    pattern_catg = initial_pattern3(initial_file, app_num)
    print('initial pattern number small/large: ', len(pattern_catg[0]), len(pattern_catg[1]))
    pattern_catg = [distinct(pattern_catg[0]), distinct(pattern_catg[1])]
    print('distinct pattern number small/large: ', len(pattern_catg[0]), len(pattern_catg[1]))
    # print 'initial patterns: ', pattern
    # print 'categoried patterns: '
    # print pattern_catg[0]
    # print pattern_catg[1]

    optval0, using_pat0, using_num0 = ip_model(pattern_catg[0], pattern_catg[1])

    objv_rec = []
    max_itr = 1000
    itr = 0
    while itr < max_itr:
        tt0 = time.time()
        print('\n', '*' * 30, 'master problem', '*' * 30)
        pi, objv = rlmp(pattern_catg[0], pattern_catg[1])
        objv_rec.append(objv)
        sigm123 = [0, 0]
        new_pat123 = [0, 0]
        print('\n', '*' * 30, 'sub problem 1', '*' * 30)
        # sigm123[0], new_pat123[0] = sub(pi, ln[0], pr[0])  # solve sub-p for raw1
        print('\n', '*' * 30, 'sub problem 2', '*' * 30)
        sigm123[1], new_pat123[1] = sub(pi, ln[1], pr[1])  # solve sub-p for raw2
        # sigm = min(sigm123)  # choose the minimal sigma
        sigm = sigm123[1]
        print('\nChecking parameter value: ', sigm)
        # ind = sigm123.index(sigm)

        new_pat = new_pat123[1]
        stop_ind = 0
        if sigm >= 0 - 1e-6:
            break
            # stop_ind += 1
        else:
            pattern_catg[1].append(new_pat123[1])
            # if sigm123[1] >= 0 - 1e-6:
            #     break
            # stop_ind += 1
        # else:
        #     pattern_catg[1].append(new_pat123[1])
        # if stop_ind == 2:
        #     break

        itr += 1
        tt1 = time.time()
        print('@' * 30, 'iteration%s time:' % itr, tt1 - tt0, '@' * 30)

    print('\n')
    print('=' * 50)
    print('   Get the final result...   ')
    print('=' * 50)
    print('\nEach category of patterns are as follows: ')
    print('Number of pattern1: ', len(pattern_catg[0]))
    print('Number of pattern2: ', len(pattern_catg[1]))

    optval, using_pat, using_num = ip_model(pattern_catg[0], pattern_catg[1])
    print('Initial Pattern Optimal objective value: ', optval0)
    print('Initial Pattern using number: \n', using_num0)
    print('Column Generation Optimal objective value: ', optval)
    print('Column Generation Pattern using number: \n', using_num)
    run_time = time.strftime("%Y%m%d %H%M%S", time.localtime())
    # with open(r'C:\Bee\ProjectFile\Tianchi_scheduling_20180614\results\CG_result\columns%s.csv' % run_time, 'wb') as fo:
    #     writer = csv.writer(fo)
    #     for val in using_pat:
    #         writer.writerow(val)

    t1 = time.time()
    print('Total iteration: ', itr)
    print('Total elapsed time: ', t1 - t0)

    print('\nShow the objective value evolution of the relaxed master problem...')
    plt.plot(objv_rec)
    plt.show()
