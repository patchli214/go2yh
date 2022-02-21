#!/usr/bin/env python
# -*- coding:utf-8 -*-
import sys,hashlib, os, time, datetime
import xlrd,re,xlwt
from mongoengine.queryset.visitor import Q
from regUser.models import *
from teacher.models import Teacher,Login_teacher
from branch.models import Branch
from go2.settings import BASE_DIR,USER_IMAGE_DIR,ALLOWED_HOSTS
import logging
from datetime import timedelta
from tools.utils import getDateNow
from tools import constant,utils, http, util2
from tools.constant import GradeClassType
from gradeClass.models import Lesson
import json
import gradeClass
from __builtin__ import True
from operator import attrgetter
LOG_FILE = '/data/go2/log/excel.log'
def getNetUser(filepath,branch_oid,notAdd=None,changeBranch=None):
  print '[GET NET USERS]'  
  index = 0
  regBranch = Branch.objects.get(branchName=u'网络部')  # @UndefinedVariable
  branch = Branch.objects.get(id=branch_oid)  # @UndefinedVariable
  sources = Source.objects.filter(branch=regBranch.id)
  sourceCategories = SourceCategory.objects.filter(branch=regBranch.id)
  regTeachers = Teacher.objects.filter(branch=regBranch.id)  # @UndefinedVariable

  code_col = 2
  prt1_col = 4
  name_col = 5
  gender_col = 6
  birthday_col= 7
  mobile_col = 8
  wantClass_col = 10
  demoTime_col = 13
  isDemo_col = 14
  demoTeacher_col = 15
  contractTime_col =16
  contractFee_col = 17
  memo_col = 18
  alldup = []
  excel = xlrd.open_workbook(BASE_DIR+USER_IMAGE_DIR+filepath)
  tables = excel.sheets()
  for table in tables:  
    probability = "A"
    contractStatus = None
    if u'丢失' in table.name :
        probability = 'C'
    elif u'退费' in table.name :
        contractStatus = 2
    elif u'成交' in table.name :
        contractStatus = 0
    nrows = table.nrows #行数
    ncols = table.ncols #列数
    #nrows = 10000
    
    dup = 0
    sheetIndex = 0
    nullIndex = 0

    for i in range(0,nrows):
        try:
            row = table.row_values(i)
        except:
            nullIndex = nullIndex + 1
            continue
        
        if row[code_col] == u"编号":
            continue
        if row[code_col] == '':
            nullIndex = nullIndex + 1
            
        student = Student()
        
        mstr = ''

        #mobile
        try:
            mstr = str(row[mobile_col])
        except:
            mstr = row[mobile_col].encode("utf8")
        if type(row[mobile_col]) is float:  
            mstr = repr(row[mobile_col]).split(".")[0]
        if not mstr or len(mstr)<8:
            continue
        student.prt1mobile = mstr
        student.branch = branch
        student.branchName = branch.branchName
        student.regBranch = regBranch
        student.regBranchName = u'网络部'
        
        mstr = row[code_col]
        if type(row[code_col]) is float:
            mstr = repr(row[code_col]).split(".")[0]
        student.code = mstr
        
        regYear = 0
        if len(mstr)>=10:
            rt = mstr[2:10]
            try:
                student.regTime = datetime.datetime.strptime(rt,"%Y%m%d")
            except Exception,e:
                a = 1
            regYear = 0
            if student.regTime:
                regYear = student.regTime.year
        #source,sourceCategory,regTeacher
            mstr = mstr[0:2]
            
            for s in sources:
                if s.sourceCode == mstr:
                    student.source = s
                    for t in regTeachers:
                        if t.name == s.contact:
                            student.regTeacher = t
                            student.regTeacherName = t.name
                            
                    for sc in sourceCategories:
                        if s.categoryCode == sc.categoryCode:
                            student.sourceCategory = sc
                            break
                    break

        #sourceType,name,part,gender,wangClass,memo
        student.sourceType = "A"
    
                
                
        isDemo = 0
        if row[isDemo_col] == u'是':
                isDemo = 1
        demo = GradeClass()
        if isDemo == 1:
                try:
                    demoTeacherName = row[demoTeacher_col].encode("utf8")
                except:
                    demoTeacherName = None
                demoTeacher = None
                teachers = Teacher.objects.filter(branch=branch_oid).filter(name=demoTeacherName)  # @UndefinedVariable
                if teachers and len(teachers)>0:
                    demoTeacher = teachers[0]
                    demo.teacher = demoTeacher
                mstr = row[demoTime_col]
                if type(mstr) is float:
                    mstr = str(mstr).split(".")[0]
                    if mstr and len(mstr)>=4:
                        mstr = mstr[0:4]
                else:
                    mstr = row[demoTime_col].encode("utf8")
                    mstr = mstr[0:4]
                try:
                    demo.start_date = datetime.datetime.strptime(str(regYear)+mstr,"%Y%m%d")
                    if demo.start_date < student.regTime:
                        demo.start_date = demo.start_date + timedelta(days=365)
                except Exception,e:
                    demo.start_date = None

                demo.demoIsFinish = 1
                
                student.isDemo = 1
                student.demo = []
                student.demo.append(str(demo.id))

        try:
                mstr = str(row[contractTime_col])
        except:
                mstr = row[contractTime_col].encode("utf8")
        contractTime = None
        contract = Contract()
        if contractStatus == 0 or contractStatus == 2:
                hasContract = 1
        if type(row[contractTime_col]) is float:  
                mstr = repr(row[contractTime_col]).split(".")[0]
        if mstr and len(mstr)>=8:
                hasContract = 1
                mstr = mstr[0:8]
                try:
                    contractTime = datetime.datetime.strptime(mstr,"%Y%m%d")
                    contract.singDate = contractTime
                except:
                    a = 1
        
                try:
                    mstr = str(row[contractFee_col])
                except:
                    mstr = row[contractFee_col].encode("utf8")
                
                if type(row[contractFee_col]) is float:
                    try:
                        mstr = repr(row[contractFee_col]).split(".")[0]
                        contract.paid = int(mstr)
                    except:
                        a = 1
                    
                    if contractStatus == 2:
                        student.status = 2
                        
                    else:
                        student.status = 1
                    contract.status = contractStatus
    
        student.prt1 = row[prt1_col]
        try:
            student.memo = row[memo_col]
            if type(row[memo_col]) is float:
                student.memo = repr(row[memo_col]).split(".")[0]
        except:
            print 'err momo'

        try:
            student.wantClass = row[wantClass_col]
            gend = row[gender_col]
            if isinstance(gend,str):
                student.gender = gend 
            
            
        except:
            error = 1
        
        #birthday
        try:
            age_str = str(row[birthday_col])
        except:
            age_str = row[birthday_col].encode("utf-8")
        #try:
        if True:
            ageYear = 0
            ageMonth = 0
            if type(age_str) is float:
                mstrs = str(age_str).split(".")
                mstr = mstrs[0]
                ageYear = int(mstr)
                if len(mstrs)>1:
                    mstr = mstrs[1]
                    ageMonth = int(mstr)
            else:
                nums = map(int, re.findall(r'\d+', age_str))
                if nums and len(nums)>0:
                    if nums[0] > 1 and nums[0] < 15:
                        ageYear = nums[0]
                    if len(nums)>1 and nums[1] < 12 and nums[1] > -1:
                        ageMonth = nums[1]
                                    
            if ageYear<1 or ageYear>20:
                ageYear = 0
            if ageMonth > 11 or ageMonth < 0:
                ageMonth = 0

            if ageYear > 0:
                days = ageYear*365+ageMonth*30
                now = getDateNow()
                birthday = now - timedelta(days=days)
                student.birthday = birthday
    
    
    
    
    
    
    
    
    
        
        #dup check
        dup = 0
        students = []
        students = Student.objects.filter(prt1mobile=student.prt1mobile)

        if students and len(students) >= 1: #有重复记录
            st = None
            for s in students:
                st = s
                if st.regBranch:
                    if st.regBranch.id == regBranch.id:#已存在客户是网络部录入
                        dup = 1
                        fill(st,student,probability,contractStatus,branch,contract,None,demo)
                        break
                    else:  #不是网络部录入，dup
                        if changeBranch == 0:
                            dup = -1
                            student = isdup(student) 
                        # change for differenct branch
                        else:
                            dup = 1
                            st.regBranch = student.regBranch
                            st.regTeacher = student.regTeacher
                            st.regBranchName = student.regBranchName
                            st.regTeacherName = student.regTeacherName
                            fill(st,student,probability,contractStatus,branch,contract,True,demo)
                        
                        
                        break
                elif str(st.branch.id) == branch_oid: #重复记录是否属于同一校区
                    dup = 1
                    st.regBranch = student.regBranch
                    st.regTeacher = student.regTeacher
                    st.regBranchName = student.regBranchName
                    st.regTeacherName = student.regTeacherName
                    fill(st,student,probability,contractStatus,branch,contract,True,demo)
                    break
                    
                else:
                    #dup = -1
                    #student = isdup(student)
                    st.regBranch = student.regBranch
                    st.regTeacher = student.regTeacher
                    st.regBranchName = student.regBranchName
                    st.regTeacherName = student.regTeacherName
                    dup = 1
                    fill(st,student,probability,contractStatus,branch,contract,True,demo)
                    break
                    
        if notAdd == True:
            continue
        #code and regTime
        if type(row[name_col]) is float:
            student.name = repr(row[code_col]).split(".")[0] 
        else:
            student.name = row[name_col]
        if len(student.name.strip())==0:
            student.name = u'无'
        #except Exception,e:
         #   print age_str
          #  print e
           # birthday = None
        
        
        if student and dup == 0:
            #demo
            student.status = 0
            #contract
            hasContract = 0
                        
             
            student.probability = probability
            student.save()
            if contractStatus == 0 or contractStatus == 2:
                saveContract(student,branch,contract)
            index = index +1
            sheetIndex = sheetIndex + 1
        else:    
            #prepare dup data to add to excel
            if student.dup == -1 and students and len(students)>0:
                for s in students:
                    if s.demo and len(s.demo)>0:
                        dm = GradeClass.objects.get(id=s.demo[0])
                        s.demoTime = dm.start_date
                        if dm.teacher:
                            s.teacherName = dm.teacher.name
                        s.isDemo = dm.demoIsFinish
                    if s.contract and len(s.contract)>0:
                        ct = s.contract[0]
                        s.depositDate = ct.singDate
                        s.uid = ct.paid
                        
                    alldup.append(s)
                if student.demo and len(student.demo)>0:
                        dm = GradeClass.objects.get(id=student.demo[0])
                        student.demoTime = dm.start_date
                        if dm.teacher:
                            student.teacherName = dm.teacher.name
                        student.isDemo = dm.demoIsFinish
                if student.contract and len(student.contract)>0:
                        ct = student.contract[0]
                        student.depositDate = ct.singDate
                        student.uid = ct.paid
                alldup.append(student)
            #===================================================================
            # if isDemo == 1:
            #     demo.students = [student]
            #     demo.branch = branch
            #     demo.gradeClass_type = 2
            #     try:
            #         getStudent = Student.objects.get(id=student.id)
            #     except:
            #         getStudent = None
            #     if getStudent and not getStudent.demo:
            #         isDemo = 2
            #         demo.save()
            #         demos = []
            #         demos.append(str(demo.id))
            #         student.demo = demos
            # 
            # if hasContract == 1:
            #     contract.student_oid = str(student.id)
            #     contract.branch = branch
            #     contract.status = contractStatus
            #     contract.save()
            #     student.contract = [contract]
            # if isDemo == 2 or hasContract == 1:
            #     student.save()
            # 
            #===================================================================
            
        
    print '-----------sheet has rows:'+str(sheetIndex)
    #print table.name 
    
    reload(sys)
    sys.setdefaultencoding('utf8')  # @UndefinedVariable
    row = 1
    if alldup and len(alldup)>0:
        print '--all dup sum--'
        print len(alldup)
        try:
            wbk = xlwt.Workbook() 
            sheet = wbk.add_sheet('sheet 1')
            sheet.write(0,0,u'是否保留')
            sheet.write(0,1,u'级别')
            sheet.write(0,2,u'编号')
            sheet.write(0,3,u'注册时间')
            sheet.write(0,4,u'家长')
            sheet.write(0,5,u'孩子')
            sheet.write(0,6,u'性别')
            sheet.write(0,7,u'年龄')
            sheet.write(0,8,u'电话')
            sheet.write(0,9,u'校区')
            sheet.write(0,10,u'班型')
            sheet.write(0,11,u'来源')
            sheet.write(0,12,u'跟进')
            sheet.write(0,13,u'试听时间')
            sheet.write(0,14,u'到场')
            sheet.write(0,15,u'试听老师')
            sheet.write(0,16,u'成交日期')
            sheet.write(0,17,u'成交额')
            sheet.write(0,18,u'成交')
            sheet.write(0,19,u'备注')
            sheet.write(0,20,u'退费日期')
            sheet.write(0,21,u'退费原因')
            
            
            
            
            for s in alldup:
                sheet.write(row,1,s.probability)
                sheet.write(row,2,s.code)
                if s.regTime:
                    sheet.write(row,3,s.regTime.strftime('%Y-%m-%d %H:%M'))
                else:
                    sheet.write(row,3,'')
                sheet.write(row,4,s.prt1)
                sheet.write(row,5,s.name)
                sheet.write(row,6,s.gender)
                sheet.write(row,7,s.yearMonth)
                sheet.write(row,8,s.prt1mobile)
                sheet.write(row,9,s.branchName)
                sheet.write(row,10,s.wantClass)
                sheet.write(row,11,'')
                
                sheet.write(row,12,s.referrer)#跟进
                
                if s.demoTime:
                    sheet.write(row,13,s.demoTime.strftime('%Y-%m-%d %H:%M'))
                else:
                    sheet.write(row,13,'')#试听时间
                sheet.write(row,14,s.branch4)#1-到场
                sheet.write(row,15,s.teacherName)#试听课老四和
                if s.depositDate:
                    sheet.write(row,16,s.depositDate.strftime('%Y-%m-%d %H:%M'))
                else:
                    sheet.write(row,16,'')#成交日期
                sheet.write(row,17,s.uid)#成交额
                sheet.write(row,18,s.status)#成交
                sheet.write(row,19,s.memo)
                if s.callInTime:
                    sheet.write(row,20,s.callInTime.strftime('%Y-%m-%d %H:%M'))
                else:
                    sheet.write(row,20,'')#退费日期
                sheet.write(row,21,s.referrerName)#退费memo
                
                
                
                row = row + 1
            wbk.save(BASE_DIR+USER_IMAGE_DIR+branch.branchCode+'_dup.xls')
        except Exception,e:
            print e
    
    
  print '[DONE]'  
   
  return index 

