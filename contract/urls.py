#!/usr/bin/env python
# -*- coding:utf-8 -*-
__author__ = 'patch'
from django.conf.urls import include, url
from contract.views import *

urlpatterns = [
    url(r'^contract_list$', contract_list, name='contract_list'),
    url(r'^removeContract$', removeContract, name='removeContract'),
    url(r'^studentContracts$', studentContracts,name='studentContracts'),
    url(r'^saveContract_api$', saveContract_api,name='saveContract_api'),
    url(r'^uploadFile$', uploadFile,name='uploadFile'),
    url(r'^incomes$', incomes,name='incomes'),
    url(r'^api_income$', api_income,name='api_income'),
    url(r'^income$', income,name='income'),
    url(r'^deposits$', deposits,name='deposits'),
    url(r'^Y19Incomes$', Y19Incomes,name='Y19Incomes'),
    url(r'^Y19Income1$', Y19Income1,name='Y19Income1'),
    url(r'^api_Y19Income$', api_Y19Income,name='api_Y19Income'),
    url(r'^api_Y19dayIn$', api_Y19dayIn,name='api_Y19dayIn'),
    url(r'^Y19stat$', Y19stat,name='Y19stat'),
    url(r'^Y19WeekStat$', Y19WeekStat,name='Y19WeekStat'),
    url(r'^Y19statTeacher$', Y19statTeacher,name='Y19statTeacher'),
    url(r'^duePay$',duePay,name='duePay'),
    url(r'^AllduePay$',AllduePay,name='AllduePay'),
    url(r'^api_y19fee$',api_y19fee,name='api_y19fee'),
    url(r'^netcontracts$',netcontracts,name='netcontracts'),
    url(r'^cstudents$', cstudents,name='cstudents'),
    
    url(r'^api_y19done$',api_y19done,name='api_y19done')
    
    
]
