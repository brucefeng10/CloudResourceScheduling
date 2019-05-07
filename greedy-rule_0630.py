# -*- coding: utf-8 -*-

import time
import datetime
import csv
import math
import numpy as np
import pandas as pd


def read_data(data_code, data_date):
    data_mach = pd.read_csv(
        "C:\Bee\ProjectFile\Tianchi_scheduling_20180614\Inputdata\scheduling_preliminary_%smachine_resources_%s.csv" % (
        data_code, data_date),
        header=None)  # pd.dataframe
    data_app = pd.read_csv(
        'C:\Bee\ProjectFile\Tianchi_scheduling_20180614\Inputdata\scheduling_preliminary_%sapp_resources_%s.csv' % (
        data_code, data_date),
        usecols=[0, 1, 2, 3, 4, 5, 6], header=None)
    data_inst = pd.read_csv(
        'C:\Bee\ProjectFile\Tianchi_scheduling_20180614\Inputdata\scheduling_preliminary_%sinstance_deploy_%s.csv' % (
        data_code, data_date),
        usecols=[0, 1, 2], header=None)
    app_app = pd.read_csv(
        'C:\Bee\ProjectFile\Tianchi_scheduling_20180614\Inputdata\scheduling_preliminary_%sapp_interference_%s.csv' % (
        data_code, data_date), header=None)

    data_mach.columns = ['mach_name', 'CPU', 'MEM', 'DISK', 'P', 'M', 'PM']
    data_inst.columns = ['inst_name', 'app_name', 'deploy_machine']
    data_app.columns = ['app_name', 'cpu', 'mem', 'disk', 'p', 'm', 'pm']
    app_app.columns = ['APP_A', 'APP_B', 'number']

    data_app['cpu'] = data_app['cpu'].str.split('|')
    data_app['mem'] = data_app['mem'].str.split('|')
    data_app['cpu'] = data_app['cpu'].map(lambda x: [float(v) for v in x])
    data_app['mem'] = data_app['mem'].map(lambda x: [float(v) for v in x])

    data_app['cpu_max'] = data_app['cpu'].map(lambda x: max(x))
    data_app['mem_max'] = data_app['mem'].map(lambda x: max(x))

    max_mean_cpu = data_app['cpu_max'].mean()
    max_mean_mem = data_app['mem_max'].mean()
    max_mean_disk = data_app['disk'].mean()

    data_app['app_score'] = data_app['cpu_max'] / (max_mean_cpu + 0.0) + data_app['mem_max'] / (max_mean_mem + 0.0) + \
                            data_app['disk'] / (max_mean_disk + 0.0)

    # data_app=data_app.sort_values(by='app_score',ascending=False)
    # print data_app.loc[data_app['app_name'] == 'app_3678']

    # rt=pd.DataFrame(data_app,columns=['app_name','disk','p','m','pm'])
    inst = pd.merge(data_inst, data_app, how='left', on=['app_name'])
    inst = inst.sort_values(by='app_score', ascending=False)
    inst_nm = inst[['inst_name', 'app_name', 'cpu', 'mem', 'disk', 'p', 'm', 'pm']]
    inst_dp = inst[['inst_name', 'app_name', 'deploy_machine']]
    inst_array = np.array(inst_nm)  # np.ndarray()
    inst_list = inst_array.tolist()  # list

    mach = data_mach.sort_values(by='CPU', ascending=False)
    mach_array = np.array(mach)
    mach_list = mach_array.tolist()
    # print mach_list[:4]

    inst_dict = {}  # {inst1: [cpu_t,mem_t,disk,p,m,pm]}

    inst_app = {}  # {inst1:app1, inst2:app2}
    inst_deploy = {}  # {inst1: [app_name, deploy_machine]}
    deploy_list = []
    for row in inst_list:
        # print row[4]
        inst_dict[row[0]] = tuple(row[2:8])
        inst_app[row[0]] = row[1]
    # xxx=[]
    for index, row in inst_dp.iterrows():
        # xxx.append([row[0],row[1],row[2]])
        if row[2] == row[2]:  # to judge if row[2] is nan, if it is nan it is not deployed
            inst_deploy[row[0]] = [row[1], row[2]]
            deploy_list.append(row[0])

    app_dict = {}  # {app1:[cpu_t,mem_t,disk,p,m,pm]}
    for index, row in data_app.iterrows():
        app_dict[row[0]] = tuple(row[1:7])

    mach_dict = {}  # {mach1:[cpu,mem,disk,p,m,pm]}
    for index, row in data_mach.iterrows():
        mach_dict[row[0]] = tuple(row[1:7])

    intfer_dict = {}  # {(APP_A,APP_B):k,...,(APP_A,APP_B):k}
    for index, row in app_app.iterrows():

        if row['APP_A'] == row['APP_B']:
            intfer_dict[(row['APP_A'], row['APP_B'])] = row['number'] + 1.
        else:
            # print 'no',row['number'] + 0.
            intfer_dict[(row['APP_A'], row['APP_B'])] = row['number'] + 0.

    return inst_list, inst_dict, inst_app, inst_deploy, deploy_list, mach_list, mach_dict, app_dict, intfer_dict


