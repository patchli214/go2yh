#!/usr/bin/env python
# -*- coding:utf-8 -*-

from django.db import models
from mongoengine import *


class Income(Document):
    cityId = StringField()
    branchId = StringField()
    payer = StringField()
    studentId = StringField() #交款学生id
    receipterId = StringField() #收款人ID
    type = StringField() #类号
    typeName = StringField()
    payDate = DateTimeField()
    paid = FloatField() 
    paymethod = StringField() #付款方式，见congstant.PAY_METHOD
    memo = StringField()
    status = IntField()#=ContractStatus
    
    refund = FloatField() #退款
    refundDate = DateTimeField()
    memo2 = StringField()#退款理由
    refundAppDate = DateTimeField()
    refundApprove = IntField() #0-未审批，1-通过，2-驳回
    refundMemo = StringField() #驳回退费理由
    
class Y19Income(Document):
    branch = StringField()
    branchName = StringField()
    regName = StringField()
    mobile = StringField()
    payDate = DateTimeField()
    
    type = StringField()
    paid = FloatField()
    source = StringField()
    sellerId = StringField()
    sellerName = StringField()
    memo = StringField()
    contractId = StringField()#对应的真朴合同ID
    
    logDate = DateTimeField()#登记入系统的时间，财务按此时间查询开通新账户
    appDone = BooleanField()#元十九开通用户app后打勾✅
    appFee = BooleanField()#元十九财务收款后打勾☑️
    
    meta = {
        'collection': 'Y19Income'
    }

class Y19data(Document):
    branch = StringField()
    branchName = StringField()
    teacher = StringField()
    teacherName = StringField()
    day = DateTimeField()
    dayIn = IntField()
    dayReg = IntField()
    dayInToday = IntField()
    dayRegToday = IntField()
    dayAdd = IntField()
    meta = {'collection':'Y19data'}


    
       