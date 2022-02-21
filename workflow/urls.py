#!/usr/bin/env python
# -*- coding:utf-8 -*-
__author__ = 'patch'
from django.conf.urls import include, url
from workflow.views import *

urlpatterns = [
    
    url(r'^refundApprovedList$', refundApprovedList, name='refundApprovedList'),
    url(r'^refundWaitingList$', refundWaitingList, name='refundWaitingList'),
    url(r'^api_refund$', api_refund, name='api_refund'),
    url(r'^receiptRequire$', receiptRequire, name='receiptRequire'),
    url(r'^receipts$', receipts, name='receipts'),
    url(r'^receiptApp_api$', receiptApp_api, name='receiptApp_api'),
    url(r'^receiptDeal_api$', receiptDeal_api, name='receiptDeal_api'),
    url(r'^reimburseApps$', reimburseApps, name='reimburseApps'),
    url(r'^reimburseDeal_api$', reimburseDeal_api, name='reimburseDeal_api'),
    url(r'^reimburseDeals$', reimburseDeals, name='reimburseDeals'),
    url(r'^reimburseApps_api$', reimburseApps_api, name='reimburseApps_api'),
    url(r'^reimburseDealAll_api$', reimburseDealAll_api, name='reimburseDealAll_api'),
    url(r'^todayContact$', todayContact, name='todayContact'),
    
]