def interference_assess(app_used_num, app_name):
    '''to assess an instance and judge if it violates the interference lists'''
    '''input existed app number in the checking machine({app1:num,app2:num}), the app name of the instance'''
    '''return True if app_name can be put in this machine, else False'''

    for app in app_used_num:

        if (app, app_name) in intfer_dict:
            if app_name in app_used_num:
                if app_used_num[app_name] + 1 > intfer_dict[(app, app_name)]:
                    # print app_used_num[app_name], intfer_dict[(app,app_name)]
                    return False
                else:
                    pass
            else:
                if intfer_dict[(app, app_name)] < 1:
                    # print app, intfer_dict[(app,app_name)]
                    return False
                else:
                    pass
        if (app_name, app) in intfer_dict:
            if app_name in app_used_num:
                pass
            else:
                if app_used_num[app] > intfer_dict[(app_name, app)]:
                    # print app_used_num[app], intfer_dict[(app_name,app)]
                    return False
                else:
                    pass

    return True


# violation('ssf')
def violation_check0(app_name, mach_name, mach_used_set, mach_used_num, thres, cpu_mode):
    if mach_dict[mach_name][0] - max(list_plus(mach_used_set[mach_name][1][0], app_dict[app_name][0])) < 0 - 1e-6:
        # print 'cpu check'
        return False  # cpu assessment
    elif mach_dict[mach_name][1] - max(list_plus(mach_used_set[mach_name][1][1], app_dict[app_name][1])) < 0 - 1e-6:
        # print 'mem check'
        return False  # memory assessment
    elif app_dict[app_name][2] > mach_dict[mach_name][2] - mach_used_set[mach_name][1][2]:
        # print 'disk check'
        return False  # disk assessment
    elif app_dict[app_name][3] > mach_dict[mach_name][3] - mach_used_set[mach_name][1][3]:
        # print 'p check'
        return False  # p assessment
    elif app_dict[app_name][4] > mach_dict[mach_name][4] - mach_used_set[mach_name][1][4]:
        # print 'm check'
        return False  # m assessment
    elif app_dict[app_name][5] > mach_dict[mach_name][5] - mach_used_set[mach_name][1][5]:
        # print 'pm check'
        return False  # pm assessment
    elif not interference_assess(mach_used_num[mach_name], app_name):
        # print 'interference check'
        return False  # interference assessment
    else:
        return True


def violation_check(app_name, mach_name, mach_used_set, mach_used_num, thres, cpu_mode):
    if mach_name not in mach_used_set:
        if max(app_dict[app_name][0]) <= mach_dict[mach_name][0] and max(app_dict[app_name][1]) <= mach_dict[mach_name][
            1] and app_dict[app_name][2] <= mach_dict[mach_name][2]:
            return True
        else:
            return False
    elif mach_dict[mach_name][0] - max(list_plus(mach_used_set[mach_name][1][0], app_dict[app_name][0])) < 0 - 1e-6:
        # print 'cpu check'
        return False  # cpu assessment
    elif mach_dict[mach_name][1] - max(list_plus(mach_used_set[mach_name][1][1], app_dict[app_name][1])) < 0 - 1e-6:
        # print 'mem check'
        return False  # memory assessment
    elif app_dict[app_name][2] > mach_dict[mach_name][2] - mach_used_set[mach_name][1][2]:
        # print 'disk check'
        return False  # disk assessment
    elif app_dict[app_name][3] > mach_dict[mach_name][3] - mach_used_set[mach_name][1][3]:
        # print 'p check'
        return False  # p assessment
    elif app_dict[app_name][4] > mach_dict[mach_name][4] - mach_used_set[mach_name][1][4]:
        # print 'm check'
        return False  # m assessment
    elif app_dict[app_name][5] > mach_dict[mach_name][5] - mach_used_set[mach_name][1][5]:
        # print 'pm check'
        return False  # pm assessment
    elif not interference_assess(mach_used_num[mach_name], app_name):
        # print 'interference check'
        return False  # interference assessment
    elif cpu_mode == 'average' and sum(list_plus(app_dict[app_name][0], mach_used_set[mach_name][1][0])) / (
        0. + time_num) > thres * mach_dict[mach_name][0] + 1e-6:
        return False  # average cpu assessment
    elif cpu_mode == 'max' and max(list_plus(app_dict[app_name][0], mach_used_set[mach_name][1][0])) > thres * \
            mach_dict[mach_name][0] + 1e-6:
        return False  # average cpu assessment
    else:
        return True


def list_plus(x, y):
    '''input two lists, add them element by element'''
    z = []
    for i in range(len(x)):
        summ = x[i] + y[i]
        z.append(summ)
    return z


def list_minus(x, y):
    '''input two lists, add them element by element'''
    z = []
    for i in range(len(x)):
        z.append(x[i] - y[i])
    return z


def list_equal(x, y):
    for i in range(len(x)):
        if x[i] == y[i]:
            return True
    return False


def self_checking():
    time_num = 98
    inst_set, inst_dict, mach_set, mach_dict, app_dict, intfer_dict = read_data()
    mach_used_set = {}
    mach_used_set['machine_3001'] = [mach_dict['machine_3001'], app_dict['app_8559']]
    mach_used_num = {'machine_3001': {'app_8559': 1}}
    print(app_dict['app_8439'][0])
    print('immed')
    print(mach_used_set['machine_3001'][1][0])
    if violation_check('app_8439', 'machine_3001'):
        print('can put')
    else:
        print('can not put')


