#!/usr/bin/env python
# -*- coding:utf-8 -*-
__author__ = 'bee'

from django import template

from tools import constant

register = template.Library()


@register.filter
def get_gradeClass_type(gradeClass_type):
    if gradeClass_type == constant.GradeClassType.normal:
        return "课程"
    if gradeClass_type == constant.GradeClassType.demo:
        return "试听"
    if gradeClass_type == constant.GradeClassType.missClass:
        return "补课"
    if gradeClass_type == constant.GradeClassType.other:
        return "其他"
