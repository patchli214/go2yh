#!/usr/bin/env python
# -*- coding:utf-8 -*-
import json,datetime,time,itertools
import sys
from django.views.decorators.csrf import  csrf_exempt
from mongoengine.queryset.visitor import Q
from go2.settings import BASE_DIR,USER_IMAGE_DIR
from regUser.models import Student,Contract,ContractType, GradeClass,StudentFile
from branch.models import Branch,City
from regUser.forms import PicForm
from itertools import chain
from operator import attrgetter
from django.shortcuts import render
from django.http import HttpResponse,HttpResponseRedirect
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from tools.utils import checkCookie,getDateNow, getWeekBegin
from django.http import HttpResponse,HttpResponseRedirect
from tools import http, utils, constant,zhenpustat,dbsearch,util2
from datetime import timedelta
from teacher.views import login
from teacher.models import Teacher
from student.models import Receipt
from contract.models import *
from webpage.models import Reg
import contract

def cstudents(request):
    login_teacher = checkCookie(request)
    print 'student---------------'
    if not (login_teacher):
        return HttpResponseRedirect('/login')
    searchPhone = request.GET.get("searchPhone") #
    searchName = request.GET.get("searchName") #
    query = Q(prt1mobile__ne=None)
    list = []
    print searchName
    print searchPhone
    if (searchName == None or searchName == '') and (searchPhone == None or searchPhone == ''):

        response = render(request, 'cstudents.html',{"list":list,
                                             "tel":searchPhone,
                                             "name":searchName,
                                             "login_teacher":login_teacher})
        return response
    if searchName:
        query = query&(Q(name__icontains=searchName)|Q(name2__icontains=searchName))
    if searchPhone:
        query = query&(Q(prt1mobile__contains=searchPhone)|Q(prt2mobile__contains=searchPhone))
    print query

    try:
        list = Student.objects.filter(query)  # @UndefinedVariable

    except Exception,e:
        print e
    response = render(request, 'students.html',{"list":list,
                                             "tel":searchPhone,
                                             "name":searchName,
                                             "login_teacher":login_teacher})


    return response


def contract_list(request):
  try:
    reload(sys)
    sys.setdefaultencoding('utf8')  # @UndefinedVariable
    now = getDateNow()
    login_teacher = checkCookie(request)
    city = City.objects.get(id=login_teacher.cityId)  # @UndefinedVariable
    if not (login_teacher):
        return HttpResponseRedirect('/login')
    isFinance = utils.isFinance(login_teacher.branch)
    contractFrom = request.path + '?' + request.META['QUERY_STRING']
    searchStatusStr = request.GET.get("searchStatus") #合同状态
    searchMultiStr = request.GET.get("searchMulti") #是否续费
    searchCTtype = request.GET.get("searchCTtype") #正规班－0，假期班－1，赠课－2
    searchCT = request.GET.get("searchCT") #具体合同类型
    searchCity = request.GET.get("searchCity")
    if searchCity == '0':
        searchCity = None

    searchStatus = None
    try:
        searchStatus = int(searchStatusStr)
    except:
        searchStatus = None
        searchStatusStr = None


    searchMulti = None
    try:
        searchMulti = int(searchMultiStr)
    except:
        searchMulti = None
        searchMultiStr = '-1'
    if not searchCTtype:
        searchCTtype = '-1'
    if not searchCT:
        searchCT = '-1'

    beginDate = request.GET.get("beginDate")
    endDate = request.GET.get("endDate")
    bDate = None
    eDate = None
    if beginDate:
        try:
            bDate = datetime.datetime.strptime(beginDate,"%Y-%m-%d")
        except:
            bDate = None
    if endDate:
        try:
            eDate = datetime.datetime.strptime(endDate,"%Y-%m-%d")
            eDate = eDate + timedelta(days=1)
        except:
            eDate = None
    if not bDate and not eDate:
        eDate = now
        endDate = eDate.strftime("%Y-%m-%d")
        now = datetime.datetime.strptime(now.strftime("%Y-%m-%d")+' 00:00:00',"%Y-%m-%d %H:%M:%S")
        if login_teacher.branchType != '0':
            bDate = getWeekBegin(now)
            bDate = bDate + timedelta(days=-1)
        else:
            bDate = now + timedelta(days=-30)
        beginDate = bDate.strftime("%Y-%m-%d")
    list = []

    cities = None
    searchBranch = login_teacher.branch
    showAll = False
    if login_teacher.branchType != '0':
        searchBranch = None
        if login_teacher.cityId == constant.BEIJING:

            if login_teacher.showIncome == '1':
                cities = City.objects.all().order_by("sn")  # @UndefinedVariable
                if searchCity:
                    try:
                        city = City.objects.get(id=searchCity)  # @UndefinedVariable

                    except:
                        city = None

                else:
                    city = None
                showAll = True
        else:
            try:
                city = City.objects.get(id=login_teacher.cityId)  # @UndefinedVariable
                searchCity = login_teacher.cityId
            except:
                city = None
    valid = True

    cts0,ctQuery0 = dbsearch.getNormalContractTypes(city,valid)


    #日期
    order = "-singDate"
    cts = None
    query = Q(singDate__gte=bDate)&Q(singDate__lt=eDate)
    if searchStatus == constant.ContractStatus.refund or searchStatus == constant.ContractStatus.finish:
        query = Q(endDate__gte=bDate)&Q(endDate__lt=eDate)
        order = "-endDate"
    if searchStatus == constant.ContractStatus.refundWaiting:
        query = Q(refundAppDate__gte=bDate)&Q(refundAppDate__lt=eDate)
        order = "-refundAppDate"
    #校区
    if searchBranch:
        query = query&Q(branch=searchBranch)

    #常规班、集训班、赠课类型, 合同长度类型
    queryCT = None
    if searchCT != '-1':
        queryCT = Q(contractType=searchCT)
    elif searchCTtype == '0':
        cts,ctQuery = dbsearch.getNormalContractTypes(city)
        queryCT = ctQuery
    elif searchCTtype == '1':
        cts,ctQuery = dbsearch.getHolidayContractType(city)
        queryCT = ctQuery
    elif searchCTtype == '2':
        cts,ctQuery = dbsearch.getFreeContractTypes(city)
        queryCT = ctQuery
    elif searchCTtype == '3':

        cts,ctQuery = dbsearch.getMemberFeeContractTypes(city)
        queryCT = ctQuery

    if queryCT:
        query = query&(queryCT)

    #状态

    if searchStatus != None:

        queryStatus = Q(status=searchStatus)
        if searchStatus == 1:
            queryStatus = queryStatus|Q(status=3)
        query = query&(queryStatus)

    #else:
        #query = query&Q(status=0)
    #续费
    if searchMulti > -1:
        query = query&Q(multi=searchMulti)
    if searchCity:
        branches = Branch.objects.filter(city=searchCity)  # @UndefinedVariable
        ci = 0
        qcity = None
        for b in branches:
            if ci == 0:
                qcity = Q(branch=b.id)
            else:
                qcity = qcity|Q(branch=b.id)
            ci = ci + 1
        query = query&(qcity)
    query = query&Q(status__ne=constant.ContractStatus.delete)
    contracts = Contract.objects.filter(query).order_by("branch",order)  # @UndefinedVariable



    if not searchBranch:
        for c in contracts:
          try:
              go = False
              if not showAll and str(c.branch.city.id)  == login_teacher.cityId:
                  go = True
              elif showAll:
                  go = True

              if go:
                student = Student.objects.get(id=c.student_oid)  # @UndefinedVariable
                if student and login_teacher.showIncome == '1':
                    list.append(c)
                elif student and login_teacher.role < constant.Role.financial and str(student.regBranch.id)==login_teacher.branch:
                    list.append(c)
          except:
            student = None
    else:
        list = contracts



    l = []
    sum = 0 #学费总额
    sumPure = 0
    gone = []
    for c in list:
        try:
            s = Student.objects.get(id=c.student_oid)  # @UndefinedVariable

        except:
            s = None
        if s:
            c.student_name = s.name
            c.student_id = s.id
            c.regBranch = s.regBranchName
            c.regTeacher = s.regTeacherName
            c.teacherName = s.teacherName
            if s.co_teacher and len(s.co_teacher)>0:
                for t in s.co_teacher:
                    try:
                        c.regTeacher = c.regTeacher + ' ' + t.name
                    except:
                        err = 1
            if c.branch:
                c.branchName = c.branch.branchName
                if showAll:
                    citySn = ''
                    if c.branch.city.sn < 10:
                        citySn = '0' + str(c.branch.city.sn)
                    else:
                        citySn = str(c.branch.city.sn)
                    c.city = citySn + c.branch.city.cityName
            c.gender = s.gender
            c.yearMonth = s.birthday
            c.sn = s.branch.sn
            c.code = s.code
            c.regTime = s.callInTime
            c.sourceType = s.sourceType
            birthday = s.birthday
            if birthday:
                days = (getDateNow()-birthday).days
                y = days/365
                m = days%365/30
                c.yearMonth = str(y)+u'岁'+str(m)+u'个月'

            if c.status == constant.ContractStatus.refund:
                if c.refund > 0:
                    c.paid = c.refund
            if not c.paid and c.contractType:
                c.paid = c.contractType.fee
            if c.paid:
                sum = sum + c.paid
            if c.paid>1600:
                sumPure = sumPure + c.paid
            personCsum = 0
            if s.contract and len(s.contract)>1:
                #print 'cc.contractType.type HAS'
                personSum = 0
                personWeeks = 0
                personSigndate = getDateNow()
                c.memo2 = ''
                nw = 0
                ns = 0
                nrw = 0
                nrs = 0
                i = 0
                for cc in s.contract:
                    i = i + 1
                    cmulti = ''
                    if c.memo2 != '':
                        c.memo2 = c.memo2 + ' '

                    try:
                      showWeeks = str(cc.weeks)+u'周'
                      if login_teacher.showIncome == '1':
                          showWeeks = str(cc.weeks*2)+u'课时'

                      if cc.multi == constant.MultiContract.newDeal and (cc.contractType.type == constant.ContractType.normal or cc.contractType.type == constant.ContractType.memberFee):

                        cmulti = u'新招生'
                        nw = cc.weeks
                        ns = cc.paid
                        c.memo2 = c.memo2+str(i)+'.'+cmulti+showWeeks+str(cc.paid)+u'元'+'('+cc.singDate.strftime("%Y-%m-%d")+')'
                      if cc.multi == constant.MultiContract.oldRedeal and (cc.contractType.type == constant.ContractType.normal or cc.contractType.type == constant.ContractType.memberFee):
                        cmulti = u'老生续费'
                        c.memo2 = c.memo2+str(i)+'.'+cmulti+showWeeks+str(cc.paid)+u'元'+'('+cc.singDate.strftime("%Y-%m-%d")+')'
                      if cc.contractType.type == constant.ContractType.hc:
                        cmulti = u'集训班'
                        c.memo2 = c.memo2+str(i)+'.'+cmulti+str(cc.weeks)+u'周'+str(cc.paid)+u'元'+'('+cc.singDate.strftime("%Y-%m-%d")+')'
                      if cc.contractType.type == constant.ContractType.free:
                        cmulti = u'增课'
                        c.memo2 = c.memo2+str(i)+'.'+cmulti+showWeeks+str(cc.paid)+u'元'+'('+cc.singDate.strftime("%Y-%m-%d")+')'
                      if cc.multi == constant.MultiContract.newRedeal and (cc.contractType.type == constant.ContractType.normal or cc.contractType.type == constant.ContractType.memberFee):
                        cmulti = u'新生续费到'

                        nrw = nw + cc.weeks
                        nrs = ns + cc.paid
                        showWeeks = str(nrw)+u'周'
                        if login_teacher.showIncome == '1':
                            showWeeks = str(nrw*2)+u'课时'

                        c.memo2 = c.memo2+str(i)+'.'+cmulti+showWeeks+str(nrs)+u'元'+'('+cc.singDate.strftime("%Y-%m-%d")+')'



                    except:
                        ex = 1

            if searchStatus == constant.ContractStatus.finish:
                if c.student_oid not in gone:
                    gone.append(c.student_oid)
                    l.append(c)

            else:
                l.append(c)

    list = l

    # 页码设置


    mainurl = "/go2/contract/contract_list?branch="+login_teacher.branch
    if searchStatusStr:
        mainurl = mainurl + '&searchStatus=' + searchStatusStr
    if searchMultiStr:
        mainurl = mainurl + '&searchMulti=' + searchMultiStr
    if searchCTtype:
        mainurl = mainurl + '&searchCTtype=' + searchCTtype
    if searchCT:
        mainurl = mainurl + '&searchCT=' + searchCT
    showCol = 7
    if showAll:
        showCol = 7
    if searchStatusStr == '2' or searchStatusStr == '1' or searchStatusStr == '-1':
        showCol = showCol + 1
    response = render(request, 'contracts.html',{"list":list,"cts":cts0,
                                             "paymethods":utils.constant.PAY_METHOD,
                                             "branch":searchBranch,
                                             "beginDate":beginDate,
                                             "endDate":endDate,
                                             "searchStatus":searchStatusStr,
                                             "searchCT":searchCT,
                                             "searchCTtype":searchCTtype,
                                             "searchMulti":searchMultiStr,
                                             "searchCity":searchCity,
                                             "sum":sum,"showCol":showCol,
                                             "sumPure":sumPure,"showAll":showAll,
                                             "cities":cities,"isFinance":isFinance,
                                             "login_teacher":login_teacher})
    response.set_cookie("mainurl",mainurl)
    response.set_cookie("backurl",mainurl)
    response.set_cookie("contractFrom",contractFrom)

    return response
  except Exception,e:
      res = {'err':1,'msg':str(e)}
      return http.JSONResponse(json.dumps(res, ensure_ascii=False))

