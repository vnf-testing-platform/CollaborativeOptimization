from django.shortcuts import render, HttpResponseRedirect, HttpResponse
import json
import pickle
import csv
import os
import uuid
import time
import datetime
import pytz
from sklearn.svm import SVC
from sklearn.neighbors import KNeighborsClassifier
from sklearn.gaussian_process import GaussianProcessClassifier
from sklearn.gaussian_process.kernels import RBF
from sklearn.tree import DecisionTreeClassifier
from sklearn.neural_network import MLPClassifier
from sklearn.ensemble import RandomForestClassifier, AdaBoostClassifier
from sklearn.naive_bayes import GaussianNB
from sklearn.discriminant_analysis import QuadraticDiscriminantAnalysis

from cosite.models import DetectedParams, PPPoESessionTest, UserTransTest, MultiTest, Log, FinalResult, CPUMemory, TestCaseState
from influxdb import InfluxDBClient


def index(req):
    if req.path == '/':
        return HttpResponseRedirect('/co/')
    return render(req, 'cosite/index.html')


def data_query(req):
    return render(req, 'cosite/show_Task.html')


def data_show(req):
    return render(req, 'cosite/show_VNF.html')


def user_profile(req):
    return render(req, 'cosite/user_profile.html')


def pages_sign_in(req):
    return render(req, 'cosite/pages_sign-in.html')


def pages_forgot_password(req):
    return render(req, 'cosite/pages_forgot-password.html')


def pages_lock_screen(req):
    return render(req, 'cosite/pages_lock-screen.html')


def report_session(req):
    return render(req, 'cosite/report_vBRAS_session.html')


def report_frame(req):
    return render(req, 'cosite/report_vBRAS_frame.html')


def report_multi(req):
    return render(req, 'cosite/report_vBRAS_multi.html')


def api4get_data(req):
    if req.method == 'GET':
        needed_params = req.GET.getlist('selectedParams[]')
        items = DetectedParams.objects \
            .only('add_time', *needed_params) \
            .filter(add_time__gt=req.GET.get('timeBegin'),
                    add_time__lt=req.GET.get('timeEnd')).all()

        # test add model to MultiTest table --> success execute!!!
        # mt = MultiTest()
        # mt.task_id = uuid.uuid1()
        # mt.cpu = 0.99
        # mt.memory = 0.88
        # mt.add_time = time.strftime('%Y-%m-%d %H:%M:%S',time.localtime(time.time()))
        # mt.save()

        result = []
        for item in items:
            rst = {}
            for param in needed_params:
                rst[param] = getattr(item, param)
            rst['add_time'] = item.add_time.strftime('%Y-%m-%d %H:%M:%S')
            result.append(rst)
        return HttpResponse(json.dumps(result), content_type='text/json')
    return HttpResponse('Permission denied!', status=403)

# 初始化支持向量机
classifiers = {"Nearest Neighbors": KNeighborsClassifier(3),
               "Linear SVM": SVC(kernel="linear", C=0.025),
               "RBF SVM": SVC(gamma=2, C=1),
               "Gaussian Process": GaussianProcessClassifier(1.0 * RBF(1.0), warm_start=True),
               "Decision Tree": DecisionTreeClassifier(max_depth=5),
               "Random Forest": RandomForestClassifier(max_depth=5, n_estimators=10, max_features=1),
               "Neural Net": MLPClassifier(alpha=1),
               "AdaBoost": AdaBoostClassifier(),
               "Naive Bayes": GaussianNB(),
               "QDA": QuadraticDiscriminantAnalysis()}
property_params = ['ave_anneal_soak_t',
                   'ave_anneal_rapid_cool_outlet_t',
                   'ave_anneal_slow_cool_outlet_t',
                   'pc', 'pmn', 'pp', 'ps',
                   'finishing_inlet_t', 'finishing_outlet_t', 'coiling_t']
property_max_min = {'ave_anneal_soak_t': [854.9, 797.6],
                    'ave_anneal_rapid_cool_outlet_t': [455.7, 398.6],
                    'ave_anneal_slow_cool_outlet_t': [665.4, 614.9],
                    'pc': [0.0025, 0.0011],
                    'pmn': [0.16, 0.1],
                    'pp': [0.014, 0.007],
                    'ps': [0.0139, 0.0024],
                    'finishing_inlet_t': [1076.4, 1014.1],
                    'finishing_outlet_t': [927.2, 912.5],
                    'coiling_t': [753.4, 654.5]}
origin_data = pickle.load(open('data.pkl', 'rb'))