def saveContract(student,branch,contract):

    contract.student_oid = str(student.id)
    if not contract.status:
        contract.status = 0
    contract.branch = branch
    contract.student_name = student.name

    contract.save()
    cts = []
    cts.append(contract)
    student.contract = cts
    if contract.status == 0:
        student.status = 1
    else:
        student.status = contract.status
    try:
        student.save()
    except:
        print student.prt1mobile
        print student.memo
    getId('contract save--',student)
    return

def getId(tag,student):
    return
            
def fill(student1,student,probability,contractStatus,branch,contract,doSave=False,demo=None):
    if not student1.regBranch:
        student1.regBranch = student.regBranch
        student1.regBranchName = student.regBranchName
        doSave = True
                            
    if not student1.regTeacher:
        student1.regTeacher = student.regTeacher
        student1.regTeacherName = student.regTeacherName
        doSave = True
   
    if not student1.code:
        student1.code = student.code
        if student1.code:
            doSave = True
      
    #if not student1.memo:
    if True:
        student1.memo = student.memo
        if student1.memo:
            doSave = True
    if not student1.prt1:
        student1.prt1 = student.prt1
        if student1.prt1:
            doSave = True
    
    if not student1.birthday:
        student1.birthday = student.birthday
        if student1.birthday:
            doSave = True
    if not student1.gender:
        student1.gender = student.gender
        if student1.gender:
            doSave = True
    
    if not student1.demo or len(student1.demo) == 0:
        if demo and demo.demoIsFinish == 1:
            demo.save()
            doSave = True
            student1.demo = []
            student1.demo.append(str(demo.id))
            student1.isDemo = 1
            
    if not student1.wantClass:
        student1.wantClass = student.wantClass
        if student1.wantClass:
            doSave = True
    
    if probability == 'C' and student1.probability != 'C':
        student1.probability = 'C'
        doSave = True
    if contractStatus == 0:
        student1.status = 1
        if student1.contract and len(student1.contract)>0:
            student1.contract[0].status = 0
            student1.contract[0].save()
        else:
            saveContract(student1,branch,contract)
    elif contractStatus == 2:
        student1.status = 2
        if student1.contract and len(student1.contract)>0:
            student1.contract[0].status = 2
            student1.contract[0].save()
            doSave = True
        else:
            saveContract(student1,branch,contract)
    if doSave:
        student1.save()
        getId('fill 0',student)

    return