def netcontracts(request):
    login_teacher = checkCookie(request)
    if not (login_teacher):
        return HttpResponseRedirect('/login')
    searchCity = request.GET.get("searchCity")
    searchBranch = request.GET.get("searchBranch")
    beginDate = request.GET.get("beginDate")
    endDate = request.GET.get("endDate")
    bDate = None
    eDate = None
    if beginDate:
        try:
            bDate = datetime.datetime.strptime(beginDate,"%Y-%m-%d")
        except:
            bDate = None
    if endDate:
        try:
            eDate = datetime.datetime.strptime(endDate,"%Y-%m-%d")
            eDate = eDate + timedelta(days=1)
        except:
            eDate = None
    if not bDate and not eDate:
        now = utils.getDateNow(8)
        eDate = now
        endDate = eDate.strftime("%Y-%m-%d")
        now = datetime.datetime.strptime(now.strftime("%Y-%m-%d")+' 00:00:00',"%Y-%m-%d %H:%M:%S")
        if login_teacher.branchType != '0':
            bDate = getWeekBegin(now)
            bDate = bDate + timedelta(days=-1)
        else:
            bDate = now + timedelta(days=-30)
        beginDate = bDate.strftime("%Y-%m-%d")
    list = []
    query = (Q(contractType=constant.BJ_NETCT1)|Q(contractType=constant.BJ_NETCT2))&Q(singDate__gte=bDate)&Q(singDate__lt=eDate)
    query = query&Q(status__ne=4)
    contracts = Contract.objects.filter(query)  # @UndefinedVariable
    for c in contracts:
        try:
            s = Student.objects.get(id=c.student_oid)  # @UndefinedVariable
        except:
            s = None
        c.student = s
        try:
            y19s = Y19Income.objects.filter(contractId=str(c.id))  # @UndefinedVariable
            y19 = y19s[0]
            c.regName = y19.regName
            c.regMobile = y19.mobile
        except Exception,e:
            print e
            y19 = None

        list.append(c)

    response = render(request, 'netcontracts.html',{"list":list,
                                             "branch":searchBranch,
                                             "beginDate":beginDate,
                                             "endDate":endDate,
                                             "searchCity":searchCity,
                                             "login_teacher":login_teacher})


    return response

def removeContract(request):
    login_teacher = checkCookie(request)
    if not (login_teacher):
        return HttpResponseRedirect('/login')
    if login_teacher.role == 7:
        id = request.POST.get("id")
        try:
            contract = Contract.objects.get(id=id)  # @UndefinedVariable
        except Exception,e:
            res = {"error": 1, "msg": e}
            return http.JSONResponse(json.dumps(res, ensure_ascii=False))
        if contract:
            try:
                student = Student.objects.get(id=contract.student_oid)  # @UndefinedVariable
                if student:
                    normalStatus = -1
                    contracts = student.contract
                    list = []
                    for c in contracts:
                        if str(c.id) != id:
                            list.append(c)
                            if c.status==0:
                                normalStatus = 1
                    student.contract = list
                    if normalStatus == 1:
                        student.status = normalStatus
                    else:
                        student.status = 0
                    student.save()
                contract.delete()
                res = {"error": 0, "msg": "成功"}
            except Exception,e:
                res = {"error": 1, "msg": e}
        else:
            res = {"error": 1, "msg": "未找到此合同"}
    else:
        res = {"error": 1, "msg": "您没有删除合同的权限"}
    return http.JSONResponse(json.dumps(res, ensure_ascii=False))

def studentContracts(request):
    login_teacher = checkCookie(request)
    if not (login_teacher):
        return HttpResponseRedirect('/login')
    if login_teacher.role < 5:
        res = {"err":"无权管理合同"}
        return http.JSONResponse(json.dumps(res, ensure_ascii=False))


    contractFrom = request.COOKIES.get('contractFrom','')

    refundMemo = request.COOKIES.get('refundMemo','')
    refund = request.COOKIES.get('refund','')

    student_oid = request.GET.get("student_oid")
    refundId = request.GET.get("refundContractId")
    if not refundId:
        refundId = ''
    city = City.objects.get(id=login_teacher.cityId)  # @UndefinedVariable
    contractTypes = ContractType.objects.filter(city=login_teacher.cityId).order_by("code")  # @UndefinedVariable
    q = Q(city=login_teacher.cityId)&Q(deleted__ne=1)
    validContractTypes = ContractType.objects.filter(q).order_by("code")  # @UndefinedVariable
    student = None
    contracts = None
    num = 0
    canSign = True
    otherCS = None

    sum = 0 #学费总额
    sumAvail = 0 #学费可开票
    sumPrinted = 0 #学费已开票金额
    requireSum = 0 #学费申请开票中

    sum2 = 0 #会员费
    sumAvail2 = 0 #会员费可开票
    sumPrinted2 = 0 #会员费已开票
    requireSum2 = 0 #会员费申请开票中


    dateNow = utils.getDateNow()
    dateNowStr = dateNow.strftime("%Y-%m-%d")
    receipts = None

    try:
        student = Student.objects.get(id=student_oid)  # @UndefinedVariable


        try:
            #canSign,otherCS = util2.canSign(student.id,student.prt1mobile)
            query = Q(student_oid=student_oid)
            contracts = Contract.objects.filter(query).order_by('dueDate','singDate')  # @UndefinedVariable

        except Exception, e:
            print(e)

        if student and contracts and len(contracts)>0:
            #contracts = student.contract
            num = len(contracts)
            hasOld = False


            try:

                deadline0 = dateNow+datetime.timedelta(days=-constant.RECEIPT_DEADLINE_REDEAL) #123天前
                deadline = dateNow+datetime.timedelta(days=-constant.RECEIPT_DEADLINE_NEW) #93天前
                hasDeadline0 = False
                hasDeadline = False
                temp = []
                for c in contracts:

                    try:
                        if c.status == constant.ContractStatus.delete:
                            continue
                        try:
                            if c.contractType.duration < city.dealDuration and c.contractType.duration > 1:
                                hasOld = True
                        except:
                            err = 1
                        if c.paid and c.paid > 0:
                            if c.contractType.type == constant.ContractType.memberFee and c.multi != constant.MultiContract.memberLesson:
                                sum2 = sum2 + c.paid
                            else:
                                sum = sum + c.paid
                        #学费
                        #print '[multi]'+str(c.multi)
                        #print '[type]'+str(c.contractType.type)
                        mf = False #会员费
                        isNew = False #新生合同
                        is3month = False #季度学费
                        isValidDate0 = False #在第一期限内（四个月）
                        isValidDate1 = False #三个月
                        try:
                            mf = c.contractType.type == constant.ContractType.memberFee# and c.multi != constant.MultiContract.memberLesson
                        except:
                            mf = False
                        isNew = c.multi == constant.MultiContract.newDeal
                        is3month = c.multi == constant.MultiContract.memberLesson
                        isValidDate0 = c.beginDate >= deadline0
                        isValidDate1 = c.singDate >= deadline

                        #学费
                        if isNew and (not mf or is3month) and isValidDate0 and c.paid and c.paid > 0:
                            sumAvail = sumAvail + c.paid
                            hasDeadline0 = True
                        elif not isNew and (not mf or is3month) and isValidDate1 and c.paid and c.paid > 0:
                            sumAvail = sumAvail + c.paid
                            hasDeadline = True
                        #会员费
                        if mf and not is3month and isValidDate0 and c.paid and c.paid > 0 and isNew:
                            sumAvail2 = sumAvail2 + c.paid
                        elif mf and not is3month and isValidDate1 and c.paid and c.paid > 0 and not isNew:
                            sumAvail2 = sumAvail2 + c.paid
                    except Exception,e:

                        print e
                    try:
                        query = Q(contractId=str(c.id))
                        y19s = Y19Income.objects.filter(query)
                        if len(y19s) > 0:
                            c.mobile = y19s[0].mobile
                            c.regName = y19s[0].regName

                    except:
                        err = 1

                query = Q(student=student.id)&Q(status=1)
                receipts = Receipt.objects.filter(query)  # @UndefinedVariable
                printed2 = 0 #失效已开票
                printed1 = 0 #有效已开票
                printedMember1 = 0 #有效已开票-会员费
                printedMember2 = 0 #失效已开票-会员费

                for receipt in receipts:
                    if receipt.sum > 0:
                        if receipt.isMemberFee:
                            sumPrinted2 = sumPrinted2 + receipt.sum
                        else:
                            sumPrinted = sumPrinted + receipt.sum




                if sumPrinted2 > sum2 - sumAvail2:
                    printedMember1 = sumPrinted2 - (sum2 - sumAvail2)
                    printedMember2 = sum2 - sumAvail2
                else:
                    printedMember1 = 0
                    printedMember2 = sumPrinted2

                if sumPrinted > sum - sumAvail:
                    printed1 = sumPrinted - (sum - sumAvail)
                    printed2 = sum - sumAvail
                else:
                    printed1 = 0
                    printed2 = sumPrinted


                        #=======================================================
                        # if receipt.printDate >= deadline0 and hasDeadline0:
                        #     if receipt.isMemberFee:
                        #         printedMember1 = printedMember1 + receipt.sum
                        #     else:
                        #         printed1 = printed1 + receipt.sum
                        # elif receipt.printDate >= deadline and hasDeadline:
                        #     if receipt.isMemberFee:
                        #         printedMember1 = printedMember1 + receipt.sum
                        #     else:
                        #         printed1 = printed1 + receipt.sum
                        # else:
                        #     printed2 = printed2 + receipt.sum
                        #=======================================================

                sumAvail = sumAvail - printed1

                sumAvail2 = sumAvail2 - printedMember1
            except Exception,e:
                print e
                print 'eeee1111'
                err = 1
            if not hasOld:
                contractTypes = validContractTypes

    except Exception,e:
        print e
        print 'errrrrr'
        #student = None

    nowValidContracts = dbsearch.getNowValidContract(student_oid,None)
    nrc = dbsearch.getNowValidNewRedealContract(student_oid,None)
    orc = dbsearch.getNowValidOldRedealContract(student_oid,None)
    hasNowValidContract,isNewRedeal,isOldRedeal,isNew = dbsearch.checkMultiContractStatus(student_oid, getDateNow(),nowValidContracts,nrc,orc)
    query = Q(city=login_teacher.cityId)&(Q(type=1)|Q(type=2))
    newCT = validContractTypes

    if not isNew and not isNewRedeal and not isOldRedeal:
        newCT = ContractType.objects.filter(query)  # @UndefinedVariable

    query = Q(student=student_oid)&Q(contractId__ne=None)
    contractFiles = StudentFile.objects.filter(query)  # @UndefinedVariable

    query = Q(student=student.id)&(Q(status=0)|Q(status=None))

    requires = Receipt.objects.filter(query)  # @UndefinedVariable

    if requires and len(requires)>0:
        for r in requires:
            if r.sum > 0:
                if r.isMemberFee:
                    requireSum2 = requireSum2 + r.sum
                else:
                    requireSum = requireSum + r.sum
    millis = int(round(time.time() * 1000))
    backurl = '/go2/contract/studentContracts?student_oid='+str(student.id)
    sumAvailNow = sumAvail - requireSum
    sumAvailNow2 = sumAvail2 - requireSum2
    voucher = request.GET.get('voucher')
    if not voucher:
        voucher = ''
    temp = []
    if contracts:
        for c in contracts:
            temp.append(c)
    contracts = temp
    query = Q(branch=student.branch.id)&Q(status=0)
    teachers = Teacher.objects.filter(query).order_by('role')  # @UndefinedVariable

    response = render(request, 'studentContracts.html', {"student":student,"teachers":teachers,
                                             "contracts":contracts,"canSign":canSign,"otherCS":otherCS,
                                             "num":num,"hasNowValidContract":hasNowValidContract,
                                             "contractTypes":contractTypes,"paymethods":utils.constant.PAY_METHOD,
                                             "validContractTypes":validContractTypes,
                                             "isNewRedeal":isNewRedeal,
                                             "isOldRedeal":isOldRedeal,
                                             "voucher":voucher,
                                             "isNew":isNew,"newCT":newCT,"dateNowStr":dateNowStr,
                                             "contractFiles":contractFiles,"receipts":receipts,
                                             "refundId":refundId,"refundMemo":refundMemo,"refund":refund,
                                             "millis":millis,"contractFrom":contractFrom,"sumAvailNow":sumAvailNow,
                                             "sum":sum,"sumAvail":sumAvail,"sumPrinted":sumPrinted,"requireSum":requireSum,
                                             "sumAvailNow2":sumAvailNow2,
                                             "sum2":sum2,"sumAvail2":sumAvail2,"sumPrinted2":sumPrinted2,"requireSum2":requireSum2,
                                             "login_teacher":login_teacher})

    response.set_cookie("backurl",backurl)
    return response

