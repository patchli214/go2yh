#!/usr/bin/env python
# -*- coding:utf-8 -*-
import json,datetime,time,itertools
import sys,operator,os
from bson import ObjectId
from mongoengine.queryset.visitor import Q
from go2.settings import BASE_DIR,USER_IMAGE_DIR
from regUser.models import Student,StudentFile,Contract, StudentTrack
from branch.models import Branch,City, Reimburse, ReimburseItem
from teacher.models import Teacher

from operator import attrgetter
from django.shortcuts import render,render_to_response
from django.http import HttpResponse,HttpResponseRedirect
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from tools.utils import checkCookie,getDateNow
from tools import http, utils, constant

from tools.sign import Sign
from student.models import Receipt

def refundWaitingList(request):
  login_teacher = None
  temp = ''
  millis = 0
  try:  
    login_teacher = checkCookie(request)
    if not (login_teacher):
        return HttpResponseRedirect('/login')
    if login_teacher.id != login_teacher.cityFA:
        return HttpResponseRedirect('/login')
    cities = City.objects.filter(financialAdmin=login_teacher.id)  # @UndefinedVariable
    faBranches = []
    qb = None
    if cities:
        i = 0
        for c in cities:
            if i == 0:
                qb = Q(city=c.id)
            else:
                qb = qb|Q(city=c.id)
            i = i + 1
    faBranches = Branch.objects.filter(qb)  # @UndefinedVariable
    qb = None
    i = 0
    for b in faBranches:
        if i == 0:
            qb = Q(branch=b.id)
        else:
            qb = qb|Q(branch=b.id)
        i = i + 1
    query = Q(status=constant.ContractStatus.refundWaiting)&Q(refundApprove__ne=constant.RefundStatus.reject)&Q(refundApprove__ne=constant.RefundStatus.approved)&(qb)
    
    refunds = Contract.objects.filter(query).order_by("-refundAppDate")    # @UndefinedVariable

    temp = []
    for r in refunds:
        query = Q(contractId=str(r.id))&Q(fileType=constant.FileType.refundApp)
        try:
            files = StudentFile.objects.filter(query)  # @UndefinedVariable
            
            file = files[0]
            r.pic = file.filepath + file.filename
            
        except:
            r.pic = None
        if r.student_oid:
            try:
                r.student = Student.objects.get(id=r.student_oid)  # @UndefinedVariable
                allLessons,sd,lessonLeft = utils.getLessonLeft(r.student)
                r.lessonLeft = lessonLeft
            except:
                err = 1
            try:
                r.receipt = 0
                query = Q(student=r.student_oid)
                receipts = Receipt.objects.filter(query)  # @UndefinedVariable
                rsum = 0
                for rr in receipts:
                    rsum = rsum + rr.sum
                r.receipt = rsum

            except:
                r.receipt = 0
        temp.append(r)
    millis = int(round(time.time() * 1000))

  except Exception,e:
      print e
  return render(request, 'refundWaitingList.html', {"login_teacher":login_teacher,"timenow":millis,
                                                  "refunds":temp,"sum":len(temp)})


def refundApprovedList(request):
    login_teacher = checkCookie(request)
    if not (login_teacher):
        return HttpResponseRedirect('/login')
    if login_teacher.id != login_teacher.cityFR:
        return HttpResponseRedirect('/login')
    query = Q(financialRefund=login_teacher.id)
    cities = City.objects.filter(query)  # @UndefinedVariable
    query = None
    i = 0
    for city in cities:
        if i == 0:
            query = Q(city=city.id)
        else:
            query = query|Q(city=city.id)
        i = i + 1
    branches = Branch.objects.filter(query)  # @UndefinedVariable
    query = None
    i = 0
    for b in branches:
        if i == 0:
            query = Q(branch=b.id)
        else:
            query = query|Q(branch=b.id)
        i = i + 1
    query = Q(status=constant.ContractStatus.refundWaiting)&Q(refundApprove=constant.RefundStatus.approved)&(query)
    
    refunds = Contract.objects.filter(query).order_by("-refundAppDate")    # @UndefinedVariable
    temp = []
    for r in refunds:
        query = Q(contractId=str(r.id))&Q(fileType=constant.FileType.refundApp)
        try:
            files = StudentFile.objects.filter(query)  # @UndefinedVariable
            
            file = files[0]
            r.pic = file.filepath + file.filename
            
        except:
            r.pic = None
        if r.student_oid:
            try:
                r.student = Student.objects.get(id=r.student_oid)  # @UndefinedVariable
                allLessons,sd,lessonLeft = utils.getLessonLeft(r.student)
                r.lessonLeft = lessonLeft
            except:
                r.student = None
            try:
                r.receipt = 0
                query = Q(student=r.student_oid)
                receipts = Receipt.objects.filter(query)  # @UndefinedVariable
                rsum = 0
                for rr in receipts:
                    rsum = rsum + rr.sum
                r.receipt = rsum
            except:
                r.receipt = 0
        temp.append(r)

    return render(request, 'refundApprovedList.html', {"login_teacher":login_teacher,
                                                  "refunds":temp,"sum":len(temp)})