def isdup(student):
    student.dup = -1
    student.resolved = -1
    return student



def saveLesson(gc,lessonTime,type,teacher,lessonId,studentId,checked,value,oriTime=None,memo=None,oriLessons=None):
    lesson = None
    if not lessonId:
        lessons = None
        if type == 0:
            lessons = Lesson.objects.filter(gradeClass=gc).filter(type=type).filter(lessonTime=lessonTime)  # @UndefinedVariable
        else:
            lessons = Lesson.objects.filter(gradeClass=gc).filter(type=type).filter(lessonTime=lessonTime).filter(student=studentId)  # @UndefinedVariable
        if lessons and len(lessons)>0:
            res = {"error": 1, "msg": "已存在！"}
            return http.JSONResponse(json.dumps(res, ensure_ascii=False))
        else:
            lesson = Lesson()
    else:
        if type == 0 or type == 2:
            lesson = Lesson.objects.get(id=lessonId)  # @UndefinedVariable
                
        else:
            try:
                lid = str(lessonId)
                query = (Q(type=1)|Q(type=3))&Q(lessonId=lid)&Q(student=studentId)
                ls = Lesson.objects.filter(query)  # @UndefinedVariable
                if ls and len(ls)>0:
                    lesson = ls[0]
                
            except:
                lesson = Lesson()
        if not lesson:
            lesson = Lesson()
    try:
        cando = True
        if studentId:
            try:
                st = Student.objects.get(id=studentId)
                lesson.student = studentId
            except:
                cando = False
                res = {"error": 1, "msg": "student not found"}
        if cando:
            
            lesson.lessonTime = lessonTime
            lesson.gradeClass = gc
            lesson.teacher = teacher
            lesson.type = type
            if type != 0:
                lesson.lessonId = str(lessonId)
            lesson.checked = checked
            lesson.value = value
            if memo:
                lesson.memo = memo
            if oriLessons:
                lesson.oriLessons = oriLessons
            lesson.save()
    
        #=======================================================================
        # if (type == 1 or type == 3) and studentId:
        #     sl = Lesson.objects.filter(student=studentId).filter(value__ne=0).filter(type__ne=2)
        #     lessonCount = 0
        #     for l in sl:
        #         lessonCount = l.value + lessonCount 
        #     #lessonCount = Lesson.objects.filter(student=studentId).filter(value__ne=0).filter(type__ne=2).count()
        #     student = Student.objects.get(id=studentId)
        #     student.lessons = lessonCount
        #     student.save()
        #=======================================================================

    except Exception,e:
        print e    
    res = {"error": 0, "msg": "OK"}
    return http.JSONResponse(json.dumps(res, ensure_ascii=False))

    