def api4get_exception(req):
    if req.method == 'GET':
        needed_params = req.GET.getlist('selectedParams[]')
        items = DetectedParams.objects.filter(add_time__gt=req.GET.get('timeBegin'),
                                              add_time__lt=req.GET.get('timeEnd')).all()[:50]
        # unpredicted_items = []
        # for item in items:
        #     if item.label == 0:
        #         unpredicted_items.append(item)
        test_data = []
        # for item in unpredicted_items:
        for item in items:
            data = []
            for param in property_params:
                data.append(getattr(item, param))
            test_data.append(data)

        clf = classifiers[req.GET.get('algorithm')]
        clf.fit(origin_data['train_data'], origin_data['target_data'])
        test_result = clf.predict(test_data) if len(test_data) > 0 else []
        # test_result = [result.item() for result in test_result]

        # for i in range(len(unpredicted_items)):
        #     if test_result[i] != unpredicted_items[i].label:
        #         unpredicted_items[i].label = test_result[i]
        #         unpredicted_items[i].save()
        # for i in range(len(items)):
        #     if test_result[i] != items[i].label:
        #         items[i].label = test_result[i]
        #         items[i].save()

        result = []
        for i in range(len(items)):
            rst = {}
            for param in needed_params:
                rst[param] = getattr(items[i], param)
            rst['add_time'] = items[i].add_time.strftime('%Y-%m-%d %H:%M:%S')
            rst['label'] = test_result[i].item()
            result.append(rst)
        return HttpResponse(json.dumps([result, property_max_min]), content_type='text/json')
    return HttpResponse('Permission denied!', status=403)


def api4get_correlation(req):
    if req.method == 'GET':
        needed_params = req.GET.getlist('selectedParams[]')
        items = DetectedParams.objects \
            .only('add_time', *needed_params) \
            .filter(add_time__gt=req.GET.get('timeBegin'),
                    add_time__lt=req.GET.get('timeEnd')).all()
        data = []
        for i in range(len(needed_params)):
            data.append([])
            for item in items:
                data[i].append(getattr(item, needed_params[i]))

        cnf = gra(data[0], data[1:])
        result = {needed_params[0]: 1}
        for i in range(1, len(needed_params)):
            result[needed_params[i]] = cnf[i]
        return HttpResponse(json.dumps(result), content_type='text/json')
    return HttpResponse('Permission denied!', status=403)


def gra(ref, origin_des):
    ref_0 = ref[0]
    des = [[cell for cell in row] for row in origin_des]
    ref = list(map(lambda x: x / ref_0, ref))
    for i in range(len(des)):
        for j in range(len(des[0])):

            des[i][j] = abs(origin_des[i][j] / origin_des[i][0] - ref[j])
    des_max = max(list(map(max, des)))
    result = []
    for row in des:
        des_sum = 0
        for cell in row:
            des_sum += (0.5 * des_max) / (cell + 0.5 * des_max)
        result.append(des_sum / len(des[0]))
    result.insert(0, 1)
    return result


# test
def api4_test(req):
    if req.method == 'POST':
        temp = req.POST
        print(temp)
        d = json.loads(req.body.decode('utf-8'))
        scripttype = d.get('scripttype')
        serverIp = d.get('serverIp')
        testcase = d.get('testcase')
        testcasenum=testcase['script'][0]['file']
        taskId = d.get('taskId')
        device = d.get('device')
        parameter = d.get('parameter')
        clientnum=parameter['PPPoEClientNum']
        porttype=parameter['porttype']

        # 获取ip地址
        # print('========')
        # x_forwarded_for = req.META.get('HTTP_X_FORWARDED_FOR')
        # if x_forwarded_for:
        #     ip = x_forwarded_for.split(',')[-1].strip()
        # else:
        #     ip = req.META.get('REMOTE_ADDR')
        #
        # print(x_forwarded_for)
        # print(ip)
        # print('========')

        print(scripttype)
        print(serverIp)
        print(testcase)
        print(testcasenum)
        print(taskId)
        print(device)
        print(parameter)
        print(clientnum)
        print(porttype)

        data = {'stepId': 1, 'log': 'Fail', 'execteIndex': '1', 'testcaseId': '114', 'reslt': 1, 'taskId': '243d8bd5-15fa-48b1-b9c8-d19a2f7b7338','testresult':''}

        # 从数据库取数据开始
        # dp = DetectedParams.objects.first()
        # data={'id': dp.id, 'label': dp.label}
        # 取数据结束

        return HttpResponse(json.dumps(data), content_type='application/json')
    return HttpResponse('Permission denied!', status=403)


def api4_test2(req):
    if req.method == 'GET':
        temp = req.GET
        print(temp)

        b = json.loads(req.GET.get('b'))
        c = b['d']['e']
        print(b)
        print(c)

        d = json.loads(req.GET.get('testcase'))
        d['script'][0]['id']

        return HttpResponse('success')
        # return HttpResponse('ok')
    return HttpResponse('Permission denied!', status=403)


# VNF_1_Concurrent_Session_Capacity
# 获取到前台发送的指令，主要是为生成uuid后返回给前台
def api4_vnf1_uuid(req):
    if req.method == 'POST':
        # temp = req.POST
        # print(temp)

        d = json.loads(req.body.decode('utf-8'))
        beginflag = d.get('begin')
        if beginflag == 1:
            taskid = uuid.uuid1()
            taskid = str(taskid)

        obj = TestCaseState()
        obj.task_id = taskid
        obj.set_session = d.get('set_session')
        obj.set_flow = d.get('set_flow')
        obj.current_state = True
        # mt.add_time = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time()))
        # obj.add_time = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time()))
        obj.type_name = 'VNF_1_Concurrent_Session_Capacity'
        obj.save()

        # pst = PPPoESessionTest()
        # pst.task_id = taskid
        # pst.save()
        # 删除测试条目
        # PPPoESessionTest.objects.filter(task_id='6d306a8a-402f-11e7-a90f-ac728980a78b').delete()
        data = {'taskId': taskid}
        return HttpResponse(json.dumps(data), content_type='application/json')
    return HttpResponse('Permission denied!', status=403)