def saveContract_api(request):

    login_teacher = checkCookie(request)
    if not (login_teacher):
        return HttpResponseRedirect('/login')

    status = 0
    try:
        status = int(request.POST.get("status"))
    except:
        status = 0

    weeksStr = request.POST.get("weeks")

    beginDateString = request.POST.get("beginDate")
    endDateString = request.POST.get("endDate")
    dueDateString = request.POST.get("dueDate")

    signDateString = request.POST.get("signDate")
    multiStr = request.POST.get("multi")

    signDate = None
    beginDate = None
    endDate = None
    dueDate = None
    try:
        beginDate = datetime.datetime.strptime(beginDateString,"%Y-%m-%d")
    except:
        beginDate = None
    try:
        signDate = datetime.datetime.strptime(signDateString,"%Y-%m-%d")
    except:
        signDate = None
    try:
        endDate = datetime.datetime.strptime(endDateString,"%Y-%m-%d")
    except:
        endDate = None
    try:
        dueDate = datetime.datetime.strptime(dueDateString,"%Y-%m-%d")
    except:
        dueDate = None
    openId = []
    student_oid = request.POST.get("student_oid")
    student = Student.objects.get(id=student_oid)  # @UndefinedVariable
    #签约校区自动提升为第一意向校区，其他意向校区顺位后移
    branch = None
    #===========================================================================
    # if login_teacher.branchType == '1':
    #     branch = student.branch
    # else:
    #     branch = util2.getBranch(login_teacher.branch)
    #===========================================================================

    branch = student.branch
    if not branch:
        branch = student.branch

    if constant.DEBUG:
        print '[branch]' + str(branch.id) + '[student.branch]' + str(student.branch.id)
    changeBranch = False

    if not branch:
        res = {"error": 1, "msg": "没有分配校区，无法签合同"}
        response = http.JSONResponse(json.dumps(res, ensure_ascii=False))
        return response
    cid = request.POST.get("cid")
    if not cid:
        res = {"error": 1, "msg": "没有学籍号，无效合同"}
        response = http.JSONResponse(json.dumps(res, ensure_ascii=False))
        return response


    paymethod = request.POST.get("paymethod")
    hasPaymethod = False
    if paymethod:
        try:
            utils.constant.PAY_METHOD[paymethod]
            hasPaymethod = True
        except:
            hasPaymethod = False
    else:
        hasPaymethod = False
    if not hasPaymethod:
        res = {"error": 1, "msg": "付款方式有误，无法保存合同"}
        response = http.JSONResponse(json.dumps(res, ensure_ascii=False))
        return response

    datenow = utils.getDateNow(8)

    onemonthBefore = utils.subtract_one_month(datenow)
    if int(datenow.strftime("%d")) > constant.SIGN_CLASS_EXPIRE_DAY:
        onemonthBefore = utils.getThisMonthBegin(datenow)

    contract_oid = request.POST.get("contract_oid")

    if not contract_oid and signDate < onemonthBefore and login_teacher.id != login_teacher.cityRB and status != constant.ContractStatus.refundWaiting:
        res = {"error": 1, "msg": "签约日期有误，只能创建本月签约的合同！"}
        response = http.JSONResponse(json.dumps(res, ensure_ascii=False))
        return response
    try:
      if str(branch.id) != str(student.branch.id):
        changeBranch = True
        if constant.DEBUG:
            print 'sign branch is not student.branch!'
            print '[branch2]' + student.branch2
        if student.branch2 == str(branch.id):
            if constant.DEBUG:
                print 'sign branch is student.branch2 !'
            student.branch2 = str(student.branch.id)
            student.branch2name = student.branchName
            if constant.DEBUG:
                print 'set branch2 to:' + student.branch2
        elif student.branch3 == str(branch.id):
            student.branch3 = str(student.branch.id)
            student.branch3name = student.branchName
        elif student.branch4 == str(branch.id):
            student.branch4 = str(student.branch.id)
            student.branch4name = student.branchName
        student.branch = branch
        student.branchName = branch.branchName
    except Exception,e:
        print e

    teacher = student.regTeacher
    signTeacher = request.POST.get('signTeacher')
    try:
        teacher = Teacher.objects.get(id=signTeacher)  # @UndefinedVariable
    except:
        teacher = student.regTeacher

    assistId = request.POST.get('assistId')
    assistant = None
    try:
        assistant = Teacher.objects.get(id=assistId)  # @UndefinedVariable
    except:
        assistant = None

    multi = 0
    try:
        multi = int(multiStr)
    except:
        multi = 0

    contractType_oid = request.POST.get("ct_oid")

    contractType = ContractType.objects.get(id=contractType_oid)  # @UndefinedVariable
    memo = request.POST.get("memo")
    memo2 = request.POST.get("memo2")
    paid = 0
    weeks = 0
    try:
        paid = int(request.POST.get("paid"))
    except:
        if contractType.discountPrice > 0:
            paid = contractType.discountPrice
        elif contractType.fee > 0:
            paid = contractType.fee
        else:
            paid = 0
    try:
        weeks = int(weeksStr)
    except:
        weeks = contractType.duration
    contract = None
    #修改已存在合同

    if contract_oid:
        try:
            contract = Contract.objects.get(id=contract_oid)  # @UndefinedVariable
            canSave = False

            if contract.singDate or contract.multi == 3:
              if login_teacher.id == login_teacher.cityRB or status == constant.ContractStatus.refundWaiting:
                canSave = True
              elif not contract.singDate and signDate < onemonthBefore:
                res = {"error": 1, "msg": "合同修改期已过，不能保存本月前的合同！"}
                response = http.JSONResponse(json.dumps(res, ensure_ascii=False))
                return response
              elif contract.singDate < onemonthBefore and contract.singDate != signDate:
                res = {"error": 1, "msg": "合同修改期已过，不能修改签约日期！"}
                response = http.JSONResponse(json.dumps(res, ensure_ascii=False))
                return response
              elif contract.singDate < onemonthBefore and contract.singDate == signDate:
                if contract.weeks != weeks or contract.paid != paid:
                    res = {"error": 1, "msg": "合同修改期已过，不能修报名周数和金额！"}
                    response = http.JSONResponse(json.dumps(res, ensure_ascii=False))
                    return response
                if contract.status != status and status == constant.ContractStatus.delete:
                    res = {"error": 1, "msg": "合同修改期已过，合同不能作废！"}
                    response = http.JSONResponse(json.dumps(res, ensure_ascii=False))
                    return response
            else:
                canSave = True
        except Exception,e:
            print e
            contract = Contract()
    else:
        contract = Contract()

    if not contract.singDate:
        contract.branch = branch
        contract.teacher = teacher

    now = getDateNow()
    if signDate == None:
        signDate = now
    contract.singDate = signDate
    if beginDate:
        contract.beginDate = beginDate
    else:
        contract.beginDate = now

    if status == 0 and (contractType.type == constant.ContractType.normal or contractType.type == constant.ContractType.memberFee or contract.paid >= 3600):
        student.status = 1

    contract.contractType = contractType

    contract.status = status
    contract.memo = memo

    if contractType.memo.find(u'网课') > -1:
        contract.teacher = teacher
        contract.assistant = assistant
    if memo2:
        contract.memo2 = memo2

    contract.student_oid = student_oid
    contract.paid = paid
    contract.weeks = weeks
    contract.endDate = endDate
    contract.dueDate = dueDate
    if constant.DEBUG:
        print 'got refund?'
        print request.POST.get("refund")
    refund = None
    if status == -1:
        contract.refundAppDate = getDateNow()
        contract.refundApprove = 0
        refundStr = request.POST.get("refund")
        if constant.DEBUG and refundStr:
            print 'refund----'+refundStr
        refund = 0
        if refundStr:
            try:
                refund = int(float(refundStr))
            except:
                refund = 0
        if refund == 0:
            refund = paid
        query = Q(id=login_teacher.cityFA)

        try:
            toTeacher = Teacher.objects.get(query)  # @UndefinedVariable

            if toTeacher and toTeacher.openId:
                openId = toTeacher.openId
        except:
            err = 1
    if constant.DEBUG:
        print 'before---'
    if refund:
        contract.refund = refund
    if constant.DEBUG:
        print 'got refund'
    query = Q(singDate=contract.singDate)&Q(student_oid=contract.student_oid)&Q(status__ne=constant.ContractStatus.refund)&Q(status__ne=constant.ContractStatus.refundWaiting)
    # 签约日期是同一天的重复合同查询
    cs = Contract.objects.filter(query)  # @UndefinedVariable
    if constant.DEBUG:
        print 'got 000'
    has = False
    all = len(cs)
    i = 0
    que = Q(city=login_teacher.cityId)&Q(type=constant.ContractType.hc)
    hc = None
    try:
        hc = ContractType.objects.filter(que)[0]  # @UndefinedVariable
    except:
        hc = None
    try:
        for c in cs:
          try:
            if contract.id != c.id and contract.contractType.id == c.contractType.id and contract.multi != 3 and c.multi != 3 :#常规班删除旧的类型一样的合同
                i = i + 1
              #删除重复合同
                c.delete()
          except:
            continue
    except Exception,e:
        err = 1
    contract.multi = multi
    contract.paymethod = paymethod
    contract.cid = cid
    print '8'
    contract.save()

    voucher = request.POST.get('voucher')
    query = Q(source=voucher)
    reg = Reg.objects.filter(query)  # @UndefinedVariable
    hasVoucher = False

    if reg and len(reg) > 0:

        r = reg[0]
        r.done = True
        r.studentId = contract.student_oid
        r.save()
        stud = Student.objects.get(id=student_oid)  # @UndefinedVariable
        utils.saveTrack(True,stud.id,None,None,login_teacher.id,u'使用兑奖券【'+voucher+u'】',None)
        hasVoucher = True
    if constant.DEBUG:
        print 'DONE'

    query = Q(student_oid=contract.student_oid)
    cs = Contract.objects.filter(query).order_by("_id")  # @UndefinedVariable
    student.contract = cs
    hasNormal = False
    hasFinish = False
    hasRefund = False
    studentsum = 0
    print '9'
    for c in student.contract:

        try:
            if c.status == constant.ContractStatus.delete:
                student.status = constant.StudentStatus.normal
            if c.status == constant.ContractStatus.sign and (contractType.type == constant.ContractType.normal or contractType.type == constant.ContractType.memberFee or contract.paid >= 3600):
                student.status = constant.StudentStatus.sign
                hasNormal = True

                break

            if c.status == constant.ContractStatus.finish and contract.status != constant.ContractStatus.sign:
                student.status = constant.StudentStatus.finish
                hasFinish = True
            if c.status == constant.ContractStatus.refund:
                student.status = constant.StudentStatus.refund
                hasRefund = True
            if c.status != constant.ContractStatus.delete and c.status != constant.ContractStatus.refund:
                studentsum = studentsum + c.paid
        except:
            continue

    if not hasNormal and not hasFinish and not hasRefund:
        student.status = constant.StudentStatus.normal

    if studentsum >= 3600 and student.status == 0:
        student.status = 1
        print 'change to 1'



    hasClass = False
    try:
      if student.gradeClass and len(student.gradeClass)>0:
        try:
            clas = GradeClass.objects.get(id=student.gradeClass)  # @UndefinedVariable
            if clas.gradeClass_type == 1 and clas.deleted != 1:
                hasClass = True
        except:
            hasClass = False
      if not hasClass:
        student.teacher = None
        student.teacherName = None
      allLessons,sd,lessonLeft = utils.getLessonLeft(student)
      student.lessons = allLessons - lessonLeft
      student.lessonLeft = lessonLeft
    except Exception,e:
      err = 1

    if constant.DEBUG:
        print 'branch2 to save:'



    print student.status
    beginDate = None
    endDate = None
    days = None
    learnDays = None
    try:
        beginDate,endDate,days,learnDays = util2.getLessonCheckDeadline(student_oid)
        endDate,learnDays = util2.getEndDateAddVocation(beginDate, endDate, login_teacher.cityId,learnDays)
        endDate,learnDays = util2.getEndDateAddSuspension(beginDate, endDate, student_oid,learnDays)
    except:
        print 'err'


    student.contractDeadline = endDate

    student.save()

    if changeBranch:
        query = Q(branch=student.regBranch)
        if student.branch2:
            query = query|Q(branch=student.branch2)
        if student.branch3:
            query = query|Q(branch=student.branch3)
        if student.branch4:
            query = query|Q(branch=student.branch4)

        query = (query)&Q(role__gt=3)&Q(role__lt=8)&Q(status__ne=-1)
        allTeachers = Teacher.objects.filter(query)  # @UndefinedVariable
        message_txt = ''
        url = ''
        try:
            sname = ''
            has1 = False
            has2 = False
            if student.name:
                has1 = True
                sname = student.name
            if student.name2:
                has2 = True
                sname = sname + u' ' + student.name2
            if not has1 and not has2:
                sname = student.prt1mobile
            message_txt = sname+u' 已在'+student.branchName+u'校区签约'
            url = '/go2/regUser/studentInfo/' + str(student.id) + '/'
        except Exception,e:
            err = 1
        if constant.DEBUG:
            print message_txt
            print allTeachers._query
            print len(allTeachers)
        for t in allTeachers:
            #print 'allTeacher-'+t.branch.branchName+t.name
            utils.sendMessage(login_teacher.branchName,login_teacher.id, login_teacher.teacherName, str(t.id), message_txt, None, url)

    makeSiblingStudent(student)
    msg = u"保存成功"
    #if hasVoucher:
       # msg = u'兑奖完毕'

    #############################
    #      元十九会员费合同        #
    #############################
    mobile = request.POST.get("mobile")
    regName = request.POST.get("regName")

    hasMemberFee = False
    for c in cs:
        try:
                if str(c.id) != contract_oid and c.contractType.type == constant.ContractType.memberFee and c.multi != constant.MultiContract.memberLesson:
                    contract.weeks = contract.weeks + c.weeks
        except Exception,e:
                print e
        try:
            if c.contractType.type == constant.ContractType.memberFee and c.multi != constant.MultiContract.memberLesson:
                hasMemberFee = True
                break
        except:
            err = 1

    if mobile and contract_oid:
        shouldContract = Contract.objects.get(id=contract_oid)  # @UndefinedVariable



        query = Q(contractId=contract_oid)

        y19s = Y19Income.objects.filter(query)
        y19 = Y19Income()
        try:
            y19 = y19s[0]
        except:
            y19 = Y19Income()

        y19.mobile = mobile
        if regName:
            y19.regName = regName

        y19.payDate = contract.singDate
        y19.contractId = contract_oid
        y19.branch = str(contract.branch.id)
        y19.branchName = contract.branch.branchName
        y19.type= u'会员卡'

        try:
            y19.source = contract.contractType.memo
        except Exception,e:
            print e

        if not y19.logDate:
            y19.logDate = utils.getDateNow(8)
        try:
            y19.sellerId = str(student.teacher.id)
            y19.sellerName = student.teacher.name

        except Exception,e:
            print e
            try:
                y19.sellerId = str(student.regTeacher.id)
                y19.sellerName = student.regTeacher.name
            except Exception,e:
                print e
        try:
            y19.save()
        except Exception,e:
            print e

        #######################
        # 生成每期应收款
        #######################
        shouldPayStr= request.POST.get("shouldPay")
        shouldPay = 0
        try:
            shouldPay = int(shouldPayStr)
        except:
            try:
                if contract.contractType.tuition:
                    t.shouldPay = contract.contractType.tuition
            except:
                shouldPay = 1400
        if shouldContract:
            try:
                shouldContract.shouldPay = shouldPay
                shouldContract.save()

            except:
                err = 1
        query = (Q(contractId=str(contract.id))&Q(singDate=None))|Q(status=constant.ContractStatus.delete)
        toDelete = Contract.objects.filter(query)  # @UndefinedVariable


        for t in toDelete:

            t.delete()



        times = contract.weeks/12
        if times < 4:
            times = 4
        ts = []
        dueDate = contract.beginDate
        dueDate0 = dueDate


        for i in range(times):
          try:
            t = Contract()
            t.dueDate = dueDate
            t.contractId = str(contract.id)
            t.branch = contract.branch
            t.student_oid = contract.student_oid


            t.shouldPay = shouldPay
            t.beginDate = contract.beginDate
            t.cid = contract.cid
            t.multi = constant.MultiContract.memberLesson
            t.weeks = 12

            query = Q(student_oid=t.student_oid)&Q(dueDate=dueDate)
            ccc = Contract.objects.filter(query)  # @UndefinedVariable

            dueDate = utils.nextDueDate(dueDate)
            if len(ccc) > 0:
                for c in ccc:
                    c.contractId = t.contractId
                    c.save()

                continue


            ts.append(t)


          except Exception,e:
              print e

        print 'OUT TS LOOP!!!!'
        print len(ts)
        paidsDue = times - len(ts)



        query = Q(student_oid=student_oid)&Q(multi=3)
        try:
            tsNow = Contract.objects.filter(query)  # @UndefinedVariable
            print tsNow._query
        except:
            return

        ii = len(tsNow) - paidsDue

        i = 0
        for t in ts:

            i = i + 1
            if i <= ii:
                continue
            else:
                try:
                    t.save()
                except Exception,e:
                    print '1099'
                    print e

    if contract.contractType.type == constant.ContractType.memberFee and contract.multi != constant.MultiContract.memberLesson:
        hasMemberFee = True

    if not hasMemberFee:

        query = Q(multi=constant.MultiContract.memberLesson)&Q(singDate=None)&Q(student_oid=contract.student_oid)

        csd = Contract.objects.filter(query)  # @UndefinedVariable
        print csd._query
        print len(csd)
        try:
            for cd in csd:
                print '[SHOULD DELETE!]'+str(cd.id)
                cd.delete()

        except Exception,e:
            print e
    try:
        if str(contract.contractType.id) == constant.BJ_NETCT1 or str(contract.contractType.id) == constant.BJ_NETCT2:

            branch = Branch.objects.get(id='5ac48e6f97a75d926c3b744c')  # @UndefinedVariable
            print '000'
            contract.branch = branch
            print '111'
            contract.save()
            print contract.branch.branchName
    except Exception,e:
        print e

    res = {"error": 0, "msg": msg,"openId":openId}
    response = http.JSONResponse(json.dumps(res, ensure_ascii=False))

    response.set_cookie("refundMemo",'')
    response.set_cookie("refund",'')
    return response




