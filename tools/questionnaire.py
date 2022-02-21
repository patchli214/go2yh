#!/usr/bin/env python
# -*- coding:utf-8 -*-
import json
from go2.settings import BASE_DIR
import math
import collections
from tools import constant,utils,http
from mongoengine.queryset.visitor import Q
from regUser.models import Student, Contract, ContractType
from webpage.models import Short
import random
import string
from branch.models import Branch
import datetime


#获取问卷题目
def readFileToJson(filename):
    path = BASE_DIR+'/go_static/data/'
    questions = []
    f = open(path+filename)
    q = f.read()
    #qa = json.JSONDecoder(object_pairs_hook=collections.OrderedDict).decode(q)
    qa = json.loads(q)
    questionnaire = {}
    questionnaire['title'] = qa['title']
    questionnaire['prelude'] = qa['prelude']
    questionnaire['questCount'] = qa['questCount']
    questions = qa['qs']
    #print questionnaire
    return questionnaire,questions

#ABCD转换为分数
def getScoreByAnswers(value):
    score = 0
    leng = len(value)
    map = dict()
    for i in range(leng):
        try:
            a = map[value[i:i+1]]
            map[value[i:i+1]] = a + 1
        except:
            map[value[i:i+1]] = 1

    step = int(math.ceil(float(10)/float(len(map))))
    
    for key in map.keys():
        key = key.upper()
        value = (10-(ord(key)-65)*step)*map[key]
        score = score + value
    
    score = round(float(score)/float(leng),1)
    
    return score

def getQuestStudentsAndSendSMS(cityId,branchId,beginSingDate,endSingDate,contractType):#contractType-常规或假期
    students = None
    branch = Branch.objects.get(id=branchId)  # @UndefinedVariable
    query = Q(status=constant.StudentStatus.sign)
    query2 = Q(status=constant.ContractStatus.sign)
    if branchId:
        query = query&Q(branch=branchId)
        query2 = query2&Q(branch=branchId)
    students = Student.objects.filter(query).order_by("branch")  # @UndefinedVariable
    if beginSingDate:
        query2 = query2&Q(singDate__gte=beginSingDate)
    if endSingDate:
        query2 = query2&Q(singDate__lte=endSingDate)
        
    queryct = None
    if contractType:
        query3 = Q(city=cityId)&Q(type=contractType)
        cts = ContractType.objects.filter(query3)  # @UndefinedVariable
        i = 0
        for ct in cts:
            if i == 0:
                queryct = Q(contractType=ct.id)
            else:
                queryct = queryct|Q(contractType=ct.id)
            i = i + 1
    if queryct:
        query2 = query2&(queryct)
    sids = []
    for s in students:
        sids.append(str(s.id))
    contracts = Contract.objects.filter(query2)  # @UndefinedVariable
    
            
    for c in contracts:
        if c.student_oid not in sids and c.singDate < endSingDate:
            sids.append(c.student_oid) 
            try:
                students.append(Student.objects.get(id=c.student_oid))  # @UndefinedVariable
            except:
                err = 1
    print len(students)
    for s in students:
        tid = ''
        try:
            tid = str(s.teacher.id)
        except:
            tid = ''
        sid = str(s.id)
        param = '201808_'+branch.branchCode+'_'+tid+'_'+sid
        to = None
        hasTo1 = False
        if s.prt1mobile and len(s.prt1mobile.strip()) == 11:
            hasTo1 = True
            to = s.prt1mobile.strip()
        if s.prt2mobile and len(s.prt2mobile.strip()) == 11:
            if hasTo1:
                to = to + ','+s.prt2mobile.strip()
            else:
                tp = s.prt2mobile.strip()
        if to:
            #print to+'|'+param
            sendSMS(to, param,branch.branchCode)
    return students

def getShortUrl(long_url):
    api_url = 'http://api.t.sina.com.cn/short_url/shorten.json?'
    source = 'source=3271760578'
    param = '&url_long='+long_url
    ret = http.http_get(api_url+source+param)
    res = json.loads(ret)
    short = None
    print res
    try:
        short = res[0]['url_short']
    except:
        short = None
    return short

def getShortKey(value):
    query = Q(value=value)
    short = None
    try:
        short = Short.objects.get(query)  # @UndefinedVariable
    except:
        short = Short()
        short.key = ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(6))
        print short.key
        short.value = value
        short.save()
    return short
        