#待开票列表
def receiptRequire(request):
    login_teacher = checkCookie(request)
    if not (login_teacher):
        return HttpResponseRedirect('/login')
    if login_teacher.id != login_teacher.cityRT:
        return HttpResponseRedirect('/login')
    dateNow = utils.getDateNow()
    query = Q(financialReceipt=login_teacher.id)
    cities = City.objects.filter(query)  # @UndefinedVariable
    i = 0
    for city in cities:
        if i == 0:
            query = Q(city=city.id)
        else:
            query = query|Q(city=city.id)
        i = i + 1
    
    query = Q(status=None)|Q(status=0)
    requires = Receipt.objects.filter(query).order_by('-appDate')  # @UndefinedVariable
    dealline = None
    dealline0 = None

    temp = []
    for r in requires:
        if str(r.student.id) == '5aa7882b97a75d6a73675866':
            print r.student.id
        if r.student:
            query = Q(student_oid=str(r.student.id))&Q(status__ne=constant.ContractStatus.delete)
            contracts = Contract.objects.filter(query)  # @UndefinedVariable
            if str(r.student.id) == '5aa7882b97a75d6a73675866':
                print contracts._query
            sum = 0
            sumAvail = 0
            printed2 = 0 #失效已报销
            printed1 = 0 #有效已报销
            

            sum2 = 0
            sumAvail2 = 0
            sumPrinted2 = 0
            
            
            hasDeadline0 = False
            hasDeadline = False
            deadline = r.appDate + datetime.timedelta(days=-constant.RECEIPT_DEADLINE_NEW)
            deadline0 = r.appDate + datetime.timedelta(days=-constant.RECEIPT_DEADLINE_REDEAL)
            if True:
                print deadline
                print deadline0
            for c in contracts:
                if not c.beginDate:
                    c.beginDate = c.singDate
                
                try:
                        if c.paid and c.paid > 0:
                    
                            if c.contractType.type == constant.ContractType.memberFee and c.multi != constant.MultiContract.memberLesson:
                                sum2 = sum2 + c.paid
                            else:
                                sum = sum + c.paid
                    
                    
                    
                         #学费
                        if c.multi == constant.MultiContract.newDeal and (c.contractType.type != constant.ContractType.memberFee or c.multi == constant.MultiContract.memberLesson) and c.beginDate >= deadline0 and c.paid and c.paid > 0:
                            sumAvail = sumAvail + c.paid
                            hasDeadline0 = True
                        elif c.multi != constant.MultiContract.newDeal and (c.contractType.type != constant.ContractType.memberFee or c.multi == constant.MultiContract.memberLesson) and c.singDate >= deadline and c.paid and c.paid > 0:
                            sumAvail = sumAvail + c.paid
                            hasDeadline = True
                        #会员费
                        if c.contractType.type == constant.ContractType.memberFee and c.multi != constant.MultiContract.memberLesson and c.singDate >= deadline0 and c.paid and c.paid > 0 and c.multi == constant.MultiContract.newDeal:
                            sumAvail2 = sumAvail2 + c.paid
                        elif c.contractType.type == constant.ContractType.memberFee and c.multi != constant.MultiContract.memberLesson and c.singDate >= deadline and c.paid and c.paid > 0 and c.multi != constant.MultiContract.newDeal:
                            sumAvail2 = sumAvail2 + c.paid                      
                        
                    
                        #=======================================================
                        # if c.multi == constant.MultiContract.newDeal and c.beginDate >= deadline0 and c.paid and c.paid > 0 and c.contractType.type != constant.ContractType.memberFee :
                        #     sumAvail = sumAvail + c.paid
                        #     hasDeadline0 = True
                        # elif c.multi != constant.MultiContract.newDeal and c.contractType.type != constant.ContractType.memberFee and c.singDate >= deadline and c.paid and c.paid > 0:
                        #     sumAvail = sumAvail + c.paid
                        #     hasDeadline = True
                        #=======================================================
                        
                        
                        #=======================================================
                        # if c.contractType.type == constant.ContractType.memberFee and c.singDate >= deadline0 and c.paid and c.paid > 0 and c.multi == constant.MultiContract.newDeal:
                        #     sumAvail2 = sumAvail2 + c.paid
                        # elif c.contractType.type == constant.ContractType.memberFee and c.singDate >= deadline and c.paid and c.paid > 0 and c.multi != constant.MultiContract.newDeal:
                        #     sumAvail2 = sumAvail2 + c.paid
                        #=======================================================
                        
                except:
                    hasDeadline = False
                
                
                
                
                
                
            query = Q(student=r.student.id)&Q(status=1)
            receipts = Receipt.objects.filter(query)  # @UndefinedVariable
            
            sumPrinted = 0
            printedMember1 = 0 #有效已报销-会员费
            
            for receipt in receipts:
                if receipt.sum > 0:                 
                 
                    if receipt.isMemberFee:
                            sumPrinted2 = sumPrinted2 + receipt.sum
                    else:
                            sumPrinted = sumPrinted + receipt.sum
                   
                    
                    
                    #===========================================================
                    # if receipt.printDate >= deadline0 and hasDeadline0:
                    #         if receipt.isMemberFee:
                    #             printedMember1 = printedMember1 + receipt.sum
                    #         else:
                    #             printed1 = printed1 + receipt.sum
                    # elif receipt.printDate >= deadline and hasDeadline:
                    #         if receipt.isMemberFee:
                    #             printedMember1 = printedMember1 + receipt.sum
                    #         else:
                    #             printed1 = printed1 + receipt.sum
                    # else:
                    #     if receipt.isMemberFee:
                    #         printed2 = printed2 + receipt.sum
                    #===========================================================
            
            
                                 
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
                            
                            
             
                 

            #if r.sum <= sum - sumPrinted and r.sum <= sumAvail:
            if not r.isMemberFee:
                r.available = sumAvail - printed1
                r.printed = sumPrinted
            
            else:
                #r.available = sumAvail2 - printed2
                r.available = sumAvail2 - printedMember1 
                r.printed = sumPrinted2
 
            
            
            
            temp.append(r)
    dateNow = utils.getDateNow()
    dateNowStr = dateNow.strftime("%Y-%m-%d")
    return render(request, 'receiptRequire.html', {"login_teacher":login_teacher,"dateNowStr":dateNowStr,
                                                  "requires":temp,"sum":len(temp)})

