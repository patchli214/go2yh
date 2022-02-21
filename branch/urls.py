#!/usr/bin/env python
# -*- coding:utf-8 -*-
__author__ = 'bee'
from django.conf.urls import include, url
from branch.views import *
urlpatterns = [

    # reg
    url(r'^reg$', reg, name='reg'),
    url(r'^apiReg$', api_reg, name='api_reg'),
    url(r'^city$', city, name='city'),
    url(r'^apiCity$', api_city, name='api_city'),
    url(r'^branchList$', branch_list, name='branch_list'),
    url(r'^branchInfo/(?P<branch_oid>[\w]{24})/$', branch_info, name='branch_info'),
    url(r'^cityList$', city_list, name='city_list'),
    url(r'^branchPic$', branchPic,name='branchPic'),
    url(r'^statistics$', statistics,name='statistics'),
    url(r'^netUser$', netUser,name='netUser'),
    url(r'^editCategory$', editCategory,name='editCategory'),
    url(r'^editSource$', editSource,name='editSource'),
    url(r'^api_editCategory$', api_editCategory,name='api_editCategory'),
    url(r'^api_editSource$', api_editSource,name='api_editSource'),
    url(r'^sources$', sources,name='sources'),
    url(r'^reimburses$', reimburses,name='reimburses'),
    url(r'^reimburse$', reimburse,name='reimburse'),
    url(r'^reimburseShow$', reimburseShow,name='reimburseShow'),
    url(r'^reimburseErr$', reimburseErr,name='reimburseErr'),
    
    url(r'^reimburseRemove_api$', reimburseRemove_api,name='reimburseRemove_api'),
    url(r'^api_submitReimburse$', api_submitReimburse,name='api_submitReimburse'),
    url(r'^reimburseNum_api$', reimburseNum_api,name='reimburseNum_api'),
    
    url(r'^jointDate$', jointDate,name='jointDate'),
    url(r'^cityContract$', cityContract,name='cityContract'),
    url(r'^editContract$', editContract,name='editContract'),
    url(r'^api_editContract$', api_editContract,name='api_editContract'),
    url(r'^vocations$', vocations,name='vocations'),
    url(r'^api_delVocation$', api_delVocation,name='api_delVocation'),
    url(r'^api_vocation$', api_vocation,name='api_vocation'),
    url(r'^tweet2019$', tweet2019,name='tweet2019'),
    
]