# VNF_1_Concurrent_Session_Capacity
# 接受iTest返回的结果，并将结果存入数据库
def api4_vnf1_itest(req):
    if req.method == 'POST':
        # temp = req.POST
        # print(temp)
        d = json.loads(req.body.decode('utf-8'))

        # taskId = d.get('taskId')

        # obj = PPPoESessionTest.objects.get(task_id=taskId)
        # obj.session_num = '10000'
        # obj.add_time = '19901108'
        # obj.save()

        # print(obj.session_num)

        obj = PPPoESessionTest()
        obj.task_id = d.get('taskId')

        result = d.get('testresult')
        obj.session_num = result['session_num']
        obj.add_time = result['add_time']
        obj.connect_rate = result['connect_rate']

        if PPPoESessionTest.objects.all().last():
            if PPPoESessionTest.objects.all().last().add_time != result['add_time']:
                obj.save()
        else:
            obj.save()

        print(d)

        data = {'log': 'test'}
        return HttpResponse(json.dumps(data), content_type='application/json')
    return HttpResponse('Permission denied!', status=403)


# VNF_2_VBRAS_Client_Forwarding_Performance
# 获取到前台发送的指令，主要是为生成uuid后返回给前台
def api4_vnf2_uuid(req):
    if req.method == 'POST':
        # temp = req.POST
        # print(temp)

        d = json.loads(req.body.decode('utf-8'))
        beginflag = d.get('begin')
        if beginflag == 1:
            taskid = uuid.uuid1()
            taskid = str(taskid)

        obj = TestCaseState()
        obj.task_id = taskid
        obj.set_session = d.get('set_session')
        obj.set_flow = d.get('set_flow')
        obj.current_state = True
        # mt.add_time = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time()))
        # obj.add_time = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time()))
        obj.type_name = 'VNF_2_VBRAS_Client_Forwarding_Performance'
        obj.save()

        # pst = UserTransTest()
        # pst.task_id = taskid
        # pst.save()
        # 删除测试条目
        # PPPoESessionTest.objects.filter(task_id='6d306a8a-402f-11e7-a90f-ac728980a78b').delete()
        data = {'taskId': taskid}
        return HttpResponse(json.dumps(data), content_type='application/json')
    return HttpResponse('Permission denied!', status=403)


# VNF_2_VBRAS_Client_Forwarding_Performance
# 接受iTest返回的结果，并将结果存入数据库
def api4_vnf2_itest(req):
    if req.method == 'POST':
        # temp = req.POST
        # print(temp)
        d = json.loads(req.body.decode('utf-8'))

        # taskId = d.get('taskId')

        # obj = PPPoESessionTest.objects.get(task_id=taskId)
        # obj.session_num = '10000'
        # obj.add_time = '19901108'
        # obj.save()

        # print(obj.session_num)

        obj = UserTransTest()
        obj.task_id = d.get('taskId')
        result = d.get('testresult')
        obj.frame_size = result['frame_size']
        obj.min_latency = result['min_latency']
        obj.max_latency = result['max_latency']
        obj.avg_latency = result['avg_latency']
        obj.add_time = result['add_time']
        obj.rx_rate = result['rx_rate']
        # print(UserTransTest.objects.all()[-1]['add_time'])
        if PPPoESessionTest.objects.all().last():
            if PPPoESessionTest.objects.all().last().add_time != result['add_time']:
                obj.save()
        else:
            obj.save()

        data = {'log': 'test'}
        return HttpResponse(json.dumps(data), content_type='application/json')
    return HttpResponse('Permission denied!', status=403)


# VNF_3_PPPoE_IPTV_IPoE_VoIP
# 获取到前台发送的指令，主要是为生成uuid后返回给前台
def api4_vnf3_uuid(req):
    if req.method == 'POST':
        # temp = req.POST
        # print(temp)

        d = json.loads(req.body.decode('utf-8'))
        beginflag = d.get('begin')
        if beginflag == 1:
            taskid = uuid.uuid1()
            taskid = str(taskid)

        obj = TestCaseState()
        obj.task_id = taskid
        obj.set_session = d.get('set_session')
        obj.set_flow = d.get('set_flow')
        obj.current_state = True

        # obj.add_time = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time()))
        obj.type_name = 'VNF_3_PPPoE_IPTV_IPoE_VoIP'
        obj.save()

        # pst = MultiTest()
        # pst.task_id = taskid
        # pst.save()
        # 删除测试条目
        # PPPoESessionTest.objects.filter(task_id='6d306a8a-402f-11e7-a90f-ac728980a78b').delete()
        data = {'taskId': taskid}
        return HttpResponse(json.dumps(data), content_type='application/json')
    return HttpResponse('Permission denied!', status=403)