def receipts(request):
    login_teacher = checkCookie(request)
    if not (login_teacher):
        return HttpResponseRedirect('/login')
    if login_teacher.id != login_teacher.cityRT:
        return HttpResponseRedirect('/login')
    query = Q(financialReceipt=login_teacher.id)
    cities = City.objects.filter(query)  # @UndefinedVariable
    i = 0
    for city in cities:
        if i == 0:
            query = Q(city=city.id)
        else:
            query = query|Q(city=city.id)
        i = i + 1
    
    query = Q(status=1)|Q(status=-1)
    
    beginDateStr = request.GET.get("beginDate")
    endDateStr = request.GET.get("endDate")

    beginDate = None
    endDate = None

    dateQuery = None
    try:
        beginDate = datetime.datetime.strptime(beginDateStr,'%Y-%m-%d')
        endDate = datetime.datetime.strptime(endDateStr,'%Y-%m-%d')+datetime.timedelta(days=1)
    except:
        beginDate = None
    try:
        endDate = datetime.datetime.strptime(endDateStr,'%Y-%m-%d')+datetime.timedelta(days=1)
    except:
        endDate = None
    if not beginDate:
        beginDate = utils.getDateNow()+datetime.timedelta(days=-90)
        beginDateStr = (beginDate).strftime("%Y-%m-%d")
    if not endDate:
        endDate = utils.getDateNow()
        endDateStr = endDate.strftime("%Y-%m-%d")
        endDate = endDate+datetime.timedelta(days=1)
    dateQuery = Q(printDate__gte=beginDate)&Q(printDate__lt=endDate)
    query = query&dateQuery
    requires = Receipt.objects.filter(query).order_by('-printDate')  # @UndefinedVariable
    print requires._query
    temp = []
    for r in requires:
        try:
            s = Student.objects.get(id=r.student.id)  # @UndefinedVariable
        except:
            r.student = None
        temp.append(r)
    requires = temp
    
    return render(request, 'receipts.html', {"login_teacher":login_teacher,
                                                  "requires":requires,"sum":len(requires),
                                                  "beginDate":beginDateStr,"endDate":endDateStr
                                                  })