def makeLessons(gc):

    dateNowStr = None
    try:
        dateNowStr = utils.getDateNow().strftime("%Y-%m-%d")
    except Exception,e:
        print e

    classId = gc.id
    interval0 = 0
    classDate0 = None

    try:
        if gc.start_date:
            classDate0 = gc.start_date
        else:
            print '[err start_date]'
            return

        if gc.school_day:
            interval0 = gc.school_day - 1 - classDate0.weekday()
        else:
            print '[ERR-school_day]'+gc.name
            return

    except Exception,e:
        print gc.name + str(e)
        
        return

    if interval0 < 0:
        interval0 = interval0 + 7

    if interval0 > 0:
        try:
            #delta = 
            classDate0 = classDate0 + timedelta(days=interval0)
        except Exception,e:
            print e
            print gc.name
            print classDate0
            print classDate0.weekday()
            print interval0
    try:
        classDate0 = datetime.datetime.strptime(classDate0.strftime('%Y-%m-%d') + ' ' + gc.school_time,'%Y-%m-%d %H:%M')
    except Exception,e:
        print classDate0
        print e
        print gc.school_time
        print gc.name
        return False
    
    lastLesson = None
    lastDate = None
    try:
        lastQuery = Q(gradeClass=classId)&Q(type=0)
        lastLesson = Lesson.objects.filter(lastQuery).order_by("-lessonTime")[0]  # @UndefinedVariable
        lastTime = lastLesson.lessonTime
    except Exception,e:
        #print e
        lastLesson = None
        lastTime = None
        
    lessonTime = classDate0
    
    canSave = False
    if not lastTime:
        canSave = True
    elif lastTime and lastTime<lessonTime:
        canSave = True
    if canSave:
        saveLesson(gc,lessonTime,0,gc.teacher,None,None,False,None)
    getNow = False#是否课程添加到现在了
    for i in range(1,10000):
        if not getNow:
            classDate0 = classDate0 + timedelta(days=7)
            datestr = classDate0.strftime("%Y-%m-%d")
            if datestr > dateNowStr:
                getNow = True
            lessonTime = classDate0
            canSave = False
            if not lastTime:
                canSave = True
            elif lastTime and lastTime<lessonTime:
                canSave = True
            if canSave:
                saveLesson(gc,lessonTime,0,gc.teacher,None,None,False,None)
        else:
            break
    return True

def getDateFromExcel(cell,excel):
    
    date = None
    try: 
        date = xlrd.xldate.xldate_as_datetime(cell,excel.datemode)  
    except:
        try:
            dstr = cell
            if type(cell) is float:
                dstr = str(int(cell)) 
            date = datetime.datetime.strptime(dstr,'%Y%m%d')

        except  Exception,e:
                date = None
                print cell
                print e
    return date