# VNF_3_PPPoE_IPTV_IPoE_VoIP
# 接受iTest返回的结果，并将结果存入数据库
def api4_vnf3_itest(req):
    if req.method == 'POST':
        # temp = req.POST
        # print(temp)
        d = json.loads(req.body.decode('utf-8'))

        # taskId = d.get('taskId')

        # obj = PPPoESessionTest.objects.get(task_id=taskId)
        # obj.session_num = '10000'
        # obj.add_time = '19901108'
        # obj.save()

        # print(obj.session_num)

        obj = MultiTest()
        obj.task_id = d.get('taskId')
        result = d.get('testresult')

        obj.min_latency = result['min_latency']
        obj.max_latency = result['max_latency']
        obj.avg_latency = result['avg_latency']
        obj.frame_size = result['frame_size']
        obj.tx_rate = result['tx_rate']
        obj.rx_rate = result['rx_rate']
        obj.session_num = result['session_num']
        obj.connect_rate = result['connect_rate']
        obj.add_time = result['add_time']
        if PPPoESessionTest.objects.all().last():
            if PPPoESessionTest.objects.all().last().add_time != result['add_time']:
                obj.save()
        else:
            obj.save()

        data = {'log': 'test'}
        return HttpResponse(json.dumps(data), content_type='application/json')
    return HttpResponse('Permission denied!', status=403)


# 接收log并保存至数据库
def api4_log(req):
    if req.method == 'POST':
        # temp = req.POST
        # print(temp)
        d = json.loads(req.body.decode('utf-8'))

        obj = Log()
        obj.task_id = d.get('taskId')
        obj.log = d.get('log')
        obj.add_time = d.get('add_time')

        obj.save()

        data = {'log': 'test'}
        return HttpResponse(json.dumps(data), content_type='application/json')
    return HttpResponse('Permission denied!', status=403)


# 接收log并保存至数据库
def api4_final_result(req):
    if req.method == 'POST':
        # temp = req.POST
        # print(temp)
        d = json.loads(req.body.decode('utf-8'))

        obj = FinalResult()
        obj.task_id = d.get('taskId')
        obj.final_result = d.get('final_result')
        obj.add_time = d.get('add_time')
        obj.save()

        cur_obj = TestCaseState.objects.get(current_state=True)
        cur_obj.current_state = False
        cur_obj.save()

        data = {'log': 'test'}
        return HttpResponse(json.dumps(data), content_type='application/json')
    return HttpResponse('Permission denied!', status=403)


# 停止测试
def api4_stop_task(req):
    if req.method == 'POST':
        # temp = req.POST
        # print(temp)
        d = json.loads(req.body.decode('utf-8'))
        print(d)
        # task_id = d.get('taskID')
        stop_flag = d.get('stop')

        if stop_flag == 1:
            current_task = TestCaseState.objects.get(current_state=True)
            current_task.current_state = False
            current_task.save()
            data = {'current_state': current_task.current_state, 'task_id': str(current_task.task_id)}
        else:
            data = {'current_state': None, 'task_id': None}
        return HttpResponse(json.dumps(data), content_type='application/json')
    return HttpResponse('Permission denied!', status=403)


# 判断是否存在正在运行的测试用例
def api4_if_exist_current_task(req):
    if req.method == 'POST':
        d = json.loads(req.body.decode('utf-8'))
        print(d)

        obj = TestCaseState.objects.get(current_state=True)

        if obj:
            data = {'taskid': str(obj.task_id), 'tasktype': obj.type_name}
        else:
            data = {'taskid': 0}

        # data = {'taskid': '0e4bd490-4676-11e7-af39-ac728980a78b', 'tasktype': 'VNF_1_Concurrent_Session_Capacity'}
        # data = {'taskid': '0e4bd490-4676-11e7-af39-ac728980a78b',
        #           'tasktype': 'VNF_2_VBRAS_Client_Forwarding_Performance'}
        # data = {'taskid': '0e4bd490-4676-11e7-af39-ac728980a78b', 'tasktype': 'VNF_3_PPPoE_IPTV_IPoE_VoIP'}

        return HttpResponse(json.dumps(data), content_type='application/json')
        # return HttpResponse(json.dumps(data), content_type='application/json')
    return HttpResponse('Permission denied!', status=403)


# index页面获取到CPU和memory的最新值，并保存，无返回
def api4_save_cpu_memory(req):
    if req.method == 'POST':
        d = json.loads(req.body.decode('utf-8'))
        print(d)
        task_id = d.get('taskid')

        client = InfluxDBClient('172.16.110.251', 8086, 'root', '', 'metrics')
        result_mea = client.query('show measurements;')
        print("Result:{0}".format(result_mea))
        # 显示measurements中的libvirt_domain_metrics的最新的一条数据,返回ResultSet
        result = client.query(
            'select "cpu_time_pct","mem_unused","time" from "libvirt_domain_metrics" where time>now() - 1s limit 1')
        # 返回list
        result_point = list(result.get_points(measurement='libvirt_domain_metrics'))
        print(result_point[0])  # 输出一个dict结构的字段
        print('======输出CPU利用率======')
        cpu_value = result_point[0]['cpu_time_pct']
        print(cpu_value)
        print('======输出Memory利用率======')
        mem_value = result_point[0]['mem_unused']
        print(mem_value)
        print('======输出时间戳======')
        time_value = result_point[0]['time']
        print(time_value)

        # 获取到的最新一条记录存入数据库
        new_obj = CPUMemory()
        new_obj.task_id = task_id
        new_obj.cpu = cpu_value
        new_obj.memory = mem_value
        # new_obj.add_time = time_value
        time_temp = utc_to_local(time_value.split('.')[0] + 'Z') + int(time_value.split('.')[0].split(':')[2])
        new_obj.add_time = time_temp
        new_obj.save()

        data = {}

        return HttpResponse(json.dumps(data), content_type='application/json')
    return HttpResponse('Permission denied!', status=403)