def api_refund(request):
    reload(sys)
    sys.setdefaultencoding('utf8')  # @UndefinedVariable
    login_teacher = checkCookie(request)
    if not (login_teacher):
        return HttpResponseRedirect('/login')
    mess = None
    oid = request.POST.get("contract_oid")
    status = request.POST.get("status")
    refund = request.POST.get("refund")
    refundMemo = request.POST.get("refundMemo")
    
    refundDateStr = request.POST.get("refundDate")
    refundApproveStr = request.POST.get("refundApprove")
    refundApprove = None
    if refundApproveStr:
        refundApprove = int(refundApproveStr)
    refundDate = None
    try:
        refundDate = datetime.datetime.strptime(refundDateStr,"%Y-%m-%d")
    except:
        refundDate =None
    
    res = ''
    openId = ''
    try:
        
        
        s = int(status)
        if s == 0:
            refundDate = None
        contract = Contract.objects.get(id=oid)  # @UndefinedVariable
        r = contract.refund
        if r > 0:
            contract.refund = r
        else:
            contract.refund = contract.paid
        if refundMemo:
            contract.refundMemo = refundMemo
        else:
            contract.refundMemo = None
        contract.status = s
        
        if refundDate:
            contract.endDate = refundDate
        elif refundApprove > 0:
            contract.refundApprove = refundApprove
        contract.save()
        student = Student.objects.get(id=contract.student_oid)  # @UndefinedVariable

        name = '学生-'
        if student.name:
            name = name + student.name
        if student.name2:
            name = name + '(' + student.name2 + ')'
        res = {"error": 0}

        if status == '0':

            mess = name + u'-退费申请被驳回,理由:' + refundMemo

            query = Q(contractId=oid)&Q(fileType=constant.FileType.refundApp)
            try:

                files = StudentFile.objects.filter(query)  # @UndefinedVariable
                if files and len(files)>0:
                    for file in files:
                        filepath = BASE_DIR+USER_IMAGE_DIR+file.filepath+file.filename
                        #print filepath
                        file.delete()
                        os.remove(filepath)
                

            except Exception,e:
                print e
                err = 1
        elif s == -1 and contract.refundApprove == 1:
            #退费已批准，进入出纳操作退费流程
            try:
                
                branchN = contract.branch.city.cityName + '-' + contract.branch.branchName
                
                toTeacher = Teacher.objects.get(id=contract.branch.city.financialRefund)  # @UndefinedVariable
                
                #===============================================================
                # query = Q(city=constant.BEIJING)&Q(type=1)
                # branch = Branch.objects.filter(query)[0]  # @UndefinedVariable
                # query = Q(branch=branch.id)&Q(role=constant.Role.financial)
                # toTeacher = Teacher.objects.filter(query)  # @UndefinedVariable
                #===============================================================
                if toTeacher and toTeacher.openId:
                    openId = toTeacher.openId
                    #print openId
                    res = {"error": 0,"openId":openId,"branch":branchN}
            except Exception,e:
                print e
        elif s == 2:
            
            mess = name + u'-退费完成-退款：' + str(contract.refund)
            
            query = Q(student_oid=student.id)&Q(status=constant.ContractStatus.sign)
            validContracts = Contract.objects.filter(query)  # @UndefinedVariable
            if validContracts and len(validContracts) > 0:
                donothing = 1
            else:
                student.status = constant.StudentStatus.refund
                student.save()
                
        if mess:
            
            query = Q(branch=contract.branch)&Q(status__ne=-1)&(Q(role=constant.Role.master)|Q(role=constant.Role.operator))
            toTeachers = Teacher.objects.filter(query)  # @UndefinedVariable
            url = '/go2/contract/studentContracts?student_oid='+contract.student_oid
            for t in toTeachers:
                utils.sendMessage(login_teacher.branchName,login_teacher.id, login_teacher.teacherName, str(t.id), mess, None, url)
    except Exception,e:
        print e
        res = {"error": 1, "msg": str(e)}
    
    return http.JSONResponse(json.dumps(res, ensure_ascii=False))  