def reconstruction(thres, inst_set_in, mach_set_in):
    """not consider the initial deployment"""
    # inst_set is the set of instances need to be deployed, mach_set is the machine set that can be used

    print('not consider the initial deployment')
    t0 = time.time()
    result = []  # [instance id, machine id]
    mach_used_set = {}  # {mach_name:[[max value],[accumulated value]]}
    # max value: [cpu,memory,disk,p,m,pm], accumulated value: [cpu_t,mem_t,disk,p,m,pm]
    mach_used_num = {}  # {mach_name:{'app_name': inst_number}}

    mach_patt = {}  # {mach: [2,1,0,....]}
    mach_iter = 0
    mach_name_new = mach_set[mach_iter][0]  # initialize as the first machine
    ind = 0
    for inst in inst_set_in:
        # print inst
        # print mach_used_set
        # print mach_used_num
        app_ind = int(inst[1].strip('app_')) - 1
        mach_red = []
        for mach in mach_used_set:
            if violation_check(inst[1], mach, mach_used_set, mach_used_num, thres, cpu_mode):
                gap_reduce = (max(mach_used_set[mach][1][0]) - min(mach_used_set[mach][1][0])) - (
                    max(list_plus(inst[2], mach_used_set[mach][1][0])) - min(
                        list_plus(inst[2], mach_used_set[mach][1][0])))
                mach_red.append([gap_reduce, mach])
        if mach_iter < machine_num:
            gap_reduce_new = 0 - (max(inst[2]) - min(inst[2]))
            mach_red.append([gap_reduce_new, mach_name_new])
        if len(mach_red) == 0:
            thres += 0.1
            print('*' * 50)
            print('We cannot deploy any more instances under the current threshold standard')
            print('We will change the threshold to %f' % thres)
            print('*' * 50)

            for mach in mach_used_set:
                if violation_check(inst[1], mach, mach_used_set, mach_used_num, thres, cpu_mode):
                    gap_reduce = (max(mach_used_set[mach][1][0]) - min(mach_used_set[mach][1][0])) - (
                        max(list_plus(inst[2], mach_used_set[mach][1][0])) - min(
                            list_plus(inst[2], mach_used_set[mach][1][0])))
                    mach_red.append([gap_reduce, mach])
        mach_red.sort(reverse=True)
        mach_deploy = mach_red[0][1]  # deploy inst to mach_name
        result.append([inst[0], mach_deploy])  # this inst is assigned to mach_red[0][1]
        if mach_deploy in mach_patt:
            mach_patt[mach_deploy][app_ind] += 1
        else:
            mach_patt[mach_deploy] = [0] * 4669
            mach_patt[mach_deploy][app_ind] += 1

        # update mach_used_num
        if mach_deploy in mach_used_num:
            if inst[1] in mach_used_num[mach_deploy]:  # inst[1] is the app name of this instance
                mach_used_num[mach_deploy][inst[1]] += 1
            else:
                mach_used_num[mach_deploy][inst[1]] = 1
        else:
            mach_used_num[mach_deploy] = {}
            mach_used_num[mach_deploy][inst[1]] = 1

        # update accumulated value of mach_used_set
        if mach_deploy in mach_used_set:
            mach_used_set[mach_deploy][1][0] = list_plus(mach_used_set[mach_deploy][1][0], inst[2])
            mach_used_set[mach_deploy][1][1] = list_plus(mach_used_set[mach_deploy][1][1], inst[3])
            mach_used_set[mach_deploy][1][2:] = list_plus(mach_used_set[mach_deploy][1][2:], inst[4:8])
        else:
            mach_used_set[mach_deploy] = [[], []]
            mach_used_set[mach_deploy][0] = mach_dict[mach_deploy]
            mach_used_set[mach_deploy][1] = inst[2:8]

        # update the new machine
        if mach_name_new in mach_used_set and mach_iter < machine_num:
            mach_iter += 1
            if mach_iter >= machine_num:
                print('All machines have been used!')
                print('Number of instances assigned: ', ind + 1)
                print('We will use the machines with residual resources.')
            else:

                mach_name_new = mach_set_in[mach_iter][0]

        if list_equal(mach_used_set[mach_deploy][0][2:], mach_used_set[mach_deploy][1][2:]):
            print('machine full: ', mach_deploy)
            del mach_used_set[mach_deploy]  # if any of disk,p,m,pm resource is used up, del this mach in mach_used_set

        print(ind, mach_iter - 1)
        ind += 1
        # if ind>20:
        #     break

    t1 = time.time()
    print('\nTotal elapsed time: ', t1 - t0)

    # getting the score
    used_mach = {}  # [cpu_t,mem_t,disk,p,m,pm]
    score = 0
    for v in result:
        if v[1] in used_mach:
            used_mach[v[1]][0] = list_plus(used_mach[v[1]][0], inst_dict[v[0]][0])
            used_mach[v[1]][1] = list_plus(used_mach[v[1]][1], inst_dict[v[0]][1])
            used_mach[v[1]][2:] = list_plus(used_mach[v[1]][2:], inst_dict[v[0]][2:])
        else:
            used_mach[v[1]] = [0, 1, 2, 3, 4, 5]
            used_mach[v[1]][0] = inst_dict[v[0]][0]
            used_mach[v[1]][1] = inst_dict[v[0]][1]
            used_mach[v[1]][2:] = list(inst_dict[v[0]][2:])

    for mach in used_mach:
        for cpu in used_mach[mach][0]:
            utilization = cpu / (mach_dict[mach][0] + 0.0) - 0.5
            if utilization <= 0:
                score += 1
            else:
                score += (1 + 10 * (math.e ** utilization - 1))
    print('Total scores: ', score / time_num)

    run_time = time.strftime("%Y%m%d %H%M%S", time.localtime())
    # with open(r'C:\Bee\ProjectFile\Tianchi_scheduling_20180614\results\need_adjust_%s.csv' % run_time, 'wb') as fr:
    #     writer = csv.writer(fr)
    #     for v in result:
    #         writer.writerow(v)
    with open(r'C:\Bee\ProjectFile\Tianchi_scheduling_20180614\results\CG_result\half_pat_%s.csv' % run_time,
              'wb') as fr:
        writer = csv.writer(fr)
        for v in mach_patt:
            if int(v.strip('machine_')) <= 3000:
                writer.writerow(mach_patt[v] + [1, 0])
            else:
                writer.writerow(mach_patt[v] + [0, 1])