def makeSiblingStudent(student):
    if student.siblingName or student.siblingName2 or student.siblingName3:

        query = Q(siblingId=str(student.id))
        siblings = Student.objects.filter(query)  # @UndefinedVariable
        s1 = False
        s2 = False
        s3 = False
        if student.siblingName:
            s1 = True
        if student.siblingName2:
            s2 = True
        if student.siblingName3:
            s3 = True
        has1 = False
        has2 = False
        has3 = False

        try:
            for s in siblings:
                if s.name == student.siblingName:
                    s.status = constant.StudentStatus.sign
                    s.save()
                    has1 = True
                if s.name == student.siblingName2:
                    s.status = constant.StudentStatus.sign
                    s.save()
                    has2 = True
                if s.name == student.siblingName3:
                    s.status = constant.StudentStatus.sign
                    s.save()
                    has3 = True

        except Exception,e:
            print e

        if s1 and not has1:
            saveStudent(student,student.siblingName)
        if s1 and not has2:
            saveStudent(student,student.siblingName2)
        if s1 and not has3:
            saveStudent(student,student.siblingName3)


def saveStudent(student,siblingname):
    ss = Student()
    ss.name = siblingname
    ss.siblingName = student.name
    ss.siblingId = str(student.id)
    ss.branchName = student.branchName
    ss.branch = student.branch
    ss.status = constant.StudentStatus.sign
    ss.save()


