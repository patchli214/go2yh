#!/usr/bin/env python
# -*- coding:utf-8 -*-
__author__ = 'patch'
from django.conf.urls import include, url
from webpage.views import *

urlpatterns = [
    url(r'^pages$', pages, name='pages'),
    url(r'^removePage$', removePage, name='removePage'),
    url(r'^savePage$', savePage,name='savePage'),
    url(r'^uploadPic$', uploadPic,name='uploadPic'),
    url(r'^removePic$', removePic,name='removePic'),
    url(r'^cmb2017$', cmb2017,name='cmb2017'),
    url(r'^cmb2017res$', cmb2017res,name='cmb2017res'),
    url(r'^netReg$', netReg,name='netReg'),
    url(r'^regList$', regList,name='regList'),
    url(r'^regList2$', regList2,name='regList2'),
    url(r'^api_done$', api_done,name='api_done'),
    url(r'^rotatePic$', rotatePic,name='rotatePic'),
    url(r'^sendWX$', send_template_message,name='send_template_message'),
    url(r'^luckyDraw2018a$', luckyDraw2018a,name='luckyDraw2018a'),
    url(r'^luckyDraw2018b$', luckyDraw2018b,name='luckyDraw2018b'),
    url(r'^useVoucher$', useVoucher,name='useVoucher'),
    url(r'^checkVoucher$', checkVoucher,name='checkVoucher'),
    url(r'^library20181215$', library20181215,name='library20181215'),
    url(r'^getJieli360WXToken$', getJieli360WXToken,name='getJieli360WXToken'),
    
    
    
    
]