def keep_initial(thres):
    '''keep the initial deployment if no conflicts'''
    print('keep the initial deployment if no conflicts')
    t0 = time.time()

    inst_set0, inst_dict, inst_app, inst_deploy, deploy_list, mach_set0, mach_dict, app_dict, intfer_dict = read_data(
        data_code, data_date)
    # inst_set=[inst1,inst2,...]  # inst1: [inst_name,app_name,cpu_t,mem_t,disk,p,m,pm,app_score]
    # mach_set = [mach1,mach2,...]  # mach1: [mach_name,cpu,mem,disk,p,m,pm]
    # app_dict = {app1:[cpu_t,mem_t,disk,p,m,pm]}

    result = []  # [instance id, machine id]
    mach_used_set = {}  # {mach_name:[[max value],[accumulated value]]}
    # max value: [cpu,memory,disk,p,m,pm], accumulated value: [cpu_t,mem_t,disk,p,m,pm]
    mach_used_num = {}  # {mach_name:{'app_name': inst_number}}

    keep_list = []
    move_list = []
    initial_used_mach = []
    print('initial deployed number: ', len(inst_deploy))
    for instance in deploy_list:
        app = inst_deploy[instance][0]
        mach = inst_deploy[instance][1]
        if mach in mach_used_num:
            if violation_check(app, mach, mach_used_set, mach_used_num, thres, cpu_mode):
                # if interference_assess(mach_used_num[inst_deploy[instance][1]],inst_deploy[instance][0]):
                if app in mach_used_num[mach]:
                    mach_used_num[mach][app] += 1
                else:
                    mach_used_num[mach][app] = 1

                mach_used_set[mach][1][0] = list_plus(mach_used_set[mach][1][0], inst_dict[instance][0])
                mach_used_set[mach][1][1] = list_plus(mach_used_set[mach][1][1], inst_dict[instance][1])
                mach_used_set[mach][1][2:] = list_plus(mach_used_set[mach][1][2:], inst_dict[instance][2:])

                keep_list.append(instance)
                if mach not in initial_used_mach:
                    initial_used_mach.append(mach)

            else:
                move_list.append(instance)

        else:
            mach_used_num[mach] = {}
            mach_used_num[mach][app] = 1
            mach_used_set[mach] = [[], []]
            mach_used_set[mach][0] = list(mach_dict[mach])
            mach_used_set[mach][1] = list(inst_dict[instance])

            keep_list.append(instance)
            if mach not in initial_used_mach:
                initial_used_mach.append(mach)

    keeplen = len(keep_list)
    print('initial kept instances number: ', keeplen)
    print('move list number: ', len(move_list))
    inilen = len(initial_used_mach)
    print('initial used machine number :', inilen)
    # with open(r'C:\Bee\ProjectFile\Tianchi_scheduling_20180614\results\keep_list.csv','wb') as fw:
    #     writer=csv.writer(fw)
    #     for kl in keep_list:
    #         writer.writerow([kl,inst_deploy[kl][1]])

    # remove those deployed instances and used machines

    inst_set = []
    mach_set = []
    for v in inst_set0:
        if v[0] not in keep_list:
            inst_set.append(v)

    for w in mach_set0:
        if w[0] not in initial_used_mach:
            mach_set.append(w)
    print('to be deployed number: ', len(inst_set))
    print('unused machine number: ', len(mach_set))
    full_mach = []
    for ma in mach_used_set:
        if list_equal(mach_used_set[ma][0][:3],
                      [max(mach_used_set[ma][1][0]), max(mach_used_set[ma][1][1]), mach_used_set[ma][1][2]]):
            full_mach.append(ma)
    for v in full_mach:
        del mach_used_set[v]  # if any of max_cpu, max_mem, disk resource is used up, del this mach in mach_used_set
    print('vacant used machine number: ', len(mach_used_num))

    mach_iter = 0
    mach_name_new = mach_set[mach_iter][0]  # initialize as the first machine
    ind = 0
    for inst in inst_set:
        # print inst
        mach_red = []
        for mach in mach_used_set:
            if violation_check(inst[1], mach, mach_used_set, mach_used_num, thres, cpu_mode):
                gap_reduce = (max(mach_used_set[mach][1][0]) - min(mach_used_set[mach][1][0])) - (
                    max(list_plus(inst[2], mach_used_set[mach][1][0])) - min(
                        list_plus(inst[2], mach_used_set[mach][1][0])))
                mach_red.append([gap_reduce, mach])
        if mach_iter < machine_num - inilen:
            gap_reduce_new = 0 - (max(inst[2]) - min(inst[2]))
            mach_red.append([gap_reduce_new, mach_name_new])
        if len(mach_red) == 0:
            thres += 0.1
            print('*' * 50)
            print('We cannot deploy any more instances under the current threshold standard')
            print('We will change the threshold to %f' % thres)
            print('*' * 50)

            for mach in mach_used_set:
                if violation_check(inst[1], mach, mach_used_set, mach_used_num, thres, cpu_mode):
                    gap_reduce = (max(mach_used_set[mach][1][0]) - min(mach_used_set[mach][1][0])) - (
                        max(list_plus(inst[2], mach_used_set[mach][1][0])) - min(
                            list_plus(inst[2], mach_used_set[mach][1][0])))
                    mach_red.append([gap_reduce, mach])

        mach_red.sort(reverse=True)
        mach_deploy = mach_red[0][1]
        # print inst[0],mach_name
        result.append([inst[0], mach_deploy])  # this inst is assigned to mach_red[0][1]

        # update mach_used_num
        if mach_deploy in mach_used_num:
            if inst[1] in mach_used_num[mach_deploy]:  # inst[1] is the app name of this instance
                mach_used_num[mach_deploy][inst[1]] += 1
            else:
                mach_used_num[mach_deploy][inst[1]] = 1
        else:
            mach_used_num[mach_deploy] = {}
            mach_used_num[mach_deploy][inst[1]] = 1

        # update accumulated value of mach_used_set
        if mach_deploy in mach_used_set:
            mach_used_set[mach_deploy][1][0] = list_plus(mach_used_set[mach_deploy][1][0], inst[2])
            mach_used_set[mach_deploy][1][1] = list_plus(mach_used_set[mach_deploy][1][1], inst[3])
            mach_used_set[mach_deploy][1][2:] = list_plus(mach_used_set[mach_deploy][1][2:], inst[4:8])
        else:
            mach_used_set[mach_deploy] = [[], []]
            mach_used_set[mach_deploy][0] = mach_set[mach_iter][1:]
            mach_used_set[mach_deploy][1] = inst[2:8]

        # update the new machine
        if mach_name_new in mach_used_set and mach_iter < machine_num - inilen:
            mach_iter += 1
            if mach_iter >= machine_num - inilen:
                print('All machines have been used! We will use the existing machines.')
                # print 'Number of instances assigned: ', ind + 1
                print('We will round back to use the existing machines')

                # break
            else:

                mach_name_new = mach_set[mach_iter][0]

        if list_equal(mach_used_set[mach_deploy][0][:3],
                      [max(mach_used_set[mach_deploy][1][0]), max(mach_used_set[mach_deploy][1][1]),
                       mach_used_set[mach_deploy][1][2]]):
            del mach_used_set[
                mach_deploy]  # if any of max_cpu, max_mem, disk resource is used up, del this mach in mach_used_set

        print(ind + keeplen, mach_iter - 1 + inilen)
        ind += 1
        # if ind>200:
        #     break

    t1 = time.time()
    print('\nTotal elapsed time: ', t1 - t0)

    result1 = []
    for vv in result:
        if vv[0] in move_list:
            result1 = [vv] + result1
        else:
            result1.append(vv)
    run_time = time.strftime("%Y%m%d %H%M%S", time.localtime())
    with open(r'C:\Bee\ProjectFile\Tianchi_scheduling_20180614\results\submit_%s.csv' % run_time, 'wb') as fr:
        writer = csv.writer(fr)
        for v in result1:
            # if v[1] != inst_deploy[v[0]]:
            writer.writerow(v)