def uploadFile(request):
    login_teacher = checkCookie(request)
    if not (login_teacher):
        return HttpResponseRedirect('/login')
    refundMemo = request.GET.get("refundMemo")
    refund = request.GET.get("refund")
    teacher_oid = request.GET.get("teacher_oid")
    student_oid = request.GET.get("student_oid")
    contractId = request.GET.get("contractId")
    type = str(constant.FileType.refundApp) #4
    if request.GET.get("contractId"):
        typeStr = request.GET.get("type")
        try:
            type = int(typeStr)
        except:
            type = str(constant.FileType.refundApp) #4
    print type
    if request.method == 'POST':
        # create a form instance and populate it with data from the request:
        form = PicForm(request.POST, request.FILES)
        # check whether it's valid:
        if form.is_valid():
            # process the data in form.cleaned_data as required
            files =request.FILES.getlist('picFile')
            gourl = '/go2/contract/studentContracts?student_oid='+student_oid+'&refundContractId='+contractId
            for uploadFile in files:
              #uploadFile = request.FILES['picFile']
                si = uploadFile.size
                print type
                t,filedate,relaPath = utils.handle_uploaded_image(uploadFile,login_teacher.branch,student_oid,type,1000,None,contractId)

                try:
                    query = Q(student=student_oid)&Q(contractId=contractId)&Q(fileType=type)
                    sfs = StudentFile.objects.filter(query)  # @UndefinedVariable
                    studentFile = sfs[0]
                    return HttpResponseRedirect(gourl)
                except Exception,e:

                    studentFile = StudentFile()
                    try:
                        student = Student.objects.get(id=student_oid)  # @UndefinedVariable
                    except:
                        student = None

                    try:
                        contract = Contract.objects.get(id=contractId)  # @UndefinedVariable
                    except:
                        contract = None
                    studentFile.student = student
                    if student:
                        studentFile.studentName = student.name
                    if contract:
                        studentFile.contractId = contractId
                    studentFile.filename = t
                    studentFile.filepath = relaPath
                    studentFile.fileCreateTime = getDateNow()
                    studentFile.fileType = type

                    studentFile.save()

            # redirect to a new URL:

            return HttpResponseRedirect(gourl)

    # if a GET (or any other method) we'll create a blank form
    else:
        form = PicForm()
        form.student_oid=student_oid
        form.type=type
        response = render(request, 'uploadFile.html', {'student_oid':student_oid,
                                               'teacher_oid':teacher_oid,
                                               'contractId':contractId,
                                              'type':type,
                                              'form': form})
        response.set_cookie("refundMemo",refundMemo)
        response.set_cookie("refund",refund)
        if constant.DEBUG:
            print 'upload save cookie-refund:'+refund
        return response

def getChargeSchools(login_teacher):
    schools = []
    t = Teacher.objects.get(id=login_teacher.id)  # @UndefinedVariable
    if login_teacher.branchType == constant.BranchType.school:
        schools.append(t.branch)
    elif login_teacher.branchType == constant.BranchType.marketing:
        schools = utils.getBranches(login_teacher, None)
    elif login_teacher.branchType == constant.BranchType.function:
        query = Q(financialAdmin=login_teacher.id)|Q(financialRefund=
                login_teacher.id)|Q(financialReceipt=
                login_teacher.id)|Q(financialReimburse2=
                login_teacher.id)|Q(financialReimburse=login_teacher.id)
        cities = City.objects.filter(query)  # @UndefinedVariable
        query = Q(type=constant.BranchType.school)
        i = 0
        qc = None
        for c in cities:
            if i == 0:
                qc = Q(city=c.id)
            else:
                qc = qc|Q(city=c.id)
            i = i + 1
        if qc:
            query = query&qc
        schools = Branch.objects.filter(query)  # @UndefinedVariable


    return schools

def Y19Income1(request):
    login_teacher = checkCookie(request)
    if not (login_teacher):
        return HttpResponseRedirect('/login')
    query = Q(branch=login_teacher.branch)&Q(status__ne=-1)
    teachers = Teacher.objects.filter(query)  # @UndefinedVariable
    id = request.GET.get("id")
    query = Q(id=id)
    datenow = utils.getDateNow(8)
    income = Y19Income.objects.get(query)  # @UndefinedVariable

    return render(request, 'Y19Income.html',{"login_teacher":login_teacher,"datenow":datenow,
                                           "income":income,"teachers":teachers})

def api_Y19Income(request):

    login_teacher = checkCookie(request)
    if not (login_teacher):
        return HttpResponseRedirect('/login')
    type = request.POST.get("type")
    id = request.POST.get("id")
    regName = request.POST.get('regName')
    mobile = request.POST.get('mobile')
    sellerId = request.POST.get('sellerId') #收款人ID
    source = request.POST.get('source') #

    payDate = request.POST.get('payDate')
    paydate = None
    try:
        paydate = datetime.datetime.strptime(payDate,"%Y-%m-%d")
    except:
        res = {"error": 1, "msg": "购买日期有误"}
        return http.JSONResponse(json.dumps(res, ensure_ascii=False))
    paid = request.POST.get('paid')
    memo = request.POST.get('memo')

    income = Y19Income()

    if id:

        query = Q(id=id)
        try:
            income = Y19Income.objects.get(query)  # @UndefinedVariable

        except Exception,e:
            print e
            res = {"error": 1, "msg": "未找到要修改的收入记录"}
            return http.JSONResponse(json.dumps(res, ensure_ascii=False))
    try:
        income.paid = float(paid)
    except:
        res = {"error": 1, "msg": "金额有误"}
        return http.JSONResponse(json.dumps(res, ensure_ascii=False))

    income.regName = regName
    income.mobile = mobile
    income.sellerId = sellerId
    try:
        income.sellerName = Teacher.objects.get(id=sellerId).name  # @UndefinedVariable
    except:
        income.sellerName = ''
    income.memo = memo

    income.type = type
    income.source = source
    income.payDate = paydate
    income.branch = login_teacher.branch
    income.branchName = login_teacher.branchName
    income.save()

    res = {"error": 0, "msg": "OK"}
    return http.JSONResponse(json.dumps(res, ensure_ascii=False))


def Y19Incomes(request):
    statistic = request.GET.get("statistic")
    login_teacher = checkCookie(request)
    if not (login_teacher):
        return HttpResponseRedirect('/login')

    query = Q(branch=login_teacher.branch)&Q(status__ne=-1)
    teachers = Teacher.objects.filter(query)  # @UndefinedVariable
    query = Q(branch=login_teacher.branch)&Q(isY19=True)
    yts = Teacher.objects.filter(query)  # @UndefinedVariable
    datenow = utils.getDateNow(8)
    beginDate = request.GET.get("beginDate")
    endDate = request.GET.get("endDate")
    eds = endDate
    bDate = None
    eDate = None

    if beginDate:
        try:
            bDate = datetime.datetime.strptime(beginDate,"%Y-%m-%d")
        except:
            bDate = None
    if endDate:
        try:
            eDate = datetime.datetime.strptime(endDate,"%Y-%m-%d")
            eDate = eDate + timedelta(days=1)
        except:
            eDate = None
    if not bDate and not eDate:
        eDate = datenow
        eds = eDate.strftime("%Y-%m-%d")
        now = datetime.datetime.strptime(datenow.strftime("%Y-%m-%d")+' 00:00:00',"%Y-%m-%d %H:%M:%S")

        bDate = now + timedelta(days=-90)
    query = Q(branch=login_teacher.branch)
    if login_teacher.branchType == str(constant.BranchType.management) or login_teacher.branch == '5bc0439fe5c5e6899c06cec9':
      if statistic == '1':
        branches = utils.getCityBranch(login_teacher.cityId,True)
        query = None
        i = 0
        for b in branches:
            if i == 0:
                query = Q(branch=str(b.id))
            else:
                query = query|Q(branch=str(b.id))
            i = i + 1
        query = (query)

    if bDate:

        if login_teacher.branchType == str(constant.BranchType.management) or login_teacher.branch == '5bc0439fe5c5e6899c06cec9':
            query = query&Q(logDate__gte=bDate)
        else:
            query = query&Q(payDate__gte=bDate)
        beginDate = bDate.strftime("%Y-%m-%d")
    if eDate:
        endDate = eDate.strftime("%Y-%m-%d")

        if login_teacher.branchType == str(constant.BranchType.management) or login_teacher.branch == '5bc0439fe5c5e6899c06cec9':
            query = query&Q(logDate__lt=eDate)
        else:
            query = query&Q(payDate__lt=eDate)

    incomes = None
    query = query&(Q(paid__gt=0)|Q(contractId__ne=None))
    try:
        incomes = Y19Income.objects.filter(query).order_by('-payDate')  # @UndefinedVariable
        #print incomes._query
    except Exception,e:
        print e
    y19data = None
    day = utils.getDateNow(8)
    day = utils.onlyDate(day)
    query = Q(day=day)&Q(branch=login_teacher.branch)
    y19data = Y19data.objects.filter(query).order_by("teacher")
    #print y19data._query

    return render(request, 'Y19Incomes.html',{"login_teacher":login_teacher,"datenow":datenow,
                                           "beginDate":beginDate,"teachers":teachers,"now":datenow,
                                             "endDate":eds,"statistic":statistic,"yts":yts,
                                           "incomes":incomes,"y19data":y19data})

