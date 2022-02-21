#!/usr/bin/env python
# -*- coding:utf-8 -*-
__author__ = 'bee'

from django import template

register = template.Library()

@register.filter
def week_name(value):
    week = ["", "一", "二", "三", "四", "五", "六", "日"]
    if value:
        day = int(value)
        if day >= 1 and day <= 7:
            return week[day]
        else:
            return ""

    else:
        return ""