#申请开发票api
def receiptApp_api(request): 
    login_teacher = checkCookie(request)
    if not (login_teacher):
        return HttpResponseRedirect('/login')
    student_oid = request.POST.get("student_oid")
    sumStr = request.POST.get("sum")
    title = request.POST.get("title")
    rTypeStr = request.POST.get("rType")
    taxNo = request.POST.get("taxNo")
    address = request.POST.get("address")
    bank = request.POST.get("bank")
    appDateStr = request.POST.get("appDate")
    isMemberFeeStr = request.POST.get("isMemberFee")
    isMemberFee = False
    if isMemberFeeStr == '1':
        isMemberFee = True
    sum = 0.0
    rType = 1
    student = None
    appDate = None
    
    try:
        sum = float(sumStr)
    except:
        res = {"error": 1, "msg": u'开票金额不正确'}
        return http.JSONResponse(json.dumps(res, ensure_ascii=False))

    try:
        rType = int(rTypeStr)
    except:
        rType = 1

    try:
        student = Student.objects.get(id=student_oid)  # @UndefinedVariable
    except:
        res = {"error": 1, "msg": u'学生未找到'}
        return http.JSONResponse(json.dumps(res, ensure_ascii=False))
    try:
        appDate = datetime.datetime.strptime(appDateStr,"%Y-%m-%d")
    except:
        appDate = utils.getDateNow()
    
    query = Q(student_oid=str(student.id))&Q(status__ne=constant.ContractStatus.delete)&Q(paid__gt=0)
    cs = Contract.objects.filter(query)  # @UndefinedVariable
    contractSum = 0
    for c in cs:
        contractSum = contractSum + c.paid
    
    receipt = Receipt(student=student.id)
    receipt.sum = sum
    receipt.title = title
    receipt.rType = rType
    receipt.taxNo = taxNo
    receipt.address = address
    receipt.bank = bank
    receipt.status = 0
    receipt.appDate = appDate
    receipt.contractSum = contractSum
    receipt.isMemberFee = isMemberFee
    receipt.save()
    openId = None
    try:
        city = City.objects.get(id=login_teacher.cityId)  # @UndefinedVariable
        if city and city.financialReceipt:
            fr = Teacher.objects.get(id=city.financialReceipt)  # @UndefinedVariable
            openId = fr.openId 
    except:
        openId = None
    
    res = {"error": 0, "openId": openId}
    return http.JSONResponse(json.dumps(res, ensure_ascii=False))

def receiptDeal_api(request): 
    login_teacher = checkCookie(request)
    if not (login_teacher):
        return HttpResponseRedirect('/login')
    id = request.POST.get("id")
    statusStr = request.POST.get("status")
    printDateStr = request.POST.get('printDate')
    memo = request.POST.get("memo")
    printDate = None
    receipt = None
    status = None
    try:
        receipt = Receipt.objects.get(id=id)  # @UndefinedVariable
    except:
        res = {"error": 1, "msg": u'receipt application not found'}
        return http.JSONResponse(json.dumps(res, ensure_ascii=False))
    try:
        printDate = datetime.datetime.strptime(printDateStr,"%Y-%m-%d")
    except:
        printDate = utils.getDateNow()
    try:
        status = int(statusStr)
    except:
        res = {"error": 1, "msg": u'status not found'}
        return http.JSONResponse(json.dumps(res, ensure_ascii=False))
    
    receipt.status = status
    if status == 1:
        receipt.printDate = printDate
    if memo:
        receipt.memo = memo
    receipt.save()
    try:
      mess = u'学生'+receipt.student.name
      if status == 1:
        mess = mess + u'发票已开'
      elif status == -1:
        mess = mess + u'开票申请被驳回：'
        if receipt.memo:
            mess = mess + receipt.memo
      query = Q(branch=receipt.student.branch.id)&Q(status__ne=-1)&(Q(role=constant.Role.master)|Q(role=constant.Role.operator))
      toTeachers = Teacher.objects.filter(query)  # @UndefinedVariable
      url = '/go2/contract/studentContracts?student_oid='+str(receipt.student.id)
      for t in toTeachers:
        utils.sendMessage(login_teacher.branchName,login_teacher.id, login_teacher.teacherName, str(t.id), mess, None, url)
    except Exception,e:
        print e
    res = {"error": 0, "openId": ''}
    return http.JSONResponse(json.dumps(res, ensure_ascii=False))