def Y19stat(request):
    login_teacher = checkCookie(request)
    if not (login_teacher):
        return HttpResponseRedirect('/login')
    begin = request.GET.get("beginDate")
    end = request.GET.get("endDate")
    beginDate = None
    endDate = None
    try:
        endDate = datetime.datetime.strptime(end+' 23:59:59',"%Y-%m-%d %H:%M:%S")
    except:
        endDate = utils.getDateNow(8)
    try:
        beginDate = datetime.datetime.strptime(begin,"%Y-%m-%d")
        beginDate = utils.onlyDate(beginDate)
    except:
        beginDate = endDate - datetime.timedelta(days=7)
    begin = beginDate.strftime("%Y-%m-%d")
    end = endDate.strftime("%Y-%m-%d")
    statIn = None
    statPay = None
    query = Q(city=login_teacher.cityId)&Q(deleted__ne=True)&Q(isY19=True)
    branches = Branch.objects.filter(query)  # @UndefinedVariable
    bdata = {}

    for b in branches:

        bd = {}
        bd['sn'] = str(b.sn)
        bd['branch'] = str(b.id)
        bd['branchName'] = b.branchName
        bd['dayIn'] = 0
        bd['dayReg'] = 0
        bd['dayAdd'] = 0
        bd['lifeCard'] = 0
        bd['lifeCardIncome'] = 0
        bd['biyearCard'] = 0
        bd['biyearCardIncome'] = 0
        bd['yearCard'] = 0
        bd['yearCardIncome'] = 0
        bd['monthCard'] = 0
        bd['monthCardIncome'] = 0
        bd['staffCard'] = 0
        bd['staffCardIncome'] = 0
        bd['reCard'] = 0
        bd['reCardIncome'] = 0
        bd['memberCard'] = 0
        bd['memberIncome'] = 0
        bd['allCard'] = 0
        bd['allCardIncome'] = 0
        bdata[str(b.id)] = bd
    ci = 0
    query = Q(day__gte=beginDate)&Q(day__lte=endDate)
    qcity = None
    for b in branches:
            if ci == 0:
                qcity = Q(branch=str(b.id))
            else:
                qcity = qcity|Q(branch=str(b.id))
            ci = ci + 1
    query = query&(qcity)
    indata = Y19data.objects.filter(query).order_by('branch')
    for i in indata:

        if i.dayInToday:
            bdata[i.branch]['dayIn'] = bdata[i.branch]['dayIn'] + i.dayInToday
        if i.dayRegToday:
            bdata[i.branch]['dayReg'] = bdata[i.branch]['dayReg'] + i.dayRegToday
        if i.dayAdd:
            bdata[i.branch]['dayAdd'] = bdata[i.branch]['dayAdd'] + i.dayAdd
    query = Q(payDate__gte=beginDate)&Q(payDate__lte=endDate)&(qcity)
    incomedata = Y19Income.objects.filter(query).order_by('branch')
    for c in incomedata:
        if c.paid > 0:

            if c.type == u'月卡':
                bdata[c.branch]['monthCard'] = bdata[c.branch]['monthCard'] + 1
                bdata[c.branch]['monthCardIncome'] = bdata[c.branch]['monthCardIncome'] + c.paid
            if c.type == u'年卡':
                bdata[c.branch]['yearCard'] = bdata[c.branch]['yearCard'] + 1
                bdata[c.branch]['yearCardIncome'] = bdata[c.branch]['yearCardIncome'] + c.paid
            if c.type == u'两年卡':

                bdata[c.branch]['biyearCard'] = bdata[c.branch]['biyearCard'] + 1
                bdata[c.branch]['biyearCardIncome'] = bdata[c.branch]['biyearCardIncome'] + c.paid

            if c.type == u'终身卡':
                bdata[c.branch]['lifeCard'] = bdata[c.branch]['lifeCard'] + 1
                bdata[c.branch]['lifeCardIncome'] = bdata[c.branch]['lifeCardIncome'] + c.paid
            if c.type == u'续费':
                bdata[c.branch]['reCard'] = bdata[c.branch]['reCard'] + 1
                bdata[c.branch]['reCardIncome'] = bdata[c.branch]['reCardIncome'] + c.paid
            if c.type == u'员工卡':
                bdata[c.branch]['staffCard'] = bdata[c.branch]['staffCard'] + 1
                bdata[c.branch]['staffCardIncome'] = bdata[c.branch]['staffCardIncome'] + c.paid
            if c.type != u'员工卡':
                bdata[c.branch]['allCard'] = bdata[c.branch]['allCard'] + 1
                bdata[c.branch]['allCardIncome'] = bdata[c.branch]['allCardIncome'] + c.paid
        if c.type == u'终身卡' and len(c.contractId) > 1:
                bdata[c.branch]['memberCard'] = bdata[c.branch]['memberCard'] + 1


    temp = []
    for b in branches:
        temp.append(bdata[str(b.id)])
    return render(request, 'Y19stat.html',{"login_teacher":login_teacher,"stat":temp,"beginDate":begin,"endDate":end})

def Y19WeekStat(request):
    login_teacher = checkCookie(request)
    if not (login_teacher):
        return HttpResponseRedirect('/login')
    if str(login_teacher.branchType) != str(constant.BranchType.management):
        return HttpResponseRedirect('/noright')
    temp = []
    now = utils.getDateNow(8)
    weekBegin = utils.onlyDate(utils.getWeekBegin(now, False))
    weekEnd = utils.onlyDate(weekBegin + datetime.timedelta(days=8))
    monthBegin = utils.getThisMonthBegin(now)
    monthEnd = utils.monthLastDay(now)
    query = Q(city=login_teacher.cityId)&Q(isY19=True)
    branches = Branch.objects.filter(query).order_by('sn')  # @UndefinedVariable
    temp = []
    for branch in branches:
        if True:#branch.isY19:
            begin = weekBegin
            map = {}
            map['branchName'] = branch.branchName
            data = []
            for i in range(7):

                if i > 0:
                    begin = begin+timedelta(days=1)
                end = begin+timedelta(days=1)

                query = Q(payDate__gte=begin)&Q(payDate__lt=end)&Q(branch=str(branch.id))&Q(paid__gt=0)&Q(type__ne=u'员工卡')
                re = Y19Income.objects.filter(query)

                num = len(re)#Y19Income.objects.filter(query).count()
                #if num > 0:
                 #   print branch.branchName + ':' + str(num)

                data.append(num)
            query = Q(payDate__gte=weekBegin)&Q(payDate__lt=weekEnd)&Q(branch=str(branch.id))&Q(paid__gt=0)&Q(type__ne=u'员工卡')
            num = Y19Income.objects.filter(query).count()
            data.append(num)
            query = Q(payDate__gte=monthBegin)&Q(payDate__lte=monthEnd)&Q(branch=str(branch.id))&Q(paid__gt=0)&Q(type__ne=u'员工卡')
            num = Y19Income.objects.filter(query).count()
            data.append(num)
            query = Q(branch=str(branch.id))&Q(paid__gt=0)&Q(type__ne=u'员工卡')
            num = Y19Income.objects.filter(query).count()
            data.append(num)
            map['data'] = data

            temp.append(map)
    return render(request, 'Y19WeekStat.html',{"login_teacher":login_teacher,"stat":temp})


def Y19statTeacher(request):
    login_teacher = checkCookie(request)
    if not (login_teacher):
        return HttpResponseRedirect('/login')
    begin = request.GET.get("beginDate")
    end = request.GET.get("endDate")
    beginDate = None
    endDate = None
    try:
        endDate = datetime.datetime.strptime(end+' 23:59:59',"%Y-%m-%d %H:%M:%S")
    except:
        endDate = utils.getDateNow(8)
    try:
        beginDate = datetime.datetime.strptime(begin,"%Y-%m-%d")
        beginDate = utils.onlyDate(beginDate)
    except:
        beginDate = endDate - datetime.timedelta(days=7)
    begin = beginDate.strftime("%Y-%m-%d")
    end = endDate.strftime("%Y-%m-%d")
    #statIn = None
    statPay = None
    query = Q(city=login_teacher.cityId)&Q(deleted__ne=True)
    branches = Branch.objects.filter(query)  # @UndefinedVariable
    ci = 0

    qcity1 = None
    qcity2 = None
    for b in branches:
            bid = str(b.id)

            if ci == 0:
                qcity2 = Q(branch=bid)
                qcity1 = Q(branch=b.id)
            else:
                qcity2 = qcity2|Q(branch=bid)
                qcity1 = qcity1|Q(branch=b.id)
            ci = ci + 1

    q2 = Q(payDate__gte=beginDate)&Q(payDate__lte=endDate)&Q(type__ne='员工卡')
    if str(login_teacher.branchType) != str(constant.BranchType.management) or request.GET.get('stat') == '1':

        qcity1 = Q(branch=login_teacher.branch)
        qcity2 = Q(branch=login_teacher.branch)
        q2 = q2&qcity2
    query = (qcity1)&Q(isY19=True)
    teachers = Teacher.objects.filter(query).order_by("branch")  # @UndefinedVariable
    bdata = {}

    for b in teachers:

        bd = {}
        bd['branch'] = str(b.branch.id)
        bd['branchName'] = b.branch.branchName
        bd['teacher'] = b.name
        #bd['dayIn'] = 0
        #bd['dayReg'] = 0
        #bd['dayAdd'] = 0
        bd['lifeCard'] = 0
        bd['lifeCardIncome'] = 0
        bd['biyearCard'] = 0
        bd['biyearCardIncome'] = 0
        bd['yearCard'] = 0
        bd['yearCardIncome'] = 0
        bd['monthCard'] = 0
        bd['monthCardIncome'] = 0
        bd['staffCard'] = 0
        bd['staffCardIncome'] = 0
        bd['reCard'] = 0
        bd['reCardIncome'] = 0
        bd['allCard'] = 0
        bd['allCardIncome'] = 0
        bd['get'] = 0
        bdata[str(b.id)] = bd


    #===========================================================================
    # indata = Y19data.objects.filter(query).order_by('branch')
    # for i in indata:
    #
    #     if i.dayInToday:
    #         bdata[i.branch]['dayIn'] = bdata[i.branch]['dayIn'] + i.dayInToday
    #     if i.dayRegToday:
    #         bdata[i.branch]['dayReg'] = bdata[i.branch]['dayReg'] + i.dayRegToday
    #     if i.dayAdd:
    #         bdata[i.branch]['dayAdd'] = bdata[i.branch]['dayAdd'] + i.dayAdd
    #===========================================================================

    incomedata = Y19Income.objects.filter(q2).order_by('branch')

    for c in incomedata:
        if c.paid > 0:
            try:
                bdata[c.sellerId]
            except:
                b = None
                tname = None
                teacherss = Teacher.objects.filter(id=c.sellerId)  # @UndefinedVariable
                if teacherss:

                    b = teacherss[0].branch
                    tname = teacherss[0].name
                else:
                    continue
                bd = {}
                bd['branch'] = str(b.id)
                bd['branchName'] = b.branchName
                bd['teacher'] = tname
        #bd['dayIn'] = 0
        #bd['dayReg'] = 0
        #bd['dayAdd'] = 0
                bd['lifeCard'] = 0
                bd['lifeCardIncome'] = 0
                bd['biyearCard'] = 0
                bd['biyearCardIncome'] = 0
                bd['yearCard'] = 0
                bd['yearCardIncome'] = 0
                bd['monthCard'] = 0
                bd['monthCardIncome'] = 0
                bd['staffCard'] = 0
                bd['staffCardIncome'] = 0
                bd['reCard'] = 0
                bd['reCardIncome'] = 0
                bd['allCard'] = 0
                bd['allCardIncome'] = 0
                bd['get'] = 0

                bdata[c.sellerId] = bd
                #print bdata[c.sellerId]

                #print 'NO this teacher'
                #continue

            if c.type == u'月卡':
                bdata[c.sellerId]['monthCard'] = bdata[c.sellerId]['monthCard'] + 1
                bdata[c.sellerId]['monthCardIncome'] = bdata[c.sellerId]['monthCardIncome'] + c.paid
            if c.type == u'年卡':
                bdata[c.sellerId]['yearCard'] = bdata[c.sellerId]['yearCard'] + 1
                bdata[c.sellerId]['yearCardIncome'] = bdata[c.sellerId]['yearCardIncome'] + c.paid
            if c.type == u'两年卡':

                bdata[c.sellerId]['biyearCard'] = bdata[c.sellerId]['biyearCard'] + 1
                bdata[c.sellerId]['biyearCardIncome'] = bdata[c.sellerId]['biyearCardIncome'] + c.paid

            if c.type == u'终身卡':
                bdata[c.sellerId]['lifeCard'] = bdata[c.sellerId]['lifeCard'] + 1
                bdata[c.sellerId]['lifeCardIncome'] = bdata[c.sellerId]['lifeCardIncome'] + c.paid
            if c.type == u'续费':
                bdata[c.sellerId]['reCard'] = bdata[c.sellerId]['reCard'] + 1
                bdata[c.sellerId]['reCardIncome'] = bdata[c.sellerId]['reCardIncome'] + c.paid
            if c.type == u'员工卡':
                bdata[c.sellerId]['staffCard'] = bdata[c.sellerId]['staffCard'] + 1
                bdata[c.sellerId]['staffCardIncome'] = bdata[c.sellerId]['staffCardIncome'] + c.paid
            if c.type != u'员工卡' :
                add = 0
                if c.paid > 500 and c.paid < 900:
                    add = 100
                if c.paid >= 900 and c.paid < 1500:
                    add = 200
                if c.paid >= 1500:
                    add = 300
                bdata[c.sellerId]['get'] = bdata[c.sellerId]['get'] + add

                bdata[c.sellerId]['allCard'] = bdata[c.sellerId]['allCard'] + 1
                bdata[c.sellerId]['allCardIncome'] = bdata[c.sellerId]['allCardIncome'] + c.paid

    return render(request, 'Y19statTeacher.html',{"login_teacher":login_teacher,"stat":bdata,"beginDate":begin,"endDate":end})