def getShortValue(key): 
    query = Q(key=key)
    short = None
    try:
        short = Short.objects.get(query)  # @UndefinedVariable
    except Exception,e:
        print e
        short = None
    return short

def sendSMS(to,param,branchCode):
    import sys
    reload(sys)
    sys.setdefaultencoding('utf8')  # @UndefinedVariable
    sms = u'【真朴围棋】学习满意度调查：http://go2crm.cn/go2/q?tag=201808_hf_5867c59c3010a53004bbe0ed_586cc0b497a75d6ea58b0b4f回T退订'
    sms = sms.encode('utf-8')
    paramLong = param
    param = getShortKey(param).key
    
    #return
    templateid = '545408073'
    
    sid = constant.MIAO_DI.account_sid
    token = constant.MIAO_DI.auth_token
    url = constant.MIAO_DI.sendSmsUrl

    timestamp = utils.getDateNow(8).strftime("%Y%m%d%H%M%S")#yyyyMMddHHmmss
    #print timestamp
    sig = sid+token+timestamp#MD5(ACCOUNT SID + AUTH TOKEN + timestamp)。共32位（小写）
    
    sig = utils.str2md5(sig)
    data = {'accountSid':sid,'to':to,'timestamp':timestamp,'sig':sig,'templateid':templateid,'param':param}
    #data = {'accountSid':sid,'to':to,'timestamp':timestamp,'sig':sig,'smsContent':sms}
    res = http.http_post(url,data)
    
    info = branchCode+'|'+to+'|'+param+'|'+timestamp+'|'+res
    print info
    #info = info.encode('utf8')
    utils.save_log('sms201808', info)
     
    return info

def doSMS(branchCode):
    branch = None
    try:
        
        branch = Branch.objects.get(branchCode=branchCode)  # @UndefinedVariable
        endDate = datetime.datetime.strptime("2018-03-01","%Y-%m-%d")
        getQuestStudentsAndSendSMS(str(branch.city.id), str(branch.id), None, endDate, constant.ContractType.normal)
    except Exception,e:
        print e
    return

def sendMiaoDiSMS(templateid,param,to):

    sid = constant.MIAO_DI.account_sid
    token = constant.MIAO_DI.auth_token
    url = constant.MIAO_DI.sendSmsUrl

    timestamp = utils.getDateNow(8).strftime("%Y%m%d%H%M%S")#yyyyMMddHHmmss
    #print timestamp
    sig = sid+token+timestamp#MD5(ACCOUNT SID + AUTH TOKEN + timestamp)。共32位（小写）
    
    sig = utils.str2md5(sig)
    data = {'accountSid':sid,'to':to,'timestamp':timestamp,'sig':sig,'templateid':templateid,'param':param}
    #data = {'accountSid':sid,'to':to,'timestamp':timestamp,'sig':sig,'smsContent':sms}

    data1 = json.dumps(data, ensure_ascii=False)
    data = json.loads(data1)
    res = http.http_post(url,data)
    return res

def SMSihuyi():
    url="http://api.ihuyi.com/webservice/sms.php?method=Submit" 
    account="C72207447"
    password="2e5183137a95783907ae8e89ea4be247"
    #===========================================================================
    # result = sess.post url,{
    #     'account'=>account,
    #     'password'=>password,
    #     'mobile'=>phone,
    #     'content'=>"亲爱的主人，我是小元，很高兴，您终于来了。您的验证码是：#{verify_code}。我会一直陪着您闯荡江湖，修炼成人人仰视的围棋高手。"
    #   }
    #   xml=MultiXml.parse result.body
    #   code=xml['SubmitResult']['code']
    #   success=code=='2'
    #   message=xml['SubmitResult']['msg']
    #===========================================================================

if __name__ == "__main__":
    import sys
    print sys.argv[0]
    branchCode = 'hf'
    try:
        #print "参数", sys.argv[1]
        branchCode = sys.argv[1]
    except:
        print 'not para'
    
    print branchCode
    #doSMS(branchCode)
    #getQuestStudentsAndSendSMS(cityId, branchId, None, None, constant.ContractType.normal)
    to = '18611648935'#'15810223765'
    param = '201808_hf_5867c59c3010a53004bbe0ed_5868737297a75d34fe58313f'
    #sendSMS(to,param)
    #info = u'{"respCode":"00000","respDesc":"请求成功。","failCount":"0","failList":[],"smsId":"60b259399c0348a2a52302d7ebd10122"}'
    
    #getScoreByAnswers('ABBAAAC')
    readFileToJson('assess_201808_teacher.json')