# index页面第一个图结果返回，vBRAS CPU利用率【已提供测试数据】
def api4_get_index_cpu(req):
    if req.method == 'POST':
        d = json.loads(req.body.decode('utf-8'))
        print(d)
        flag = d.get('flag')
        taskid = d.get('taskid')

        # 测试数据
        # if flag == 1:
        #     data = [{'add_time': '10:00', 'cpu': 0.3},
        #             {'add_time': '10:05', 'cpu': 2},
        #             {'add_time': '10:10', 'cpu': 3}]

        # 待测试代码
        data = []
        if flag == 1:
            items = CPUMemory.objects.filter(task_id=taskid).all()
            for item in items:
                rst = {}
                rst['add_time'] = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(item.add_time))
                rst['cpu'] = item.cpu
                data.append(rst)

        return HttpResponse(json.dumps(data), content_type='application/json')
    return HttpResponse('Permission denied!', status=403)


# index页面第一个图结果返回，vBRAS Memory利用率【已提供测试数据】
def api4_get_index_memory(req):
    if req.method == 'POST':

        d = json.loads(req.body.decode('utf-8'))
        print(d)
        flag = d.get('flag')
        task_id = d.get('taskid')

        # 测试数据
        # if flag == 1:
        #     data = [{'add_time': '10:00', 'memory': 0.5},
        #             {'add_time': '10:05', 'memory': 3},
        #             {'add_time': '10:10', 'memory': 5}]

        # 待测试代码
        data = []
        if flag == 1:
            items = CPUMemory.objects.filter(task_id=task_id).all()
            for item in items:
                rst = {}
                rst['add_time'] = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(item.add_time))
                rst['cpu'] = item.cpu
                data.append(rst)

        return HttpResponse(json.dumps(data), content_type='application/json')
    return HttpResponse('Permission denied!', status=403)


# index页面右侧的测试用例运行详情【已提供测试数据】
def api4_index_task_details(req):
    if req.method == 'POST':
        d = json.loads(req.body.decode('utf-8'))
        print(d)

        taskid = d.get('taskid')
        tasktype = d.get('tasktype')
        begin_time = TestCaseState.objects.get(task_id=taskid).add_time.strftime('%Y-%m-%d %H:%M:%S')
        current_session = PPPoESessionTest.objects.filter(task_id=taskid).last().session_num
        set_session = TestCaseState.objects.get(task_id=taskid).set_session

        if tasktype == '1':
            # 待测代码
            data = {'set_session': set_session, 'current_session': current_session, 'begin_time': begin_time}
            # 测试数据
            # data = {'set_session': 10000, 'current_session': 8000, 'begin_time': '2017-06-06 10:00'}

        elif tasktype == '2':
            # 待测代码
            obj = UserTransTest.objects.filter(task_id=taskid)

            obj_64 = obj.filter(frame_size=64).last()
            if obj_64:
                frame_size_64 = obj_64.avg_latency
            else:
                frame_size_64 = None

            obj_128 = obj.filter(frame_size=128).last()
            if obj_128:
                frame_size_128 = obj_128.avg_latency
            else:
                frame_size_128 = None

            obj_256 = obj.filter(frame_size=256).last()
            if obj_256:
                frame_size_256 = obj_256.avg_latency
            else:
                frame_size_256 = None

            obj_512 = obj.filter(frame_size=512).last()
            if obj_512:
                frame_size_512 = obj_512.avg_latency
            else:
                frame_size_512 = None

            obj_1024 = obj.filter(frame_size=1024).last()
            if obj_1024:
                frame_size_1024 = obj_1024.avg_latency
            else:
                frame_size_1024 = None

            obj_1280 = obj.filter(frame_size=1280).last()
            if obj_1280:
                frame_size_1280 = obj_1280.avg_latency
            else:
                frame_size_1280 = None

            obj_1518 = obj.filter(frame_size=1518).last()
            if obj_1518:
                frame_size_1518 = obj_1518.avg_latency
            else:
                frame_size_1518 = None

            data = {'set_session': set_session, 'current_session': current_session,
                    'frame_size_64': frame_size_64, 'frame_size_128': frame_size_128,
                    'frame_size_256': frame_size_256, 'frame_size_512': frame_size_512,
                    'frame_size_1024': frame_size_1024, 'frame_size_1280': frame_size_1280,
                    'frame_size_1518': frame_size_1518, 'begin_time': begin_time}

            # 测试数据
            # data = {'set_session': 10000, 'current_session': 7000,
            #         'frame_size_64': 100, 'frame_size_128': 80, 'frame_size_256': 30,
            #         'frame_size_512': 23, 'frame_size_1024': 55,
            #         'frame_size_1280': 45,
            #         'frame_size_1518': 33, 'begin_time': '2017-06-07 10:10'}

        elif tasktype == '3':
            # 待测代码
            data = {'set_session': set_session, 'current_session': current_session, 'begin_time': begin_time}

            # 测试数据
            # data = {'set_session': 20000, 'current_session': 12000, 'begin_time': '2017-06-07 10:15'}
        else:
            data = []

        return HttpResponse(json.dumps(data), content_type='application/json')
    return HttpResponse('Permission denied!', status=403)


