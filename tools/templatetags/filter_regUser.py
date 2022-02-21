#!/usr/bin/env python
# -*- coding:utf-8 -*-
__author__ = 'bee'

from django import template

from regUser.models import Student

register = template.Library()


@register.filter
def get_student_name(student_oid):
    try:
        student = Student.objects.get(id=student_oid)
        return student.name
    except:
        return ""