def get_score(result_file, data_code, data_date):
    used_mach = {}  # [cpu_t,mem_t,disk,p,m,pm] accumulated
    print('initial deploy number: ', len(deploy_list))
    in_machine = {}  # record those deployed instances, temporarily and permanently
    for v in deploy_list:
        mach = inst_deploy[v][1]
        in_machine[v] = mach
        if mach in used_mach:
            used_mach[mach][0] = list_plus(used_mach[mach][0], inst_dict[v][0])
            used_mach[mach][1] = list_plus(used_mach[mach][1], inst_dict[v][1])
            used_mach[mach][2:] = list_plus(used_mach[mach][2:], inst_dict[v][2:])
        else:
            used_mach[mach] = [0] * 6
            used_mach[mach][0] = inst_dict[v][0]
            used_mach[mach][1] = inst_dict[v][1]
            used_mach[mach][2:] = list(inst_dict[v][2:])
    # used_mach , deploy_list = {}, []

    with open(r'C:\Bee\ProjectFile\Tianchi_scheduling_20180614\results\%s.csv' % result_file, 'rU') as fr:
        reader = csv.reader(fr)
        for v in reader:
            if v[0] in in_machine:
                mach0 = in_machine[v[0]]
                del in_machine[v[0]]
                used_mach[mach0][0] = list_minus(used_mach[mach0][0], inst_dict[v[0]][0])
                used_mach[mach0][1] = list_minus(used_mach[mach0][1], inst_dict[v[0]][1])
                used_mach[mach0][2:] = list_minus(used_mach[mach0][2:], inst_dict[v[0]][2:])
                if used_mach[mach0][2] == 0:
                    del used_mach[mach0]

            in_machine[v[0]] = v[1]

            if v[1] in used_mach:
                used_mach[v[1]][0] = list_plus(used_mach[v[1]][0], inst_dict[v[0]][0])
                used_mach[v[1]][1] = list_plus(used_mach[v[1]][1], inst_dict[v[0]][1])
                used_mach[v[1]][2:] = list_plus(used_mach[v[1]][2:], inst_dict[v[0]][2:])
            else:
                used_mach[v[1]] = [0, 0, 0, 0, 0, 0]
                used_mach[v[1]][0] = inst_dict[v[0]][0]
                used_mach[v[1]][1] = inst_dict[v[0]][1]
                used_mach[v[1]][2:] = list(inst_dict[v[0]][2:])

    score = 0
    for mach in used_mach:
        # obey_ind = True
        if max(used_mach[mach][0]) > mach_dict[mach][0] + 1e-6:
            print('Utilization obeyed: ', mach)
        if max(used_mach[mach][1]) > mach_dict[mach][1] + 1:
            print('Memory obeyed: ', mach)
        if used_mach[mach][2] > mach_dict[mach][2]:
            print('Disk obeyed: ', mach, used_mach[mach][2], mach_dict[mach][2])
        if used_mach[mach][3] > mach_dict[mach][3]:
            print('P obeyed: ', mach)
        if used_mach[mach][4] > mach_dict[mach][4]:
            print('M obeyed: ', mach)
        if used_mach[mach][5] > mach_dict[mach][5]:
            print('PM obeyed: ', mach)

        for cpu in used_mach[mach][0]:
            utilization = cpu / (mach_dict[mach][0] + 0.0) - 0.5
            if utilization <= 0:
                score += 1
            else:
                # print mach
                score += (1 + 10 * (math.e ** utilization - 1))

    print('Total used machine number: ', len(used_mach))
    print('Total scores: ', score / time_num)