# 下拉菜单中展示所有的task列表【已提供测试数据】
def api4_history_task_list(req):
    if req.method == 'POST':

        d = json.loads(req.body.decode('utf-8'))
        print(d)

        # 测试数据
        # result = [{'add_time': '2017-05-01 10:00', 'task_id': '0e4bd490-4676-11e7-af39-ac728980a78b',
        #            'type_name': 'VNF_1_Concurrent_Session_Capacity'},
        #           {'add_time': '2017-05-02 11:00', 'task_id': '5db8b1c2-4677-11e7-b6f4-ac728980a78b',
        #            'type_name': 'VNF_2_VBRAS_Client_Forwarding_Performance'},
        #           {'add_time': '2017-06-01 12:00', 'task_id': '35f56f30-467d-11e7-98d3-ac728980a78b',
        #            'type_name': 'VNF_3_PPPoE_IPTV_IPoE_VoIP'},
        #           {'add_time': '2017-06-02 13:00', 'task_id': '6baffc5c-467f-11e7-8145-ac728980a78b',
        #            'type_name': 'VNF_1_Concurrent_Session_Capacity'},
        #           {'add_time': '2017-05-11 14:00', 'task_id': 'c46fb2f4-4695-11e7-b1ac-ac728980a78b',
        #            'type_name': 'VNF_2_VBRAS_Client_Forwarding_Performance'},
        #           {'add_time': '2017-05-25 15:00', 'task_id': '23ed47e2-4744-11e7-92c3-ac728980a78b',
        #            'type_name': 'VNF_3_PPPoE_IPTV_IPoE_VoIP'}
        #           ]

        # 待测代码
        start_time = d.get('timeBegin')
        end_time = d.get('timeEnd')
        print(start_time)
        print('=====')
        print(end_time)

        items = TestCaseState.objects.only('add_time', 'type_name') \
            .filter(add_time__gt=start_time, add_time__lt=end_time).all()

        result = []
        for item in items:
            rst = {}
            rst['task_id'] = str(item.task_id)
            rst['add_time'] = item.add_time.strftime('%Y-%m-%d %H:%M:%S')
            rst['type_name'] = item.type_name
            result.append(rst)

        return HttpResponse(json.dumps(result), content_type='application/json')
    return HttpResponse('Permission denied!', status=403)