#待审批报销
def reimburseApps(request):
    login_teacher = checkCookie(request)
    if not (login_teacher):
        return HttpResponseRedirect('/login')
    if login_teacher.id != login_teacher.cityRB and login_teacher.id != login_teacher.cityRB2:
        return HttpResponseRedirect('/login')
    query = Q(financialReimburse=login_teacher.id)
    cities = City.objects.filter(query)  # @UndefinedVariable
    query = None
    
    
        
    i = 0
    for city in cities:
        if i == 0:
            query = Q(city=city.id)
        else:
            query = query|Q(city=city.id)
        i = i + 1
    branches = Branch.objects.filter(query)  # @UndefinedVariable
    query = None
    i = 0
    
    searchBranchStr = request.GET.get("searchBranch")
    searchBranch = None
    
    try:
        searchBranch = Branch.objects.get(id=searchBranchStr)  # @UndefinedVariable

    except:
        searchBranch = None
    if searchBranch:
        query = Q(branch=searchBranch.id)
    else:
        for b in branches:
            if i == 0:
                query = Q(branch=b.id)
            else:
                query = query|Q(branch=b.id)
            i = i + 1
    query = Q(status=constant.ReimburseStatus.waiting)&(query)

    #是否有发票
    hasReceipt = request.GET.get('hasReceipt')
    if hasReceipt == '1':
        query = query&Q(hasReceipt=True)
    else:
        query = query&Q(hasReceipt=False)
    if not hasReceipt:
        hasReceipt = '0'
    mainurl = '/go2/workflow/reimburseApps?hasReceipt='+hasReceipt
    
    if searchBranch:
        mainurl = mainurl + '&searchBranch='+str(searchBranch.id)
    
    
    reimburses = Reimburse.objects.filter(query).order_by('-appDate')  # @UndefinedVariable
    temp = []
    for r in reimburses:
        r.appmemo = ''
        query = Q(rid=str(r.id))
        ris = ReimburseItem.objects.filter(query)  # @UndefinedVariable
        #print ris._query
        if ris and len(ris) > 0:
            #print 'has'
            r.appmemo = ris[0].typeName+'-'+ris[0].itemName+'('+str(len(ris))+')'
            temp.append(r)
    reimburses = temp
    
    dateNow = utils.getDateNow(8)
    response = render(request, 'reimburseApps.html', {"login_teacher":login_teacher,"branches":branches,
                                                  "hasReceipt":hasReceipt,"searchBranch":searchBranchStr,
                                                  "dateNow":dateNow,
                                             "reimburses": reimburses}) 
    response.set_cookie("reimurl",mainurl)

    return response
#获取报销申请数量，用于badge显示
def reimburseApps_api(request):
    login_teacher = checkCookie(request)
    if not (login_teacher):
        return HttpResponseRedirect('/login')
    if login_teacher.id != login_teacher.cityRB and login_teacher.id != login_teacher.cityRB2:
        return HttpResponseRedirect('/login')
    query = Q(financialReimburse=login_teacher.id)
    cities = City.objects.filter(query)  # @UndefinedVariable
    query = None
    
    i = 0
    for city in cities:
        if i == 0:
            query = Q(city=city.id)
        else:
            query = query|Q(city=city.id)
        i = i + 1
    branches = Branch.objects.filter(query)  # @UndefinedVariable
    query = None
    i = 0
    for b in branches:
        if i == 0:
            query = Q(branch=b.id)
        else:
            query = query|Q(branch=b.id)
        i = i + 1
    query = Q(status=constant.ReimburseStatus.waiting)&(query)
    
    #是否有发票
    hasReceipt = request.POST.get('hasReceipt')
    
    if hasReceipt == '1':
        query = query&Q(hasReceipt=True)
    else:
        query = query&Q(hasReceipt=False)
    
    reimburses = Reimburse.objects.filter(query).order_by('-appDate')  # @UndefinedVariable
    res = {"error": 0, "num": 0}
    if reimburses and len(reimburses) > 0:
        
        res = {"error": 0, "num": len(reimburses)}

    return http.JSONResponse(json.dumps(res, ensure_ascii=False))