def getSchoolTime(classtime):
    school_time = None
    try:
        if '-' in classtime:
            css = classtime.split('-')
            if css and len(css) > 0:
                classtime = css[0][2:len(classtime)]
        else:
            classtime = classtime[2:len(classtime)]

        ts = classtime.split(':')
        if ts and len(ts) == 1:
            ts = classtime.split('：')
        if ts and len(ts) == 1:
            ts = classtime.split('点')
        if ts and len(ts) == 1:
            return None
        if len(ts[0]) == 1:
             ts[0] = '0' + ts[0]
        if len(ts[1]) == 0:
            ts[1] = '00'
        if len(ts[1]) == 1:
            ts[1] = ts[1] + '0'
        school_time = ts[0] + ':' + ts[1]
        #school_times = school_time.split('-')
        #school_time = school_times[0]  
    except Exception,e:
        print e
        school_time = None
    if not school_time:
        print classtime
    return school_time
    
def getSchoolDay(school_day_str):
        school_day = None
        if school_day_str == u'周一':
            school_day = 1
        if school_day_str == u'周二':
            school_day = 2
        if school_day_str == u'周三':
            school_day = 3
        if school_day_str == u'周四':
            school_day = 4
        if school_day_str == u'周五':
            school_day = 5
        if school_day_str == u'周六':
            school_day = 6
        if school_day_str == u'周日':
            school_day = 7
        if not school_day:
            print school_day_str
        return school_day