def make_adjustment(result_file):
    """this main program is to adjust the submit sequence of instances,
    guarantee that no interference conflict or resource exceeding
    """

    result_dict = {}  # {inst: mach}
    result_list = []  # [inst, mach]  20180711 115130   20180709 052659

    with open(r'C:\Bee\ProjectFile\Tianchi_scheduling_20180614\results\%s.csv' % result_file, 'rU') as fr:
        reader = csv.reader(fr)
        for v in reader:
            if v[0] in inst_deploy and inst_deploy[v[0]][1] == v[1]:
                continue
            else:
                # not include those instances that do not need to be moved
                result_dict[v[0]] = v[1]
                result_list.append(v)

    moving = []  # [inst,initial_mach]
    output1 = []  # first deploy  [inst, new_mach]
    output2 = []  # last deploy
    for v in result_list:
        if v[0] in deploy_list:
            moving.append([v[0], inst_deploy[v[0]][1]])
        else:
            output2.append(v)

    print('moving number: ', len(moving))

    mach_used_num = {}
    mach_used_set = {}  # {mach_name:[[max value],[accumulated value]]}
    # initial setting
    for v in inst_deploy:  # {inst:[app,mach]} 29996
        mach = inst_deploy[v][1]
        app = inst_deploy[v][0]
        if mach in mach_used_num:
            if app in mach_used_num[mach]:
                mach_used_num[mach][app] += 1

            else:
                mach_used_num[mach][app] = 1

            mach_used_set[mach][1][0] = list_plus(mach_used_set[mach][1][0], inst_dict[v][0])
            mach_used_set[mach][1][1] = list_plus(mach_used_set[mach][1][1], inst_dict[v][1])
            mach_used_set[mach][1][2:] = list_plus(mach_used_set[mach][1][2:], inst_dict[v][2:])
        else:
            mach_used_num[mach] = {}
            mach_used_num[mach][app] = 1

            mach_used_set[mach] = [[], []]
            mach_used_set[mach][0] = list(mach_dict[mach])
            mach_used_set[mach][1] = list(inst_dict[v])

    print('initially used machine number: ', len(mach_used_num))

    # adjust manually when problems occur
    # moving_a = []
    # moving_b = []
    # for vv in moving:
    #     if vv[0] in ['inst_45772', 'inst_20232', 'inst_53327']:
    #         moving_a.append(vv)
    #     else:
    #         moving_b.append(vv)
    # moving = moving_a + moving_b

    i = 0
    while len(moving) > 0:
        i += 1
        print(len(moving))
        rem = []  # remaining(need to be moved) instances, [inst,initial_mach]
        ii = 0
        for v in moving:
            ii += 1
            break_ind = False
            # print '%s / %s' % (ii, len(moving))
            inst = v[0]
            app = inst_app[v[0]]
            mach0 = v[1]  # initial machine
            mach1 = result_dict[v[0]]  # move machine
            mach0_ind = int(mach0.strip('machine_'))  # the code of machine

            if violation_check(app, mach1, mach_used_set, mach_used_num, 1., 'max'):
                if mach1 in mach_used_num:
                    output1.append([inst, mach1])

                    # update mach_used_num
                    if app in mach_used_num[mach1]:
                        mach_used_num[mach1][app] += 1
                    else:
                        mach_used_num[mach1][app] = 1

                    # update mach_used_set
                    mach_used_set[mach1][1][0] = list_plus(mach_used_set[mach1][1][0], inst_dict[inst][0])
                    mach_used_set[mach1][1][1] = list_plus(mach_used_set[mach1][1][1], inst_dict[inst][1])
                    mach_used_set[mach1][1][2:] = list_plus(mach_used_set[mach1][1][2:], inst_dict[inst][2:])

                else:
                    output1.append([inst, mach1])
                    # first_inst.append(v[0])
                    mach_used_num[mach1] = {}
                    mach_used_num[mach1][app] = 1

                    mach_used_set[mach1] = [[], []]
                    mach_used_set[mach1][0] = list(mach_dict[mach1])
                    mach_used_set[mach1][1] = list(inst_dict[inst])

            else:
                # print 'moving to a machine temporarily: ', inst, app, mach_used_num[mach1]
                while not violation_check(app, mach1, mach_used_set, mach_used_num, 1., 'max'):
                    if mach0_ind < 6000:
                        mach0_ind += 1
                    else:
                        mach0_ind = 1

                    mach1 = 'machine_' + str(mach0_ind)

                    if mach1 == mach0:
                        print('Checked one round. Cannot put in, please put it at the beginning !!!!!', inst, app,
                              mach1)
                        rem.append([inst, mach0])
                        break_ind = True
                        break
                if break_ind:  # problems occur
                    continue
                output1.append([inst, mach1])
                rem.append([inst, mach1])

                # update mach_used_num
                if mach1 not in mach_used_num:
                    mach_used_num[mach1] = {}

                if app in mach_used_num[mach1]:
                    mach_used_num[mach1][app] += 1
                else:
                    mach_used_num[mach1][app] = 1

                # update mach_used_set
                if mach1 in mach_used_set:
                    mach_used_set[mach1][1][0] = list_plus(mach_used_set[mach1][1][0], inst_dict[inst][0])
                    mach_used_set[mach1][1][1] = list_plus(mach_used_set[mach1][1][1], inst_dict[inst][1])
                    mach_used_set[mach1][1][2:] = list_plus(mach_used_set[mach1][1][2:], inst_dict[inst][2:])
                else:
                    mach_used_set[mach1] = [[], []]
                    mach_used_set[mach1][0] = list(mach_dict[mach1])
                    mach_used_set[mach1][1] = list(inst_dict[inst])

            # update the initial machine attributes since the instance will be moved
            if app not in mach_used_num[mach0]:
                print('fuck!!!', inst, app, mach0, mach1)
            mach_used_num[mach0][app] -= 1
            if mach_used_num[mach0][app] == 0:
                del mach_used_num[mach0][app]
            if mach_used_num[mach0] == {}:
                del mach_used_num[mach0]
            mach_used_set[mach0][1][0] = list_minus(mach_used_set[mach0][1][0], inst_dict[inst][0])
            mach_used_set[mach0][1][1] = list_minus(mach_used_set[mach0][1][1], inst_dict[inst][1])
            mach_used_set[mach0][1][2:] = list_minus(mach_used_set[mach0][1][2:], inst_dict[inst][2:])
            if mach_used_set[mach0][1][2] == 0:
                del mach_used_set[mach0]

        moving = rem
        # print moving

    output = output1 + output2
    print('Number of times to be moved or deployed: ', len(output))
    # run_time = time.strftime("%Y%m%d %H%M%S", time.localtime())
    adjust_file = result_file.strip('need_adjust_improve')
    with open(r'C:\Bee\ProjectFile\Tianchi_scheduling_20180614\results\%sadjust_%s.csv' % (data_code, result_file),
              'wb') as fr:
        writer = csv.writer(fr)
        for v in output:
            writer.writerow(v)