def incomes(request):
    login_teacher = checkCookie(request)
    if not (login_teacher):
        return HttpResponseRedirect('/login')
    if login_teacher.branchType != '0' and login_teacher.branch != constant.BJ_CAIWU:
        return HttpResponseRedirect('/login')
    backurl = request.COOKIES.get('backurl','')
    if not backurl:
        backurl = request.COOKIES.get('mainurl','')
    #学生缴费带过来的ID
    studentId = request.GET.get("studentId")
    student = None
    try:
        if studentId:
            student = Student.objects.get(id=studentId)  # @UndefinedVariable
    except:
        student = None
    #收入查询query
    searchCity = request.GET.get("searchCity")
    if searchCity == '0':
        searchCity = None
    searchBranch = login_teacher.branch
    isFinance = utils.isFinance(login_teacher.branch)
    if isFinance:
        isFinance = True
        searchBranch = None
        if not searchCity:
            searchCity = constant.BEIJING
    query = None
    if searchBranch:
        query = Q(branchId=searchBranch)
    else:
        query = Q(cityId=searchCity)

    searchType = request.GET.get("type")
    if searchType:
        query = query&Q(type=searchType)
    else:
        searchType = ''
    searchPaymethod = request.GET.get("paymethod")
    if searchPaymethod:
        query = query&Q(paymethod=searchPaymethod)
    else:
        searchPaymethod = ''
    datenow = utils.getDateNow(8)
    beginDate = request.GET.get("beginDate")
    endDate = request.GET.get("endDate")
    bDate = None
    eDate = None

    searchStatus = request.GET.get("searchStatus")
    if searchStatus:
        query = query&Q(status=searchStatus)
    else:
        query = query&Q(status__ne=constant.ContractStatus.delete)

    if beginDate:
        try:
            bDate = datetime.datetime.strptime(beginDate,"%Y-%m-%d")
        except:
            bDate = None
    if endDate:
        try:
            eDate = datetime.datetime.strptime(endDate,"%Y-%m-%d")
            eDate = eDate + timedelta(days=1)
        except:
            eDate = None
    if not bDate and not eDate:
        eDate = datenow

        now = datetime.datetime.strptime(datenow.strftime("%Y-%m-%d")+' 00:00:00',"%Y-%m-%d %H:%M:%S")

        bDate = now + timedelta(days=-90)

    if bDate:
        query = query&Q(payDate__gte=bDate)
        beginDate = bDate.strftime("%Y-%m-%d")
    if eDate:
        endDate = eDate.strftime("%Y-%m-%d")
        query = query&Q(payDate__lt=eDate)

    cities = City.objects.all().order_by("sn")  # @UndefinedVariable
    incomes = Income.objects.filter(query).order_by('-payDate')  # @UndefinedVariable
    temp = []
    sum = 0
    for inc in incomes:
        try:
            inc.branchName = Branch.objects.get(id=inc.branchId).branchName  # @UndefinedVariable
            temp.append(inc)
            sum = sum + inc.paid
        except:
            err = 1
    incomes = temp
    return render(request, 'incomes.html',{"login_teacher":login_teacher,"datenow":datenow,
                                           "beginDate":beginDate,
                                             "endDate":endDate,
                                             "searchType":searchType,"searchCity":searchCity,"searchPaymethod":searchPaymethod,
                                             "INCOME_TYPE":utils.constant.INCOME_TYPE,"paymethods":utils.constant.PAY_METHOD,
                                             "student":student,"cities":cities,
                                             "backurl":backurl,"isFinance":isFinance,
                                             "sum":sum,"length":len(incomes),
                                           "incomes":incomes})

#添加新收入
@csrf_exempt
def api_income(request):

    login_teacher = checkCookie(request)
    if not (login_teacher):
        return HttpResponseRedirect('/login')
    paymethod = request.POST.get("paymethod")
    hasPaymethod = False
    if paymethod:
        try:
            utils.constant.PAY_METHOD[paymethod]
            hasPaymethod = True
        except:
            hasPaymethod = False
    else:
        hasPaymethod = False
    if not hasPaymethod:
        res = {"error": 1, "msg": "付款方式有误，无法保存合同"}
        response = http.JSONResponse(json.dumps(res, ensure_ascii=False))
        return response
    id = request.POST.get("id")
    payer = request.POST.get('payer')
    studentId = request.POST.get('studentId')
    receipterId = request.POST.get('receipter') #收款人ID
    type = request.POST.get('type') #类号

    typeName = constant.INCOME_TYPE[type]

    payDate = request.POST.get('payDate')
    paid = request.POST.get('paid')
    memo = request.POST.get('memo')
    status = constant.ContractStatus.sign
    income = Income()
    pdate = None
    try:
        pdate = datetime.datetime.strptime(payDate,"%Y-%m-%d")
        income.payDate = pdate

    except Exception,e:
        print e
        res = {"error": 1, "msg": "日期错误"}
        return http.JSONResponse(json.dumps(res, ensure_ascii=False))
    paidf = float(paid)
    datenow = utils.getDateNow(8)
    #expireTime = utils.getThisMonthBegin(utils.monthLastDay(pdate)+datetime.timedelta(days=1))+timedelta(days=constant.SIGN_CLASS_EXPIRE_DAY)
    #print 'et1'
    #print expireTime


    expireTime = utils.subtract_one_month(datenow)
    if int(datenow.strftime("%d")) > constant.SIGN_CLASS_EXPIRE_DAY:
        expireTime = utils.getThisMonthBegin(datenow)
    print 'et2'
    print expireTime


    if not id and pdate < expireTime and login_teacher.id != login_teacher.cityRB:
        res = {"error": 1, "msg": "付款日期有误，上月的收入不能再录入了！"}
        response = http.JSONResponse(json.dumps(res, ensure_ascii=False))
        return response

    if id:
        try:
            status = int(request.POST.get('status'))
        except Exception,e:
            print e
            res = {"error": 1, "msg": "状态错误"}
            return http.JSONResponse(json.dumps(res, ensure_ascii=False))


    if id:

        query = Q(id=id)
        try:
            income = Income.objects.get(query)  # @UndefinedVariable

            #expireTime = utils.getThisMonthBegin(utils.monthLastDay(income.payDate)+datetime.timedelta(days=1))+timedelta(days=constant.SIGN_CLASS_EXPIRE_DAY)
            if  income.payDate < expireTime and income.payDate != pdate and login_teacher.id != login_teacher.cityRB:
                res = {"error": 1, "msg": "修改期已过，不能修改付款日期！"}
                response = http.JSONResponse(json.dumps(res, ensure_ascii=False))
                return response
            if  income.payDate < expireTime and income.paid != paidf and login_teacher.id != login_teacher.cityRB:
                res = {"error": 1, "msg": "合同修改期已过，不能修改金额！"}
                response = http.JSONResponse(json.dumps(res, ensure_ascii=False))
                return response
            if  income.payDate < expireTime and income.status != status and login_teacher.id != login_teacher.cityRB:
                    res = {"error": 1, "msg": "修改期已过，不能作废！"}
                    response = http.JSONResponse(json.dumps(res, ensure_ascii=False))
                    return response

            try:
                pdate = datetime.datetime.strptime(payDate,"%Y-%m-%d")
                income.payDate = pdate

            except Exception,e:
                print e
                res = {"error": 1, "msg": "日期错误"}
                return http.JSONResponse(json.dumps(res, ensure_ascii=False))
        except Exception,e:
            print e
            res = {"error": 1, "msg": "未找到要修改的收入记录"}
            return http.JSONResponse(json.dumps(res, ensure_ascii=False))

    #同一人同一日期同一种类不能重复录入
    if status != constant.ContractStatus.delete:
      query = Q(payer=payer)&Q(payDate=income.payDate)&Q(type=type)

      incomes = Income.objects.filter(query)  # @UndefinedVariable

      if len(incomes) > 0: #新录入查重
        if id:
            for  i in incomes:
                print i.type
                if str(i.id) != str(income.id):
                    res = {"error": 1, "msg": "已录入"}
                    return http.JSONResponse(json.dumps(res, ensure_ascii=False))
        else:
            res = {"error": 1, "msg": "已录入"}
            return http.JSONResponse(json.dumps(res, ensure_ascii=False))

    income.status = status
    if not income.branchId:
        income.branchId = login_teacher.branch
        income.cityId = login_teacher.cityId
    income.memo = memo
    income.type = type
    income.typeName = typeName

    try:
        if studentId and len(studentId) > 1:
            s = Student.objects.get(id=studentId)  # @UndefinedVariable
            income.studentId = str(s.id)
    except Exception,e:
        print e
        err = 1

    try:
        income.paid = float(paid)
    except Exception,e:
        print e
        res = {"error": 1, "msg": "金额错误"}
        return http.JSONResponse(json.dumps(res, ensure_ascii=False))



    income.payer = payer
    income.receipterId = receipterId
    openId = None
    if status == constant.ContractStatus.refundWaiting:
        income.refundAppDate = getDateNow()
        income.refundApprove = constant.RefundStatus.waiting
        refundStr = request.POST.get("refund")
        refund = 0
        if refundStr:
            try:
                refund = int(float(refundStr))
                if refund > income.paid:
                    res = {"error": 1, "msg": "退款金额不能大于付款金额"}
                    return http.JSONResponse(json.dumps(res, ensure_ascii=False))
            except Exception,e:
                print e
                res = {"error": 1, "msg": "退款金额错误"}
                return http.JSONResponse(json.dumps(res, ensure_ascii=False))

        #获取财务处理人，准备发微信通知
        query = Q(id=login_teacher.cityFA)
        try:
            toTeacher = Teacher.objects.get(query)  # @UndefinedVariable
            if toTeacher and toTeacher.openId:
                openId = toTeacher.openId
        except:
            err = 1
    income.paymethod = paymethod

    income.save()

    res = {"error": 0, "msg": "OK","openId":openId}
    return http.JSONResponse(json.dumps(res, ensure_ascii=False))