#===============================================================================
# 1、20周5800
# 2、40周9800
# 3、80周18600
# 4、120周274005
# 5、4周试学1000
# 6、1周暑期班1000
#===============================================================================
# 2018-4 倒入老生合同、班级和签到信息
def getUserFromExcel_2(filepath,branch_oid,commonMethod=None):
    
  index = 0#保存学生总数
  if True:
    reload(sys)
    sys.setdefaultencoding('utf8')  # @UndefinedVariable
    branch = Branch.objects.get(id=branch_oid)# @UndefinedVariable
    query = Q(city=branch.city.id)&Q(type=0)
    cityContracts = ContractType.objects.filter(query)
    ccts = {}
    if constant.DEBUG:
        print '1'
    for cct in cityContracts:
        if cct.code:
            ccts[cct.code] = cct.id
    if constant.DEBUG:
        print '2'
    
    excel = None
    try:
        excel = xlrd.open_workbook(BASE_DIR+USER_IMAGE_DIR+filepath)
    except Exception,e:
        #print e
        try:
            excel = xlrd.open_workbook(BASE_DIR+USER_IMAGE_DIR+filepath+"x")
        except:
            print 'no file found'
            return

    table = None
    try:
        table = excel.sheets()[0]
    except:
        print 'fail to get sheet'
        return 
    nrows = table.nrows #行数
    ncols = table.ncols #列数
    common_col = 0
    name_col = 1
    gender_col = 2
    birthday_col= 3
    mobile_col = 4
    c_singDate = 5
    c_weeks = 6
    c_paid = 7
    c_multi = 8
    c_beginDate = 9
    teacher_col = 10
    classtime_col = 11
    remain_col = 12
    memo_col = 13
    #1姓名 2性别 3出生日期 4手机号码 5签约日期 6实际周数 7实付金额 8合同类型 9开课日期 10授课老师 11上课时间 12剩余周数 13备注

    dup = 0

    #===========================================================================
    # 导入班级           
    #===========================================================================

    for i in range(1,nrows):
      try:
        hasClass = False
        row = table.row_values(i)
        gc = GradeClass()
        gc.branch = branch
        classtime = row[classtime_col].strip()
        teacherName = row[teacher_col].strip()
        
        gc.gradeClass_type = 1
        beginDate = getDateFromExcel(row[c_beginDate],excel)
        singDate = getDateFromExcel(row[c_singDate], excel)

        if not beginDate:
            if singDate:
                beginDate = singDate
            else:
                print '[ERR No beginDate and singDate]' + str(row[name_col])
                return
        gc.start_date = beginDate
        school_day = None
        school_day_str = classtime[0:2]

        school_day = getSchoolDay(school_day_str)
        school_time = getSchoolTime(classtime)
        toSaveClass = True
        try:
            gc.name=teacherName+school_day_str+school_time
        except:
            toSaveClass = False
            print '[NO CLASS]'+str(row[name_col])
            print teacherName
            print school_day_str 
            print school_time
            continue
        if type(gc.name) == float:
            gc.name = str(int(gc.name))

        teacher = None
        try:
            query = Q(name=teacherName)&Q(branch=branch_oid)&Q(status__ne=-1)
            
            teacher = Teacher.objects.get(query)  # @UndefinedVariable
            
            gc.teacher = teacher
        except:
            print 'no this teacher:' + teacherName
        oldcalss = None
        gc.school_day = school_day
        gc.school_time = school_time

        if teacher:
            try:
                query = Q(branch=branch_oid)&Q(teacher=teacher.id)&Q(school_day=school_day)&Q(school_time=school_time)
                oldclass = GradeClass.objects.get(query)
                hasClass = True
                
            except:
                oldcalss = None

        if not hasClass:
          try:
            query = Q(branch=branch_oid)&Q(name=gc.name)
            oldclasses = GradeClass.objects.filter(query)
            if oldclasses and len(oldclasses) > 0:
                oldclass = oldclasses[0]
                hasClass = True
          except:
            oldcalss = None
        #print school_time
        if not hasClass and toSaveClass:
            #print 'add class:'+gc.name
            gc.save()

        else:
            oldclass.school_day = gc.school_day
            oldclass.school_time = gc.school_time
            if not oldclass.start_date:
                oldclass.start_date = gc.start_date
            elif gc.start_date < oldclass.start_date:
                oldclass.start_date = gc.start_date
            if gc.teacher:
                try:
                    ttt = Teacher.objects.get(id=gc.teacher.id)  # @UndefinedVariable
                    gc.teacher = ttt
                except:
                    gc.teacher = None 
                    print '[gc teacher wrong!]'  
                oldclass.teacher = gc.teacher
            else:
                print '[gc has no teacher!]'+gc.name
            oldclass.save()

            
      except Exception,e:
          print e
          print i
    #===========================================================================
    # 导入班级结束           
    #===========================================================================
    
    print '1'
    
    #===========================================================================
    # 自动生成签到表开始
    #===========================================================================
    query = Q(branch=branch_oid)&Q(deleted__ne=1)&Q(gradeClass_type=1)
    classes = GradeClass.objects.filter(query)
    
    print '[TOTAL CLASSES]'+str(len(classes))
    i = 0
    for c in classes:
        #if i == 0:
            if c.start_date and c.start_date < utils.getDateNow():
                if not makeLessons(c):
                    print '[MAKELESSON ERR]' + row[name_col]
                    print c.name
                    return
                i = i + 1
                print '[make lesson]' + str(i)

    #===========================================================================
    # 自动生成签到表结束
    #===========================================================================
         
    lastClass = None
    noindex = 0
    lastName = 'name'
    intoIndex = 0 #入班学生数
    dupIndex = 0 #与其他校区重复数
    wrongIndex = 0 #错误号码计数
    contractIndex = 0#写入合同数
    allstudents = []
    allcommons = []#共用学籍的所有学生
    #===========================================================================
    # 开始导入学生
    #===========================================================================
    for i in range(1,nrows):
        dup = 0 #标记，0-可以写入，1-无电话数据不能写入，－1:和其他校区重复的数据，不能写入
        row = table.row_values(i)
        student = Student()
        classtime = row[classtime_col].strip()
        teacherName = row[teacher_col].strip()
        classname=teacherName+classtime

        if classname:
            lastClass = classname
        else:
            classname = lastClass
        
        student.name = row[name_col]
        
        if not student.name: 
            if not lastName:
                noindex = noindex + 1
        else:
            noindex = 0
        if noindex > 2:
            break
        if student.name:
            student.name = student.name.strip() 
        lastName = student.name
        if gender_col>-1:
            if type(row[gender_col]) == str:
                student.gender = row[gender_col].strip()
        if birthday_col > -1:
            birthday = None
            birthday = getDateFromExcel(row[birthday_col],excel)
            
            student.birthday = birthday

        student.branch = branch
        student.branchName = branch.branchName
        weeksStr = utils.cellToStr(row[c_weeks])
        weeks = -1
        if weeksStr:
            weeks = int(weeksStr)
        #=======================================================================
        # 共用学籍号填入code字段
        #=======================================================================
        common_code = row[common_col]

        commons = None
        if type(row[common_col]) is float:
            common_code = str(int(row[common_col]))

        if common_code and len(common_code) > 3:
            
            print '[has common]'
            student.code = common_code
            student.commonCheckin = weeks
            
            print common_code
            query = Q(branch=branch_oid)&Q(code=common_code)
            commons = Student.objects.filter(query)
            print commons._query
        common = None
        if commons and len(commons) > 0:
            common = commons[0]
            print common.name
        dup = 0
        mstr = utils.cellToStr(row[mobile_col])
        #=======================================================================
        # 电话号码查重
        #=======================================================================
        if mstr and len(mstr)>6 and not common:
            student.prt1mobile = mstr
            if u'妈妈' in mstr:
                sss = mstr.split(u'妈妈')
                if len(sss) >1:
                    for s in sss:
                        if len(s) > 5:
                            student.prt1mobile = s
                            break
            if u'爸爸' in mstr:
                sss = mstr.split(u'爸爸')
                if len(sss) >1:
                    for s in sss:
                        if len(s) > 5:
                            student.prt1mobile = s
                            break
            students = Student.objects.filter(prt1mobile=student.prt1mobile)
            if students: #记录已存在
                if len(students) >= 1: #有重复记录
                    st = None
                    for s in students:
                        
                        st = s

                        if str(st.branch.id) == str(branch_oid):#重复记录是本校区的
                            s.name = student.name
                            s.code = student.code
                            student = s
                             
                            dup = 0
          
                            break
                        else:
                            #重复是其他校区的
                            if not st.contract: #其他校区没有合同，可以导入
                                dup = 0
                            elif len(st.contract) == 0:
                                dup = 0
                            else:  #其他校区有合同
                                dupIndex = dupIndex + 1
                                student.dup = -1
                                student.resolved = -1
                                dup = -1
                            
                                if st.regBranch:#有其他拜访校区
                                    
                                    if st.status == 1 and len(st.contract) > 0:#其他校区合同有效
                                        print mstr+'-其他校区已录入：'+st.regBranch.branchName
                                        file_object = open(LOG_FILE, 'a')
                                        time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                                        file_object.seek(0, 2)
                                        try:
                                            file_object.write('['+time+']['+branch.branchName.encode('utf-8')+'-'+student.name.encode('utf-8')+'['+st.branch.branchName.encode('utf-8')+']['+st.prt1mobile+']重复\n')
                                        except Exception,e:
                                            print e
                                        file_object.close( )
                                    else:#其他校区合同无效了
                                        st.prt1mobile = st.prt1mobile + 'A'
                                        st.save()
                                        dup = 0
                                else:
                                    #没有拜访校区，删除之
                                    st.delete()
                                    dup = 0
                            break
        #=======================================================================
        # 共用学籍，已存在数据添加siblingName，新数据添加siblingId
        #=======================================================================
        elif common:
            print 'has sibling---------------'
            common.siblingName = student.name
            common.save()
            student.siblingId = str(common.id)
            student.siblingName = common.name
            student.status = 1
            dup = 0
        else:
            dup = 1
            wrongIndex = wrongIndex + 1
            print mstr+'-号码过短'
        #=======================================================================
        # 电话号码查重结束
        #=======================================================================
        if dup == 0:
            query = Q(name=student.name)&Q(branch=branch.id)&Q(status=constant.StudentStatus.sign)
            students = Student.objects.filter(query)
            if student.name == u'施泓辰':
                print '[----------GOT------------]'
                print students._query
            for s in students:
                        
                        print '[----------GOT------------]' + student.name
                        st = s

                        if str(st.branch.id) == str(branch.id):#重复记录是本校区的
                            s.name = student.name
                            if student.code:
                                s.code = student.code
                            student = s
                             
                            dup = 0
          
                            break    
        

        thisHas = False
        if student.name == u'施泓辰':
            print student.id
        if dup == 0:
          try:

            if student.name == u'李清瑞':
                print u'[李清瑞]in'
            if str(student.id) not in allstudents or common:
                if student.name == u'李清瑞':
                    print u'[李清瑞]2'
                student.save()
                if common_code and len(common_code) > 3:
                    allcommons.append(student)
                if str(student.id) not in allstudents:
                    allstudents.append(str(student.id))
            else:
                stu = Student.objects.get(id=student.id)
                student = stu
                thisHas = True
            index = index +1
            
            #===================================================================
            # 写入合同开始
            #===================================================================
            contract_status = 0
            cstatus = 0
            singDate = None
            singDate = getDateFromExcel(row[c_singDate], excel)
            beginDate = getDateFromExcel(row[c_beginDate],excel)
            
            if not singDate:
                if beginDate:
                    singDate = beginDate
                else:
                    print '[ERR singdate]'+row[name_col]+'-'+str(row[c_singDate])
                    print 'Terminate!'
                    return

            if not beginDate:
                if singDate:
                    beginDate = singDate
                else:
                    print '[ERR No beginDate]' + str(row[name_col])
                    return
            
            
            paidStr = utils.cellToStr(row[c_paid])
            paid = -1
            if paidStr:
                paid = int(paidStr)
            
            remain = 0
            try:
                remain = int(utils.cellToStr(row[remain_col]))
                #print '剩余课时：'+str(remain)
            except:
                remain = weeks   
            
            checkin = weeks - remain #已上次数
            if checkin < 0:
                checkin = 0
            
            if singDate and paid > -1 and weeks > -1 and cstatus == 0:

                #beginDate = getDateFromExcel(row[c_beginDate], excel)

                multi = constant.MultiContract.newDeal
                multiStr = row[c_multi]
                if multiStr == u'老生续费':
                    multi = constant.MultiContract.oldRedeal
                if multiStr == u'新生续费':
                     multi = constant.MultiContract.newRedeal
                if multiStr == u'新生' or multiStr == u'新招生':
                     multi = constant.MultiContract.newDeal
                
                contractType = None
                try:
                    contractType = ccts['01']
                except:
                    contractType = None
                contract = Contract()
                
                contract.singDate = singDate
                contract.student_oid = str(student.id)
                contract.branch = branch
                contract.beginDate = beginDate
                contract.status = cstatus
                contract.paid = paid
                contract.weeks = weeks 
                contract.multi = multi
                contract.contractType = contractType
                ccs = Contract.objects.filter(student_oid=contract.student_oid)
                hasContract = False
                for c in ccs:
                    #hasContract = True
                    #print 'has contract:'+str(c.id)
                    if not thisHas:
                        c.delete()
                contractIndex = contractIndex + 1
                if common and commonMethod == 2:
                    ccc = common.contract[0]
                    if ccc and ccc.weeks:
                        ccc.weeks = ccc.weeks * 2
                        ccc.save()
                        print student.name+'[common weeks]'+str(ccc.weeks)
                else:
                    contract.save()
                
                if not thisHas:
                    
                    
                    #===========================================================
                    # 把学生写入班级
                    #===========================================================

                    try:
                        branch = student.gradeClass.branch

                    except:
                        #print '[has wrong class]'+student.name
                        student.gradeClass = None
                        student.save()

                    if not student.gradeClass:

                        school_day = None
                        school_day_str = classtime[0:2]
                        school_day = getSchoolDay(school_day_str)
                        classtime = row[classtime_col]
                        if type(classtime) == str:
                            classtime = classtime.strip()
                        teacherName = row[teacher_col]
                        if type(teacherName) == str:
                            teacherName = teacherName.strip()
                        classname=teacherName+classtime
                         
                        school_time = getSchoolTime(classtime)
                        try:
                            query = Q(name=teacherName)&Q(branch=branch_oid)&Q(status__ne=-1)
                            teacher = Teacher.objects.get(query)  # @UndefinedVariable
                            
                        except:
                            print 'no this teacher' + teacherName
                        oldcalss = None

                        if teacher:
                            student.teacher = teacher
                            student.teacherName = teacher.name
                            try:
                                query = Q(branch=branch_oid)&Q(teacher=teacher.id)&Q(school_day=school_day)&Q(school_time=school_time)
                                oldclasses = GradeClass.objects.filter(query)
     
                                if oldclasses and len(oldclasses) > 0:
                                    oldclass = oldclasses[0]
                                hasClass = True
                                s = oldclass.students
                                if not s:
                                    s = []
                                s.append(student)
                                oldclass.students = s
                                oldclass.save()
                                student.gradeClass = str(oldclass.id)
                                intoIndex = intoIndex + 1

                            except Exception,e:
                                print e
                                oldcalss = None
                    csss = []
                else:
                    csss = student.contract
                
                csss.append(contract)
                if not common:
                    student.contract = csss
                student.status = constant.StudentStatus.sign
                student.save()

                #===============================================================
                # 写入合同结束
                #===============================================================
            
            #===================================================================
            # 添加签到开始
            #===================================================================
            endDate = None
            #找到班级和最近一次可签到课
            query = Q(student=str(student.id))&(Q(type=1)|Q(type=2))&Q(checked=True)
            checkedLessons = Lesson.objects.filter(query)  # @UndefinedVariable
            if checkedLessons and len(checkedLessons) > 0:
                checkin = checkin - len(checkedLessons)
            if student.gradeClass and checkin > 0 and not thisHas:

                dateNow = utils.getDateNow()
                sid = student.id
                if common:
                    sid = common.id
                query = Q(student_oid=str(sid))&Q(beginDate__ne=None)&Q(status__ne=constant.ContractStatus.delete)
                cs = Contract.objects.filter(query).order_by("beginDate")

                beginDate = None
                if cs and len(cs) > 0:
                    beginDate = cs[0].beginDate
                query = Q(gradeClass=student.gradeClass)&Q(type=0)&Q(lessonTime__gte=beginDate)&Q(lessonTime__lt=dateNow)
                lessons = Lesson.objects.filter(query).order_by("-lessonTime")  # @UndefinedVariable
                #print '[checkin]'+str(checkin)#已上次数
                #print len(lessons)
                #print lessons._query
                lessonIndex = 0
                query = Q(type__ne=0)&Q(student=str(student.id))&Q(checked=1)
                checkedLessons = Lesson.objects.filter(query)  # @UndefinedVariable
                if checkedLessons and len(checkedLessons) > 0:
                    lessonIndex = len(checkedLessons)

                if lessonIndex < checkin:
                  for l in lessons:
                    lessonId = l.id 
            #班级签到，表示签到表上此次课已有学生上了
                    l.checked = True
                    l.save()
            #学生签到
                    lesson = Lesson()
                    lesson.teacher = l.teacher
                    lesson.gradeClass = l.gradeClass
                    lesson.student = str(student.id)
                    lesson.type = 1
                    lesson.lessonId = str(lessonId)
                    lesson.checked = True
                    lesson.lessonTime = l.lessonTime
                    lesson.save()
                    lessonIndex = lessonIndex + 1
                    if lessonIndex >= checkin:
                        break

                

                try:
                    print '['+student.name+']签到' + str(lessonIndex)
                except:
                    err = 0

            try:
                    beginDate,endDate,days,learnDays = util2.getLessonCheckDeadline(str(student.id))
                    endDate,learnDays = util2.getEndDateAddVocation(beginDate, endDate, branch.city.id,learnDays)
                    endDate,learnDays = util2.getEndDateAddSuspension(beginDate, endDate, str(student.id),learnDays)
                    if student.contractDeadline != endDate:
                        student.contractDeadline = endDate
                    if constant.DEBUG:
                        print endDate    
                    allLessons,sd,lessonLeft = utils.getLessonLeft(student)
                    student.lessons = allLessons - lessonLeft
                    student.lessonLeft = lessonLeft
                    if constant.DEBUG:
                        print '[lessons]'+str(student.lessons)
                    student.save()
            except Exception,e:
                    print e
                    print '[ERR]'+student.name
                
          except Exception,e:
              print e 
        else:
            dup = 0
  allcommons = sorted(allcommons, key=attrgetter('code'),reverse=True)
  lastCode = None
  i = 0
  allweeks = 0
  for s in allcommons:
        print s.name + str(s.commonCheckin)
        if s.code != lastCode:
            lastCode = s.code
            if i > 0:
                sid = s.id
                if s.siblingId:
                    sid = s.siblingId
                query = Q(student_oid=str(sid))&Q(status=constant.ContractStatus.sign)
                cs = Contract.objects.filter(query)
                if cs and len(cs) > 0:
                    c = cs[0] 
                    c.weeks = allweeks
                    c.save()
                    print s.name + '[update common contract weeks]' + str(c.weeks)
                allweeks = 0
        try:
            allweeks = allweeks + s.commonCheckin
        except Exception,e:
            print e
            print s.name
            
              
  print '[excel lines]' + str(index)
  print '[students]' + str(len(allstudents))
  print '[contracts]' + str(contractIndex)
  print '[into class]' + str(intoIndex)
  print '[dups]' + str(dupIndex)
  print '[wrong tel]' + str(wrongIndex)
  return index