def combine(result_a, result_b):
    result = []
    with open(r'C:\Bee\ProjectFile\Tianchi_scheduling_20180614\results\%s.csv' % result_a, 'rU') as fa:
        reader = csv.reader(fa)
        for v in reader:
            result.append(v)
    result.append(['#'])
    with open(r'C:\Bee\ProjectFile\Tianchi_scheduling_20180614\results\%s.csv' % result_b, 'rU') as fb:
        reader = csv.reader(fb)
        for w in reader:
            result.append(w)

    run_time = time.strftime("%Y%m%d %H%M%S", time.localtime())
    with open(r'C:\Bee\ProjectFile\Tianchi_scheduling_20180614\results\data_ab\submit_%s.csv' % run_time, 'wb') as fw:
        writer = csv.writer(fw)
        for row in result:
            writer.writerow(row)


combine('submit_last_resul', 'b_submit_20180730 042136')

if __name__ == '__main__':
    # data_code = 'b_'
    # data_date = '20180726'
    data_code = ''
    data_date = '20180606'
    print('We are running data: %s' % (data_code + data_date))
    thres = 0.5
    cpu_mode = 'max'
    print('CPU mode is %s, and threshold is %f' % (cpu_mode, thres))

    app_num = 9338
    machine_num = 6000
    time_num = 98
    inst_set, inst_dict, inst_app, inst_deploy, deploy_list, mach_set, mach_dict, app_dict, intfer_dict = read_data(
        data_code, data_date)
    # inst_set=[inst1,inst2,...]  # inst1: [inst_name,app_name,cpu_t,mem_t,disk,p,m,pm,app_score]
    # mach_set = [mach1,mach2,...]  # mach1: [mach_name,cpu,mem,disk,p,m,pm]
    # app_dict = {app1:[cpu_t,mem_t,disk,p,m,pm]}

    inst_set1 = []  # inst of app 1-4669
    inst_set2 = []  # inst of app 4670-9338
    mach_set1 = []  # 1500 small machine and 1500 large machine
    mach_set2 = []  # 1500 small machine and 1500 large machine

    for v in inst_set:
        app_ind = int(v[1].strip('app_')) - 1
        if app_ind < 2000:
            inst_set1.append(v)
        else:
            inst_set2.append(v)
    for i, w in enumerate(mach_set):
        if i < 1200:
            mach_set1.append(w)
        else:
            mach_set2.append(w)

    machine_num = len(mach_set1)
    inst_num = len(inst_set1)
    print('instance number: ', inst_num)
    print('machine number: ', machine_num)

    # keep_initial(thres)

    # reconstruction(thres, inst_set1, mach_set1)

    # get_score(result_file='b_submit_20180730 042136', data_code=data_code, data_date=data_date)

    make_adjustment('rs_data_a_20180810')