#修改收入或者退款页面
def income(request):
    login_teacher = checkCookie(request)
    if not (login_teacher):
        return HttpResponseRedirect('/login')
    id = request.GET.get("id")
    query = Q(id=id)
    datenow = utils.getDateNow(8)
    income = Income.objects.get(query)  # @UndefinedVariable

    return render(request, 'income.html',{"login_teacher":login_teacher,"datenow":datenow,
                                          "CONTRACT_STATUS":utils.constant.CONTRACT_STATUS,
                                          "INCOME_TYPE":utils.constant.INCOME_TYPE,"paymethods":utils.constant.PAY_METHOD,
                                           "income":income})

def deposits(request):

    login_teacher = checkCookie(request)
    if not (login_teacher):
        return HttpResponseRedirect('/login')
    backurl = request.COOKIES.get('backurl','')
    deposits = None
    searchCity = request.GET.get('searchCity')
    searchCompany = request.GET.get('searchCompany')#是否已存
    searchStatus = request.GET.get('searchStatus')
    depositWay = request.GET.get('depositWay')
    cityId = constant.BEIJING
    if searchCity:
        try:
            city = City.objects.get(id=searchCity)  # @UndefinedVariable
            cityId = str(city.id)
        except:
            cityId = constant.BEIJING

    branchs = utils.getCityBranch(cityId)
    query = Q(deposit__gt=0)
    if depositWay == 'A' or depositWay == 'B' or depositWay == 'C':
        query = query&Q(depositWay=depositWay)
    else:
       depositWay = ''
    if searchStatus:
        query = query&Q(depositStatus=searchStatus)
    else:
        searchStatus = ''
    if searchCompany:
        query = query&Q(depositCompany=searchCompany)
    else:
        searchCompany = ''

    datenow = utils.getDateNow(8)
    beginDate = request.GET.get("beginDate")
    endDate = request.GET.get("endDate")
    bDate = None
    eDate = None
    if beginDate:
        try:
            bDate = datetime.datetime.strptime(beginDate,"%Y-%m-%d")
        except:
            bDate = None
    if endDate:
        try:
            eDate = datetime.datetime.strptime(endDate,"%Y-%m-%d")
            eDate = eDate + timedelta(days=1)
        except:
            eDate = None
    if not bDate and not eDate:
        eDate = datenow

        now = datetime.datetime.strptime(datenow.strftime("%Y-%m-%d")+' 00:00:00',"%Y-%m-%d %H:%M:%S")

        bDate = now + timedelta(days=-30)

    if bDate:
        query = query&Q(depositDate__gte=bDate)
        beginDate = bDate.strftime("%Y-%m-%d")
    if eDate:
        endDate = eDate.strftime("%Y-%m-%d")
        query = query&Q(depositDate__lt=eDate)

    queryBranch = None
    i = 0
    for b in branchs:
        if i == 0:
            queryBranch = Q(branch=b.id)
        else:
            queryBranch = queryBranch|Q(branch=b.id)
        i = i + 1
    query = query&(queryBranch)
    deposits = Student.objects.filter(query).order_by('branch','-depositDate')  # @UndefinedVariable
    sum = 0
    for d in deposits:
        sum = sum + d.deposit
    cities = City.objects.all().order_by('sn')  # @UndefinedVariable
    return render(request, 'deposits.html', {"login_teacher":login_teacher,
                                             "backurl":backurl,
                                             "deposits": deposits,
                                             "searchCity":cityId,
                                             "searchStatus":searchStatus,
                                             "cities":cities,
                                            "beginDate":beginDate,
                                             "endDate":endDate,
                                             "paymethods":constant.PAY_METHOD,
                                             "depositWay":depositWay,
                                             "length":len(deposits),
                                             "searchCompany":searchCompany,
                                             "sum":sum
                                             })


def duePay(request):
    login_teacher = checkCookie(request)
    if not (login_teacher):
        return HttpResponseRedirect('/login')
    nextMonth = utils.getDateNow(8)+timedelta(days=30)
    query = Q(branch=login_teacher.branch)&Q(singDate=None)&Q(dueDate__lt=nextMonth)
    duePays = Contract.objects.filter(query).order_by('dueDate')  # @UndefinedVariable
    temp = []
    for contract in duePays:
        student = Student.objects.get(id=contract.student_oid)  # @UndefinedVariable
        if student.status != constant.StudentStatus.sign:
            continue
        contract.regName = ''
        if student.name:
            contract.regName = student.name
        if student.name2:
            contract.regName = contract.regName +' '+student.name2
        contract.mobile = student.prt1mobile
        temp.append(contract)




    response = render(request, 'duePay.html',{"login_teacher":login_teacher,
                                           "duePays":temp})
    response.set_cookie("mainurl",'/go2/contract/studentContract')
    contractFrom = request.path + '?' + request.META['QUERY_STRING']
    response.set_cookie("contractFrom",contractFrom)
    return response


def AllduePay(request):
    login_teacher = checkCookie(request)
    if not (login_teacher):
        return HttpResponseRedirect('/login')

    if str(login_teacher.branchType) != str(constant.BranchType.function):
        return HttpResponseRedirect('/noright')
    cityId = request.GET.get("cityId")
    if not cityId:
        cityId = constant.BEIJING
    cities = City.objects.all()  # @UndefinedVariable
    branches = utils.getCityBranch(cityId, None, 1)
    qbranch = Q(branch=branches[0].id)
    i = 0
    for b in branches:
        if i > 0:
            qbranch = qbranch|Q(branch=branches[i])
        i = i + 1


    nextMonth = utils.getDateNow(8)+timedelta(days=30)
    query = Q(singDate=None)&Q(dueDate__lt=nextMonth)&qbranch
    duePays = Contract.objects.filter(query).order_by('branch','dueDate')  # @UndefinedVariable
    temp = []
    for contract in duePays:
        student = Student.objects.get(id=contract.student_oid)  # @UndefinedVariable
        contract.regName = ''
        if student.name:
            contract.regName = student.name
        if student.name2:
            contract.regName = contract.regName +' '+student.name2
        contract.mobile = student.prt1mobile
        #print  contract.branch.branchName
        temp.append(contract)

    response = render(request, 'AllduePay.html',{"login_teacher":login_teacher,
                                           "duePays":temp,"cities":cities,"selectCity":cityId})
    response.set_cookie("mainurl",'/go2/contract/studentContract')
    contractFrom = request.path + '?' + request.META['QUERY_STRING']
    response.set_cookie("contractFrom",contractFrom)
    return response

def api_Y19dayIn(request):
  try:
    reload(sys)
    sys.setdefaultencoding('utf8')  # @UndefinedVariable
    print 'inlaaaaaa'
    login_teacher = checkCookie(request)
    if not (login_teacher):
        return HttpResponseRedirect('/login')

    dayIns = request.POST.get("dayIns")
    dayRegs = request.POST.get("dayRegs")
    dayAdds = request.POST.get("dayAdds")

    dayins = dayIns.split('__')
    dayregs = dayRegs.split('__')
    dayadds = dayAdds.split('__')
    print '------------dayAdds---------------'
    print dayAdds
    day = utils.getDateNow(8)
    day = utils.onlyDate(day)

    for dayIn in dayins:
        bi = dayIn.split('|')
        t = bi[0]
        teacher = None
        try:
            teacher = Teacher.objects.get(username=t)  # @UndefinedVariable
        except:
            teacher = None
            break
        di = None
        if len(bi) > 1:
          di = bi[1]
          print di
        dr = None
        da = None
        print 'inlaaaaaa-------3'
        for dayReg in dayregs:
            bii = dayReg.split('|')
            ti = bii[0]
            if t == ti:
                if len(bii) > 1:
                    dr = bii[1]
                break
        for dayAdd in dayadds:
            print dayAdd
            aii = dayAdd.split('|')
            ti = aii[0]
            if t == ti:
                if len(aii) > 1:
                    da = aii[1]
                    print da
                break
        print 'inlaaaaaa-------4'
        query = Q(day=day)&Q(teacher=str(teacher.id))
        try:
            print '[---------------GET IF DUP----------------]'
            print str(teacher.id)
            print day
            y19data = Y19data.objects.get(query)
            #print len(y19data)
            #print y19data._query
            print y19data
            print 'ok'

        except:
            y19data = Y19data()
            y19data.branch = login_teacher.branch
            y19data.branchName = login_teacher.branchName
            y19data.teacher = str(teacher.id)
            y19data.teacherName = teacher.name
            y19data.day = day

        try:
            y19data.dayIn = int(di)
            y19data.dayReg = int(dr)
            y19data.dayAdd = int(da)
            query = Q(teacher=str(teacher.id))&Q(day__lt=day)
            last = Y19data.objects.filter(query).order_by("-day")
            if len(last) > 0:
                l = last[0]
                try:
                    y19data.dayInToday = y19data.dayIn - l.dayIn
                except:
                    err = 1
                try:
                    y19data.dayRegToday = y19data.dayReg - l.dayReg
                except:
                    err = 1
            y19data.save()
        except Exception,e:
            print e
        print 'inlaaaaaa-------6'
    print 'inlaaaaaa-------7'
    res = {"error": 0}
  except Exception,e:
      res = {"error":1,"msg":str(e)}
  return http.JSONResponse(json.dumps(res, ensure_ascii=False))

@csrf_exempt
def api_y19fee(request):
    print '1'
    ret = 0
    msg = u'已收款'
    login_teacher = checkCookie(request)
    print '2'
    if not (login_teacher):
        res = {"error":1,"msg":"未登录"}
        return http.JSONResponse(json.dumps(res, ensure_ascii=False))
    id = request.POST.get('id')
    print '3'
    done = request.POST.get('done')
    print '4'
    try:
        c = Y19Income.objects.get(id=id)  # @UndefinedVariable
        if done == '1':
            c.appFee = True
        else:
            msg = u'未收款'
            c.appFee = False
            if c.appDone == True:
                c.appDone = False
        print '5'
        c.save()
        print '6'

    except Exception,e:
        msg = str(e)
        ret = 1
    res = {"error": ret,"msg":msg}
    return http.JSONResponse(json.dumps(res, ensure_ascii=False))

@csrf_exempt
def api_y19done(request):
    ret = 0
    msg = u'已开通'
    login_teacher = checkCookie(request)
    if not (login_teacher):
        res = {"error":1,"msg":"未登录"}
        return http.JSONResponse(json.dumps(res, ensure_ascii=False))
    id = request.POST.get('id')
    done = request.POST.get('done')
    try:
        c = Y19Income.objects.get(id=id)  # @UndefinedVariable
        if done == '1' and c.appFee:
            c.appDone = True
        elif done == '1' and not c.appFee:
            msg = u'财务未收款，不能开通'
            ret = 1
            c.appDone = False
        else:
            msg = u'未开通'
            c.appDone = False
        c.save()
    except Exception,e:
        msg = str(e)
        ret = 1
    res = {"error": ret,"msg":msg}
    return http.JSONResponse(json.dumps(res, ensure_ascii=False))