#财务批量处理报销
def reimburseDealAll_api(request): 
    #print 'on'
    login_teacher = checkCookie(request)
    if not (login_teacher):
        return HttpResponseRedirect('/login')
    if login_teacher.id != login_teacher.cityRB2 and login_teacher.id != login_teacher.cityRB:
        return HttpResponseRedirect('/login')
    ids = request.POST.get("ids")
    #print ids
    paidDateStr = request.POST.get('paidDate')
    finmemo = request.POST.get("finmemo")
    paidDate = None
    reimburse = None

    idArray = ids.split(',')
    
    for id in idArray:
      #print id    
      try:
        reimburse = Reimburse.objects.get(id=id)  # @UndefinedVariable
      except Exception,e:
        print e
        res = {"error": 1, "msg": u'reimburse not found'}
        return http.JSONResponse(json.dumps(res, ensure_ascii=False))
      try:
        paidDate = datetime.datetime.strptime(paidDateStr,"%Y-%m-%d")
      except:
        paidDate = utils.getDateNow()

      reimburse.status = 2
    #if status == constant.ReimburseStatus.approved:
      reimburse.paidDate = paidDate
      reimburse.save()
    
    res = {"error": 0, "openId": ''}
    return http.JSONResponse(json.dumps(res, ensure_ascii=False))

#财务处理报销
def reimburseDeal_api(request): 
    login_teacher = checkCookie(request)
    if not (login_teacher):
        return HttpResponseRedirect('/login')
    if login_teacher.id != login_teacher.cityRB2 and login_teacher.id != login_teacher.cityRB:
        return HttpResponseRedirect('/login')
    id = request.POST.get("id")
    statusStr = request.POST.get("status")
    paidDateStr = request.POST.get('paidDate')
    finmemo = request.POST.get("finmemo")
    paidDate = None
    reimburse = None
    status = None

    try:
        reimburse = Reimburse.objects.get(id=id)  # @UndefinedVariable
    except Exception,e:
        print e
        res = {"error": 1, "msg": u'reimburse not found'}
        return http.JSONResponse(json.dumps(res, ensure_ascii=False))
    try:
        paidDate = datetime.datetime.strptime(paidDateStr,"%Y-%m-%d")
    except:
        paidDate = utils.getDateNow()
    try:
        status = int(statusStr)
    except Exception,e:
        print e
        res = {"error": 1, "msg": u'status not found'}
        return http.JSONResponse(json.dumps(res, ensure_ascii=False))
    
    reimburse.status = status
    #if status == constant.ReimburseStatus.approved:
    reimburse.paidDate = paidDate
    
    if finmemo:
        reimburse.finmemo = finmemo
    reimburse.save()
    try:
        mess = ''
        if status == -1: #驳回发送消息给运营
            mess = mess + u'报销申请被驳回：'
            if reimburse.finmemo:
                mess = mess + reimburse.finmemo
            query = Q(branch=reimburse.branch.id)&Q(status__ne=-1)&Q(role=constant.Role.operator)
            toTeachers = Teacher.objects.filter(query)  # @UndefinedVariable
            url = '/go2/branch/reimburses'
            for t in toTeachers:
                utils.sendMessage(login_teacher.branchName,login_teacher.id, login_teacher.teacherName, str(t.id), mess, None, url)
    except Exception,e:
        print e
    res = {"error": 0, "openId": ''}
    return http.JSONResponse(json.dumps(res, ensure_ascii=False))