if __name__ == '__mai__':
    '''checking the result'''
    import copy

    inst_set, inst_dict, inst_app, inst_deploy, deploy_list, mach_set, mach_dict, app_dict, intfer_dict = read_data()

    result_dict = {}  # {inst:mach}
    result_list = []  # [inst,mach]  20180711 115130   20180709 052659
    with open(r'C:\Bee\ProjectFile\Tianchi_scheduling_20180614\results\submit_%s.csv' % '20180716 142656', 'rU') as fr:
        reader = csv.reader(fr)
        for v in reader:
            result_dict[v[0]] = v[1]
            result_list.append(v)
    print('total: ', len(result_list))
    mach_used_num = {}
    mach_used_set = {}
    for v in inst_deploy:  # {inst:[app,mach]} 29996

        mach = inst_deploy[v][1]
        app = inst_deploy[v][0]
        if mach in mach_used_num:
            if app in mach_used_num[mach]:
                mach_used_num[mach][app] += 1

            else:
                mach_used_num[mach][app] = 1

            mach_used_set[mach][1][0] = list_plus(mach_used_set[mach][1][0], inst_dict[v][0])
            mach_used_set[mach][1][1] = list_plus(mach_used_set[mach][1][1], inst_dict[v][1])
            mach_used_set[mach][1][2:] = list_plus(mach_used_set[mach][1][2:], inst_dict[v][2:])
        else:
            mach_used_num[mach] = {}
            mach_used_num[mach][app] = 1

            mach_used_set[mach] = [[], []]
            mach_used_set[mach][0] = list(mach_dict[mach])
            mach_used_set[mach][1] = list(inst_dict[v])

    print('initially used machine number: ', len(mach_used_num))

    output = []
    i = 0
    for v in result_list:
        i += 1
        inst = v[0]
        app = inst_app[inst]
        mach1 = v[1]

        if inst in inst_deploy:
            mach0 = inst_deploy[inst][1]

            if mach1 in mach_used_num:
                if violation_check0(app, mach1):
                    # if interference_assess(mach_used_num[mach1], app):
                    output.append([inst, mach1])
                    # first_inst.append(v[0])
                    if app in mach_used_num[mach1]:
                        mach_used_num[mach1][app] += 1
                    else:
                        mach_used_num[mach1][app] = 1

                    mach_used_num[mach0][app] -= 1
                    if mach_used_num[mach0][app] == 0:
                        del mach_used_num[mach0][app]
                    if mach_used_num[mach0] == {}:
                        del mach_used_num[mach0]

                    # update mach_used_set
                    mach_used_set[mach1][1][0] = list_plus(mach_used_set[mach1][1][0], inst_dict[inst][0])
                    mach_used_set[mach1][1][1] = list_plus(mach_used_set[mach1][1][1], inst_dict[inst][1])
                    mach_used_set[mach1][1][2:] = list_plus(mach_used_set[mach1][1][2:], inst_dict[inst][2:])

                    mach_used_set[mach0][1][0] = list_minus(mach_used_set[mach0][1][0], inst_dict[inst][0])
                    mach_used_set[mach0][1][1] = list_minus(mach_used_set[mach0][1][1], inst_dict[inst][1])
                    mach_used_set[mach0][1][2:] = list_minus(mach_used_set[mach0][1][2:], inst_dict[inst][2:])


                else:
                    print('wrong: ', i, inst, app, mach1, mach_used_num[mach1])
                    print('inst info:', inst_dict[inst])
                    print('acuum info: ', mach_used_set[mach1][1][0])
                    break

            else:
                output.append([v[0], mach1])
                # first_inst.append(v[0])
                mach_used_num[mach1] = {}
                mach_used_num[mach1][app] = 1

                mach_used_num[mach0][app] -= 1
                if mach_used_num[mach0][app] == 0:
                    del mach_used_num[mach0][app]
                if mach_used_num[mach0] == {}:
                    del mach_used_num[mach0]

                # update mach_used_set
                mach_used_set[mach1] = [[], []]
                mach_used_set[mach1][0] = list(mach_dict[mach1])
                mach_used_set[mach1][1] = list(app_dict[app])

                mach_used_set[mach0][1][0] = list_minus(mach_used_set[mach0][1][0], inst_dict[inst][0])
                mach_used_set[mach0][1][1] = list_minus(mach_used_set[mach0][1][1], inst_dict[inst][1])
                mach_used_set[mach0][1][2:] = list_minus(mach_used_set[mach0][1][2:], inst_dict[inst][2:])

        else:
            if mach1 in mach_used_num:
                if violation_check0(app, mach1):
                    # if interference_assess(mach_used_num[mach1], app):
                    output.append([inst, mach1])
                    # first_inst.append(v[0])
                    if app in mach_used_num[mach1]:
                        mach_used_num[mach1][app] += 1
                    else:
                        mach_used_num[mach1][app] = 1

                    # update mach_used_set
                    mach_used_set[mach1][1][0] = list_plus(mach_used_set[mach1][1][0], inst_dict[inst][0])
                    mach_used_set[mach1][1][1] = list_plus(mach_used_set[mach1][1][1], inst_dict[inst][1])
                    mach_used_set[mach1][1][2:] = list_plus(mach_used_set[mach1][1][2:], inst_dict[inst][2:])


                else:
                    print('wrong: ', i, inst, app, mach1, mach_used_num[mach1])
                    print('inst info:', inst_dict[inst])
                    print('acuum info: ', mach_used_set[mach1][1][0])
                    break

            else:
                output.append([v[0], mach1])
                # first_inst.append(v[0])
                mach_used_num[mach1] = {}
                mach_used_num[mach1][app] = 1

                # update mach_used_set
                mach_used_set[mach1] = [[], []]
                mach_used_set[mach1][0] = list(mach_dict[mach1])
                mach_used_set[mach1][1] = list(inst_dict[inst])

    print('total output: ', len(output))