def job_calEndDate(branchCode):
    print '[BRGIN Calculate contracts endDate]'
    branch = Branch.objects.get(branchCode=branchCode)  # @UndefinedVariable
    query = Q(status=constant.StudentStatus.sign)&Q(contractDeadline=None)&Q(branch=branch.id)
    students = Student.objects.filter(query)
    for s in students:
        beginDate,endDate,days,learnDays = util2.getLessonCheckDeadline(str(s.id))
        endDate,learnDays = util2.getEndDateAddVocation(beginDate, endDate, branch.city.id,learnDays)
        endDate,learnDays = util2.getEndDateAddSuspension(beginDate, endDate, str(s.id),learnDays)
        s.contractDeadline = endDate
        s.save()
        allLessons,sd,lessonLeft = utils.getLessonLeft(s)
    print '[END Calculate contracts endDate]'


def job_getUserFromExcel_2(branchCode,commonMethod=None):
    #commonMethod == 2:合同周数要翻倍
    print '[branch]'+branchCode
    branch = Branch.objects.get(branchCode=branchCode)  # @UndefinedVariable
    util2.del_contracts(branch.id)
    util2.del_classes(branch.id)
    getUserFromExcel_2('2-'+branchCode+'.xls',branch.id,commonMethod)
    job_calEndDate(branchCode)

if __name__ == "__main__":
    job_getUserFromExcel_2('lg',2)
    #job_getUserFromExcel_2('zgc',2)
    
    #job_calEndDate('zgc')
    #===========================================================================
    #print(getSchoolTime(u'周五9:0'))
    # print(getSchoolTime('9点0'))
    # print(getSchoolTime('9：0'))
    # print(getSchoolTime('9点'))
    #===========================================================================
    