def reimburseDeals(request):
    login_teacher = checkCookie(request)
    if not (login_teacher):
        return HttpResponseRedirect('/login')
    if login_teacher.id != login_teacher.cityRB and login_teacher.id != login_teacher.cityRB2:
        return HttpResponseRedirect('/login')
    query = None
    queryBranch = None
    queryCity = None
    if login_teacher.id == login_teacher.cityRB:
        queryCity = Q(financialReimburse=login_teacher.id)
    if login_teacher.id == login_teacher.cityRB2:
        queryCity = Q(financialReimburse2=login_teacher.id)
    cities = City.objects.filter(queryCity)  # @UndefinedVariable
    queryCity = None
    i = 0
    for city in cities:
        if i == 0:
                queryCity = Q(city=city.id)
        else:
                queryCity = queryCity|Q(city=city.id)
        i = i + 1
    branches = Branch.objects.filter(queryCity).order_by('sn')  # @UndefinedVariable
    
    
    query = Q(status=constant.ReimburseStatus.approved)|Q(status=constant.ReimburseStatus.reject)
    #是否有发票
    hasReceipt = request.GET.get('hasReceipt')
    if hasReceipt == '1':
        query = query&Q(hasReceipt=True)
    else:
        query = query#&Q(hasReceipt=False)
        
    searchStatusStr = request.GET.get("searchStatus")
    searchBranchStr = request.GET.get("searchBranch")
    searchType = request.GET.get("searchType")
    beginDateStr = request.GET.get("beginDate")
    endDateStr = request.GET.get("endDate")
    
    beginDate = None
    endDate = None
    searchStatus = None
    searchBranch = None
    try:
        searchBranch = Branch.objects.get(id=searchBranchStr)  # @UndefinedVariable
    except:
        searchBranch = None
    try:
        searchStatus = int(searchStatusStr)
    except:
        searchStatus = None
    try:
        beginDate = datetime.datetime.strptime(beginDateStr,'%Y-%m-%d')
        endDate = datetime.datetime.strptime(endDateStr,'%Y-%m-%d')+datetime.timedelta(days=1)

    except:
        beginDate = None
    try:
        endDate = datetime.datetime.strptime(endDateStr,'%Y-%m-%d')+datetime.timedelta(days=1)
    except:
        endDate = None
    if beginDate:
        query = query&Q(appDate__gte=beginDate)
    else:
        beginDate = utils.getDateNow()+datetime.timedelta(days=-7)
        beginDateStr = (beginDate).strftime("%Y-%m-%d")
        query = query&Q(appDate__gte=beginDate)
    if endDate:
        query = query&Q(appDate__lt=endDate)
    else:
        endDate = utils.getDateNow()
        endDateStr = endDate.strftime("%Y-%m-%d")
        endDate = endDate+datetime.timedelta(days=1)
        query = query&Q(appDate__lt=endDate)
    if searchType and len(searchType) == 0:
        searchType = None
    if searchStatus is not None:
        query = query&Q(status=searchStatus)    
    if searchType:
        query = query&Q(type=searchType)
    
    if searchBranch:
        query = query&Q(branch=searchBranch.id)
    else: #没有指明校区，则查询所有管辖校区
        
        i = 0
        for b in branches:
            if i == 0:
                queryBranch = Q(branch=b.id)
            else:
                queryBranch = queryBranch|Q(branch=b.id)
            i = i + 1
        query = (query)&(queryBranch)
    
    reimburses = Reimburse.objects.filter(query).order_by('-appDate')  # @UndefinedVariable
    
    temp = []
    for r in reimburses:
        r.appmemo = ''
        query = Q(rid=str(r.id))
        ris = ReimburseItem.objects.filter(query)  # @UndefinedVariable
        #print ris._query
        if ris and len(ris) > 0:
            #print 'has'
            r.appmemo = ris[0].typeName+'-'+ris[0].itemName+'('+str(len(ris))+')'
            temp.append(r)
    reimburses = temp
    
    
    return render(request, 'reimburseDeals.html', {"login_teacher":login_teacher,
                                                   "hasReceipt":hasReceipt,
                                                   "branches":branches,
                                                   "types":constant.REIMBURSE_TYPE,
                                                   "searchStatus":searchStatus,
                                               "searchBranch":searchBranchStr,
                                               "searchType":searchType,
                                               "beginDate":beginDateStr,"endDate":endDateStr,
                                             "reimburses": reimburses}) 
    
def todayContact(request):
    login_teacher = checkCookie(request)
    if not (login_teacher):
        return HttpResponseRedirect('/login')
    query = Q(branch=login_teacher.branch)
    tq = None
    teachers = Teacher.objects.filter(query)  # @UndefinedVariable
    i = 0
    for t in teachers:
        if i == 0:
            tq = Q(teacher=t.id)
        else:
            tq = tq|Q(teacher=t.id)
        i = i + 1
        
    contacts = None
    
    today = utils.getDateNow(8)
    sdate = request.GET.get('sdate')
    
    try:
        sd = datetime.datetime.strptime(sdate,'%Y-%m-%d')
    except:
        sd = today 
    begin = utils.getDayBegin(sd)
    end = begin + datetime.timedelta(days=1)
    
    query = Q(trackTime__gte=begin)&Q(trackTime__lt=end)&tq&Q(deleted__ne=1)
    contacts = StudentTrack.objects.filter(query)  # @UndefinedVariable
    if sd:
        sdate = sd.strftime("%Y-%m-%d")
        
    return render(request, 'todayContact.html', {"login_teacher":login_teacher,
                                             "contacts": contacts,"sdate":sdate})