# 选择某一项task后，返回cpu性能资源比【已提供测试数据】
def api4_query_task_cpu(req):
    if req.method == 'POST':
        d = json.loads(req.body.decode('utf-8'))
        print(d)

        result = []
        taskid = d.get('taskid')
        task_type = d.get('tasktype')

        if task_type == '1':
            # 待测代码
            items = PPPoESessionTest.objects.filter(task_id=taskid)
            for item in items:
                rst = {}
                # rst['add_time'] = item.add_time.strftime('%Y-%m-%d %H:%M:%S')
                rst['add_time'] =  time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(item.add_time))
                # 上线速率
                current_session = item.session_num
                set_session = TestCaseState.objects.get(task_id=taskid).set_session
                # cpu利用率
                obj = CPUMemory.objects.filter(add_time__lt=item.add_time).last()
                cpu = obj.cpu
                # 性能资源比
                cpu_res_rate = (current_session/set_session)/cpu
                rst['cpu'] = cpu_res_rate
                result.append(rst)

            # 测试数据
            # result = [{'cpu': 0.15, 'add_time': '2017-06-01 10:00:13'},
            #           {'cpu': 0.21, 'add_time': '2017-06-01 10:00:16'},
            #           {'cpu': 0.33, 'add_time': '2017-06-01 10:00:19'},
            #           {'cpu': 0.32, 'add_time': '2017-06-01 10:00:22'},
            #           {'cpu': 0.45, 'add_time': '2017-06-01 10:00:25'},
            #           {'cpu': 0.57, 'add_time': '2017-06-01 10:00:28'},
            #           {'cpu': 0.66, 'add_time': '2017-06-01 10:00:31'},
            #           {'cpu': 0.89, 'add_time': '2017-06-01 10:00:35'},
            #           {'cpu': 0.90, 'add_time': '2017-06-01 10:00:38'},
            #           {'cpu': 0.93, 'add_time': '2017-06-01 10:00:41'}]

        elif task_type == '2':
            # 待测代码
            items = UserTransTest.objects.filter(task_id=taskid)
            for item in items:
                rst = {}
                rst['add_time'] = item.add_time.strftime('%Y-%m-%d %H:%M:%S')
                # 转发速率
                rx_rate = item.rx_rate
                # cpu利用率
                obj = CPUMemory.objects.filter(add_time__lt=item.add_time).last()
                cpu = obj.cpu
                # 性能资源比
                cpu_res_rate = rx_rate/cpu
                rst['cpu'] = cpu_res_rate
                result.append(rst)

            # 测试数据
            # result = [{'cpu': 0.15, 'add_time': '2017-06-02 12:00:13'},
            #           {'cpu': 0.21, 'add_time': '2017-06-02 12:00:16'},
            #           {'cpu': 0.33, 'add_time': '2017-06-02 12:00:19'},
            #           {'cpu': 0.32, 'add_time': '2017-06-02 12:00:22'},
            #           {'cpu': 0.45, 'add_time': '2017-06-02 12:00:25'},
            #           {'cpu': 0.57, 'add_time': '2017-06-02 12:00:28'},
            #           {'cpu': 0.66, 'add_time': '2017-06-02 12:00:31'},
            #           {'cpu': 0.89, 'add_time': '2017-06-02 12:00:35'},
            #           {'cpu': 0.90, 'add_time': '2017-06-02 12:00:38'},
            #           {'cpu': 0.93, 'add_time': '2017-06-02 12:00:41'}]

        elif task_type == '3':
            # 待测代码
            items = MultiTest.objects.filter(task_id=taskid)
            for item in items:
                rst = {}
                rst['add_time'] = item.add_time.strftime('%Y-%m-%d %H:%M:%S')
                # 转发速率
                rx_rate = item.rx_rate
                # 上线速率
                current_session = item.session_num
                set_session = TestCaseState.objects.get(task_id=taskid).set_session
                # cpu利用率
                obj = CPUMemory.objects.filter(add_time__lt=item.add_time).last()
                cpu = obj.cpu
                # 性能资源比
                cpu_res_rate = (rx_rate+current_session/set_session)/cpu
                rst['cpu'] = cpu_res_rate
                result.append(rst)

            # 测试数据
            # result = [{'cpu': 0.15, 'add_time': '2017-06-03 13:00:13'},
            #           {'cpu': 0.21, 'add_time': '2017-06-03 13:00:16'},
            #           {'cpu': 0.33, 'add_time': '2017-06-03 13:00:19'},
            #           {'cpu': 0.32, 'add_time': '2017-06-03 13:00:22'},
            #           {'cpu': 0.45, 'add_time': '2017-06-03 13:00:25'},
            #           {'cpu': 0.57, 'add_time': '2017-06-03 13:00:28'},
            #           {'cpu': 0.66, 'add_time': '2017-06-03 13:00:31'},
            #           {'cpu': 0.89, 'add_time': '2017-06-03 13:00:35'},
            #           {'cpu': 0.90, 'add_time': '2017-06-03 13:00:38'},
            #           {'cpu': 0.93, 'add_time': '2017-06-03 13:00:41'}]
        else:
            result = {}

        return HttpResponse(json.dumps(result), content_type='application/json')
    return HttpResponse('Permission denied!', status=403)


# 选择某一项task后，返回memory性能资源比【已提供测试数据】
def api4_query_task_memory(req):
    if req.method == 'POST':

        d = json.loads(req.body.decode('utf-8'))
        print(d)

        result = []
        taskid = d.get('taskid')
        task_type = d.get('tasktype')

        if task_type == '1':
            # 待测代码
            # items = PPPoESessionTest.objects.filter(task_id=taskid)
            # for item in items:
            #     rst = {}
            #     # rst['add_time'] = item.add_time.strftime('%Y-%m-%d %H:%M:%S')
            #     rst['add_time'] = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(item.add_time))
            #     # 上线速率
            #     current_session = item.session_num
            #     set_session = TestCaseState.objects.get(task_id=taskid).set_session
            #     # memory利用率
            #     obj = CPUMemory.objects.filter(add_time__lt=item.add_time).last()
            #     memory = obj.memory
            #     # 性能资源比
            #     memory_res_rate = (current_session / set_session) / memory
            #     rst['memory'] = memory_res_rate
            #     result.append(rst)

            # 测试数据
            result = [{'memory': 0.15, 'add_time': '2017-06-01 10:00:13'},
                      {'memory': 0.21, 'add_time': '2017-06-01 10:00:16'},
                      {'memory': 0.33, 'add_time': '2017-06-01 10:00:19'},
                      {'memory': 0.32, 'add_time': '2017-06-01 10:00:22'},
                      {'memory': 0.45, 'add_time': '2017-06-01 10:00:25'},
                      {'memory': 0.57, 'add_time': '2017-06-01 10:00:28'},
                      {'memory': 0.66, 'add_time': '2017-06-01 10:00:31'},
                      {'memory': 0.89, 'add_time': '2017-06-01 10:00:35'},
                      {'memory': 0.90, 'add_time': '2017-06-01 10:00:38'},
                      {'memory': 0.93, 'add_time': '2017-06-01 10:00:41'}]

        elif task_type == '2':
            # 待测代码
            # items = UserTransTest.objects.filter(task_id=taskid)
            # for item in items:
            #     rst = {}
            #     rst['add_time'] = item.add_time.strftime('%Y-%m-%d %H:%M:%S')
            #     # 转发速率
            #     rx_rate = item.rx_rate
            #     # cpu利用率
            #     obj = CPUMemory.objects.filter(add_time__lt=item.add_time).last()
            #     memory = obj.memory
            #     # 性能资源比
            #     memory_res_rate = rx_rate / memory
            #     rst['memory'] = memory_res_rate
            #     result.append(rst)

            # 测试数据
            result = [{'memory': 0.15, 'add_time': '2017-06-02 12:00:13'},
                      {'memory': 0.21, 'add_time': '2017-06-02 12:00:16'},
                      {'memory': 0.33, 'add_time': '2017-06-02 12:00:19'},
                      {'memory': 0.32, 'add_time': '2017-06-02 12:00:22'},
                      {'memory': 0.45, 'add_time': '2017-06-02 12:00:25'},
                      {'memory': 0.57, 'add_time': '2017-06-02 12:00:28'},
                      {'memory': 0.66, 'add_time': '2017-06-02 12:00:31'},
                      {'memory': 0.89, 'add_time': '2017-06-02 12:00:35'},
                      {'memory': 0.90, 'add_time': '2017-06-02 12:00:38'},
                      {'memory': 0.93, 'add_time': '2017-06-02 12:00:41'}]

        elif task_type == '3':
            # 待测代码
            # items = MultiTest.objects.filter(task_id=taskid)
            # for item in items:
            #     rst = {}
            #     rst['add_time'] = item.add_time.strftime('%Y-%m-%d %H:%M:%S')
            #     # 转发速率
            #     rx_rate = item.rx_rate
            #     # 上线速率
            #     current_session = item.session_num
            #     set_session = TestCaseState.objects.get(task_id=taskid).set_session
            #     # cpu利用率
            #     obj = CPUMemory.objects.filter(add_time__lt=item.add_time).last()
            #     memory = obj.memory
            #     # 性能资源比
            #     memory_res_rate = (rx_rate + current_session / set_session) / memory
            #     rst['memory'] = memory_res_rate
            #     result.append(rst)

            # 测试数据
            result = [{'memory': 0.15, 'add_time': '2017-06-03 13:00:13'},
                      {'memory': 0.21, 'add_time': '2017-06-03 13:00:16'},
                      {'memory': 0.33, 'add_time': '2017-06-03 13:00:19'},
                      {'memory': 0.32, 'add_time': '2017-06-03 13:00:22'},
                      {'memory': 0.45, 'add_time': '2017-06-03 13:00:25'},
                      {'memory': 0.57, 'add_time': '2017-06-03 13:00:28'},
                      {'memory': 0.66, 'add_time': '2017-06-03 13:00:31'},
                      {'memory': 0.89, 'add_time': '2017-06-03 13:00:35'},
                      {'memory': 0.90, 'add_time': '2017-06-03 13:00:38'},
                      {'memory': 0.93, 'add_time': '2017-06-03 13:00:41'}]
        else:
            result = {}

        return HttpResponse(json.dumps(result), content_type='application/json')
        # return HttpResponse(json.dumps(data), content_type='application/json')
    return HttpResponse('Permission denied!', status=403)


# 选择某一项task后，返回资源利用率稳定性，由于公式未知，未进行编写【无法提供测试数据】
def api4_query_task_stability(req):
    if req.method == 'POST':

        d = json.loads(req.body.decode('utf-8'))
        print(d)

        result = []
        taskid = d.get('taskid')
        task_type = d.get('tasktype')

        return HttpResponse(json.dumps(result), content_type='application/json')
        # return HttpResponse(json.dumps(data), content_type='application/json')
    return HttpResponse('Permission denied!', status=403)


# UTCS时间转换为时间戳 2016-07-31T16:00:00Z
def utc_to_local(utc_time_str, utc_format='%Y-%m-%dT%H:%M:%SZ'):
    local_tz = pytz.timezone('Asia/Chongqing')
    local_format = "%Y-%m-%d %H:%M"
    utc_dt = datetime.datetime.strptime(utc_time_str, utc_format)
    local_dt = utc_dt.replace(tzinfo=pytz.utc).astimezone(local_tz)
    time_str = local_dt.strftime(local_format)
    return int(time.mktime(time.strptime(time_str, local_format)))


# 本地时间转换为UTC
def local_to_utc(local_ts, utc_format='%Y-%m-%dT%H:%MZ'):
    local_tz = pytz.timezone('Asia/Chongqing')
    local_format = "%Y-%m-%d %H:%M"
    time_str = time.strftime(local_format, time.localtime(local_ts))
    dt = datetime.datetime.strptime(time_str, local_format)
    local_dt = local_tz.localize(dt, is_dst=None)
    utc_dt = local_dt.astimezone(pytz.utc)
    return utc_dt.strftime(utc_format)

