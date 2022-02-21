#!/usr/bin/env python
# -*- coding:utf-8 -*-
from django.core.files.storage import FileSystemStorage
from datetime import timedelta
__author__ = 'patch'

import sys,hashlib, os, time, datetime, StringIO
import  xlrd,re,xlwt, subprocess,logging

from mongoengine.queryset.visitor import Q
from PIL import Image, ImageOps
from PIL.ExifTags import TAGS
from django.core.files import File

from branch.models import Branch
from go2 import settings
from go2.settings import BASE_DIR,USER_IMAGE_DIR,ALLOWED_HOSTS
from gradeClass.models import Lesson
from regUser.models import *
from teacher.models import Teacher,Login_teacher,Message
from tools.templatetags.filter_gradeClass import get_gradeClass_type
from tools import constant

# Get an instance of a logger
logger = logging.getLogger('utils')

#文件备份服务器地址
REMOTE_BK_DIR = "root@172.16.27.68:/root"

def now2datetime(convert_to_local=True):
    now = long(time.time())
    return timestamp2datetime(now, convert_to_local)

def timestamp2datetime(timestamp, convert_to_local=True):
    ''' Converts UNIX timestamp to a datetime object. '''
    if isinstance(timestamp, (int, long, float)):
        dt = datetime.datetime.utcfromtimestamp(timestamp)
        if convert_to_local:  # 是否转化为本地时间
            dt = dt + datetime.timedelta(hours=8)  # 中国默认时区
        return dt
    return timestamp

def getTeachers(branchId,roleExs=None,includeQuit=None):
    if not roleExs:
        roleExs = [9]
    query = Q(branch=branchId)&Q(status=0)
    if includeQuit == True:
        query = Q(branch=branchId)
    if roleExs and len(roleExs)>0:
        for ex in roleExs:
            query = query&Q(role__ne=ex)
    teachers = Teacher.objects.filter(query).order_by("id")  # @UndefinedVariable
    return teachers

def getDateNow(hours=None):
    #print hours
    if not hours:
        hours = 0

    d1 = datetime.datetime.now()
    timeNow = d1+datetime.timedelta(hours=hours)
    #print d1
    #print timeNow
    return timeNow

def getWeekFirstDay(firstDay,isNET=None):
    if not firstDay:
        firstDay = getWeekBegin(getDateNow(8), isNET)
        #=======================================================================
        # now = now2datetime()
        # now_day = now.isoweekday()  # 今天是本周第几天
        # delte = 1 - now_day
        # firstDay = now + datetime.timedelta(days=delte)  # 本周第一天
        #=======================================================================

    firstDay = firstDay.replace(hour=0)
    print 'yyyyyyyyyy'
    firstDay = firstDay.replace(minute=0)
    firstDay = firstDay.replace(second=0)
    print 'ssssssssssssssss'
    firstDay = firstDay.replace(microsecond=0)

    lastDay = firstDay + datetime.timedelta(days=6)
    lastWeekFirstDay = firstDay + datetime.timedelta(days=-7)
    nextWeekFirstDay = firstDay + datetime.timedelta(days=7)

    return firstDay,lastDay,lastWeekFirstDay,nextWeekFirstDay

def getWeekBegin(somedate,isNET=None):
    weekday = somedate.weekday()
    if isNET == 1:
        weekday = weekday
    else:
        if weekday == 0:
            weekday = 6
        else:
            weekday = weekday -1

    weekbegin = somedate - datetime.timedelta(days=weekday)
    weekbegin = datetime.datetime.strptime(weekbegin.strftime("%Y-%m-%d")+" 00:00:00","%Y-%m-%d %H:%M:%S")
    #logger.log('weekbegin--------------------------------------------------------')
    return weekbegin

def dateOfYearMonth(year,month):
    yd = int(float(year))*365
    md = 0
    if month:
        try:
            md = int(float(month))*30
        except:
            md = 0

    days = yd + md
    now = getDateNow()
    ageDate = now - datetime.timedelta(days=days)
    return ageDate

def str2md5(str):
    try:
        m = hashlib.md5()
        m.update(str)
        return m.hexdigest()
    except:
        return None


def save_log(filename, info):
    txt = info.encode("utf-8")

    dir = os.path.join(settings.BASE_DIR, 'log')
    if not os.path.exists(dir):
        os.mkdir(dir)
    file = os.path.join(dir, filename + ".log")
    if os.path.exists(file):
        file_w = open(file, "a")
    else:
        file_w = open(file, "w")
    file_w.write("\n" + txt)
    file_w.close()

# 课程
def get_gradeClass_from_oid(oid):
    if not oid or len(oid) == 0:
        return GradeClass()
    else:
        try:
            return GradeClass.objects.get(id=oid)
        except:
            return None


# 教室
def get_classroom_from_oid(oid):
    try:
        return Classroom.objects.get(id=oid)
    except:
        return None

def get_branch_from_oid(oid):
    try:
        return Branch.objects.get(id=oid)  # @UndefinedVariable
    except:
        return None

# 老师
def get_teacher_from_oid(oid):
    try:
        return Teacher.objects.get(id=oid)  # @UndefinedVariable
    except:
        return None

def getStat(login_teacher,isOwn,tag,beginDate,endDate):
    stat = Stat()
    stat.dayTag = tag
    if isOwn:
        stat.visit = Student.objects.filter(regTeacher=login_teacher.id).filter(regTime__gte=beginDate).filter(regTime__lte=endDate).count()
    else:
        stat.visit = Student.objects.filter(branch=login_teacher.branch).filter(regTime__gte=beginDate).filter(regTime__lte=endDate).count()
    if not stat.visit:
        stat.visit = 0
    if isOwn:
        stat.demo = GradeClass.objects.filter(start_date__gte=beginDate).filter(start_date__lte=endDate).filter(demoIsFinish=1).filter(teacher=login_teacher.id).count()
        #stat.demo = Student.objects.filter(regTeacstatisticlogin_teacher.id).filter(demo__start_date__gte=beginDate).count()
    else:
        stat.demo = GradeClass.objects.filter(start_date__gte=beginDate).filter(start_date__lte=endDate).filter(demoIsFinish=1).filter(branch=login_teacher.branch).count()
        #stat.demo = Student.objects.filter(branch=statisticn_teacher.branch).filter(demo__start_date__gte=beginDate).count()
    if not stat.demo:
        stat.demo = 0
    ct = ContractType.objects.filter(city=login_teacher.cityId).filter(duration=4)
    if isOwn:
        stat.sign = Contract.objects.filter(teacher=login_teacher.id).filter(singDate__gte=beginDate).filter(singDate__lte=endDate).count()
        #stat.sign = Student.objects.filter(regTeacstatisticlogin_teacher.id).filter(contract__singDate__gte=beginDate).count()
    else:
        stat.sign = Contract.objects.filter(branch=login_teacher.branch).filter(singDate__gte=beginDate).filter(singDate__lte=endDate).count()
    if not stat.sign:
        stat.sign = 0
    return stat


def checkCookie(request):
    login_teacher = Login_teacher()
    username = request.COOKIES.get('username', '')
    if not (username):
        # return HttpResponseRedirect('/travel/login')
        return None
    login_teacher.username = username
    login_teacher.role = int(request.COOKIES.get('role', ''))
    login_teacher.branchName = request.COOKIES.get('branchName', '')
    login_teacher.branchTel = request.COOKIES.get('branchTel', '')
    login_teacher.branch = request.COOKIES.get('branch', '')
    login_teacher.id = request.COOKIES.get('userid', '')

    login_teacher.roleName = request.COOKIES.get('roleName', '')
    login_teacher.teacherName = request.COOKIES.get('teacherName', '')
    login_teacher.name2 = request.COOKIES.get('name2', '')
    login_teacher.page = request.COOKIES.get('teacherPage', '')
    login_teacher.cityId = request.COOKIES.get('cityId', '')
    login_teacher.city = request.COOKIES.get('city', '')
    login_teacher.branchSN = request.COOKIES.get('branchSN', '')
    login_teacher.branchType = request.COOKIES.get('branchType', '')
    login_teacher.cityHeadquarter = request.COOKIES.get('cityHeadquarter', '')
    login_teacher.cityHeadquarterName = request.COOKIES.get('cityHeadquarterName', '')
    login_teacher.isSuper = request.COOKIES.get('isSuper', '')

    login_teacher.showIncome = request.COOKIES.get('showIncome', '')

    login_teacher.cityFA = request.COOKIES.get('cityFA', '')
    login_teacher.cityFR = request.COOKIES.get('cityFR', '')
    login_teacher.cityRT = request.COOKIES.get('cityRT', '')
    login_teacher.cityRB = request.COOKIES.get('cityRB', '')
    login_teacher.cityRB2 = request.COOKIES.get('cityRB2', '')
    return login_teacher



# 顺时针旋转图片90度
def imageRotage(filename):

    img = Image.open(filename)
    img2 = img.rotate(-90,expand=True)
    img2.save(filename)


###########################
#
# 上传图片
#
###########################

def handle_uploaded_image(i,branch_oid,student_oid,type=None,maxlength=None,teacherId=None,contractId=None):
        filedate = getDateNow()
        tags = i.name.split('.')
        tag = ''
        for t in tags:
            tag = t
        tag = tag.lower()
        if tag != 'jpg' and tag != 'png' and tag != 'gif' and tag != 'jpeg':

            userImagePath = branch_oid+'/reimburse/'
            filename=userImagePath+student_oid+'_a.'+tag
            fs = FileSystemStorage()

            try:
                fs.save(filename, i)
            except Exception,e:
                print e
            return filename,filedate

        if not maxlength:
            maxlength = 640 #文件最大宽度默认640px

        # read image from InMemoryUploadedFile
        image_str = ""
        for c in i.chunks():
            image_str += c

        # create PIL Image instance
        imagefile  = StringIO.StringIO(image_str)
        image = None

        try:
            image = Image.open(imagefile)
        except Exception,e:
            print e
            return None,e

        info = None
        exif = {}
        try:
            image._getexif()

            for tag, value in info.items():
                decoded = TAGS.get(tag, tag)
                exif[decoded] = value
                if decoded == 'DateTime' or decoded == 'DateTimeOriginal':
                    fdate = exif[decoded]
                    filedate = datetime.datetime.strptime(fdate,"%Y:%m:%d %H:%M:%S")

        except Exception,e:
            err = 1
        x = image.size[0]
        y = image.size[1]
        img_ratio = float(x) / float(y)

        # if not RGB, convert
        if image.mode not in ("L", "RGB"):
            image = image.convert("RGB")

        #define file output dimensions (ex 60x60)
        if x>maxlength:
            x = maxlength
            y = x / img_ratio
        if y>maxlength:
            y = maxlength
            x = y * img_ratio
        #get orginal image ratio

        # resize but constrain proportions?
        if x==0.0:
            x = y * img_ratio
        elif y==0.0:
            y = x / img_ratio

        # output file ratio
        resize_ratio = float(x) / y
        x = int(x); y = int(y)

        # get output with and height to do the first crop
        if(img_ratio > resize_ratio):
            output_width = x * image.size[1] / y
            output_height = image.size[1]
            originX = image.size[0] / 2 - output_width / 2
            originY = 0
        else:
            output_width = image.size[0]
            output_height = y * image.size[0] / x
            originX = 0
            originY = image.size[1] / 2 - output_height / 2

        #crop
        cropBox = (originX, originY, originX + output_width, originY + output_height)
        image = image.crop(cropBox)

        # resize (doing a thumb)
        image.thumbnail([x, y], Image.ANTIALIAS)

        # re-initialize imageFile and set a hash (unique filename)
        imagefile = StringIO.StringIO()
        filename = i.name

        #save to disk
        userImagePath = None
        relaPath = None
        prePath = BASE_DIR+USER_IMAGE_DIR
        if type == constant.FileType.reimburseAttach: #报销附件
            relaPath = branch_oid+'/reimburse/'
            filename=student_oid+'_a.jpg'
        elif type == constant.FileType.reimburseProof:#报销票据凭证
            relaPath = branch_oid+'/reimburse/'
            filename=student_oid+'_p.jpg'
        elif type == constant.FileType.y19member:#元十九申请表
            relaPath = branch_oid+'/reimburse/'
            filename=contractId+'_y19m.jpg'
        elif type == constant.FileType.y19receipt:#元十九收据
            relaPath = branch_oid+'/reimburse/'
            filename=contractId+'_y19r.jpg'
        elif student_oid and type != '3': #学生照片
            relaPath = branch_oid+'/'+student_oid+'/'
        elif type == constant.FileType.teacherWXqrcode:
            relaPath = branch_oid+'/'
            filename=teacherId+'.jpg'
        else: #校区相册照片
            relaPath = branch_oid+'/'
            if type != '3': #校区照
                filename = "classroom.jpg"

        userImagePath = prePath + relaPath

        if not os.path.exists(userImagePath):
            os.makedirs(userImagePath)
        if type == '4':
            filename = 'refundApp.jpg'

        imagefile = open(os.path.join(userImagePath,filename), 'wb+')

        try:
            image.save(imagefile,'JPEG', quality=60)

            #backupFile(userImagePath,filename)
        except Exception,e:
            print e
            return None,e


        #=======================================================================
        # saveFileName = branch_oid+"/"
        # if student_oid:
        #     saveFileName = saveFileName + student_oid
        # saveFileName = saveFileName + "__"+filename
        #=======================================================================

        #=======================================================================
        #
        # try:
        #     p = subprocess.Popen(["scp",userImagePath+filename,"root@172.16.0.135:/data/backup/zhenpu_crm_pics/users/"+saveFileName],stdout=subprocess.PIPE)
        # except Exception,e:
        #     save_log("debug",str(e))
        #=======================================================================

        prod = False
        #for url in settings.ALLOWED_HOSTS:
        #if url == constant.SITE_PATCH:
        #        prod = True
        #        break
        p = None
        print 'is prod?-------------------------------'
        print prod
        if prod:
          try:

             remote = REMOTE_BK_DIR+userImagePath
             save_log("debug", userImagePath+filename)
             #remote = remote[0:len(remote)-1]
             if remote[len(remote)-1:len(remote)] != '/':
                 remote = remote + '/'
             save_log("debug", remote)
             print remote
             p = subprocess.Popen(['rsync','-ave','ssh',userImagePath+filename,remote],stdout=subprocess.PIPE)
          except Exception,e:
             print e
             save_log("debug",str(e))
        if p:
            output, err = p.communicate()
        return filename,filedate,relaPath


#savepath:/data/go2/go_static/users/5867c0c33010a51fa4f5abe6/
#[pid: 102750|app: 0|req: 14/14] 221.218.29.103 () {48 vars in 2157 bytes} [Mon Aug 27 06:50:26 2018] POST /web/uploadPic?type=3&student_oid=None => generated 0 bytes in 117 msecs (HTTP/1.1 302) 4 headers in 156 bytes (3 switches on core 0)
#rsync: mkdir "/data/go2/172.16.27.68/data/go2/go_static/users/5867c0c33010a51fa4f5abe6" failed: No such file or directory (2)
#rsync error: error in file IO (code 11) at main.c(674) [Receiver=3.1.1]


#backup image file to backup server(rang.jieli360.com)
def backupFile(path,filename):
    remote = None
    for h in ALLOWED_HOSTS:
        if constant.SITE_TEST in h:
            remote = None
        elif constant.SITE_PATCH in h:
            remote = '172.16.27.68'
        elif constant.SITE_GO2CRM in h:
            remote = '172.16.0.135'
        else:
            remote = None
    if remote:
        try:
            remote = remote+':'+path
            #save_log("debug", userImagePath+filename)
            #remote = remote[0:len(remote)-1]
            #print '[remote]'+remote
            #print '[path]'+path+filename

            save_log("debug", remote)

            p = subprocess.Popen(['rsync','-ave','ssh',path+filename,remote],stdout=subprocess.PIPE)
        except Exception,e:
            save_log("debug",str(e))

def makeQrcode(branchId,studentId,filename,qrtxt):
    import qrcode
    url = '/go_static/users/'
    userImagePath = BASE_DIR+USER_IMAGE_DIR
    if branchId:
        userImagePath = userImagePath+branchId+'/'
        url = url + branchId + '/'
    if studentId:
        userImagePath = userImagePath+studentId+'/'
        url = url + studentId + '/'

    url = url+filename
    #print url
    try:
        img = qrcode.make('http://go2crm.cn'+qrtxt)
        if not os.path.isdir(userImagePath):
            os.mkdir(userImagePath)

        imagefile = open(userImagePath+filename, 'wb+');
        img.save(imagefile,'JPEG')
        return url
    except Exception,e:
        print e
        return url




#===============================================================================
# 1、20周5800
# 2、40周9800
# 3、80周18600
# 4、120周274005
# 5、4周试学1000
# 6、1周暑期班1000
#===============================================================================

def getUserFromExcel(filepath,branch_oid):
  index = 0
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
        print e
        excel = xlrd.open_workbook(BASE_DIR+USER_IMAGE_DIR+filepath+"x")
    if constant.DEBUG:
        print '3'
    table = excel.sheet_by_name(u'学籍')
    nrows = table.nrows #行数
    ncols = table.ncols #列数
    class_col = 0
    name_col = 1
    gender_col = 2
    birthday_col= 3
    mobile_col = 4
    c_singDate = 10
    c_beginDate = 11
    c_multi = 12
    c_type = 13
    c_weeks = 14
    c_paid = 15
    c_status = 16
    row = table.row_values(0)
    if constant.DEBUG:
        print '4'
    for j in range(ncols-1):
        if str(row[j]).strip() == u'班级代码':
            class_col = j
        if row[j] == u'姓名':
            name_col = j
        if row[j] == u'性别':
            gender_col = j

        if row[j] == u'出生年月':
            birthday_col = j
        if row[j] == u'手机号码':
            mobile_col = j
        if row[j] == u'签约日期':
            c_singDate = j
        if row[j] == u'合同开始日期':
            c_beginDate = j
        if row[j] == u'是否续费合同':
            c_multi = j
        if row[j] == u'合同类型':
            c_type = j
        if row[j] == u'实际周数':
            c_weeks = j
        if row[j] == u'实付金额':
            c_paid = j
        if row[j] == u'合同状态':
            c_status = j

    dup = 0

    gcs = GradeClass.objects.filter(branch=branch_oid)
    for g in gcs:
        g.delete()
    for i in range(1,nrows):
        row = table.row_values(i)
        gc = GradeClass()
        gc.branch = branch
        gc.name=row[class_col]

        gc.gradeClass_type = 1
        if type(gc.name) == float:
            gc.name = str(int(gc.name))

        if gc.name:
            if len(gc.name)>0:
                gcs = GradeClass.objects.filter(branch=branch).filter(name=gc.name)
                if gcs and len(gcs)>0:
                    continue;
                else:
                    gc.save()

    lastClass = None
    noindex = 0
    lastName = 'name'
    cindex = 0
    for i in range(1,nrows):
        dup = 0
        row = table.row_values(i)
        student = Student()
        classname = row[class_col]
        if type(classname) == float:
            classname = str(int(classname))
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
        lastName = student.name

        mstr = cellToStr(row[mobile_col])


        if mstr and len(mstr)>6:
            student.prt1mobile = mstr
            students = Student.objects.filter(prt1mobile=student.prt1mobile)
            if students: #记录已存在
                if len(students) >= 1: #有重复记录
                    st = None
                    for s in students:

                        st = s
                        if str(st.branch.id) == branch_oid:#重复记录是本校区的
                            student = s
                            dup = 0
                            break
                        else:
                            student.dup = -1
                            student.resolved = -1
        else:
            dup = 1
        if gender_col>-1:
            student.gender = row[gender_col]
        if birthday_col > -1:
            birthday = cellToDate(row[birthday_col])
            student.birthday = birthday

        student.branch = branch
        student.branchName = branch.branchName

        con_status = cellToStr(row[c_status])

        contract_status = 0
        cstatus = 0
        try:
            contract_status = int(con_status)
        except:
            contract_status = 0
        if contract_status == 1:
            cstatus = 0
            student.status = 1
        elif contract_status == 2:
            cstatus = 2
            student.status = 3
        else:
            cstatus = 2
            student.status = 0

        #contract info
        singDate = cellToDate(row[c_singDate])

        paidStr = cellToStr(row[c_paid])
        paid = -1
        if paidStr:
            paid = int(paidStr)
        weeksStr = cellToStr(row[c_weeks])
        weeks = -1
        if weeksStr:
            weeks = int(weeksStr)

        if dup == 0:
          try:

            student.save()
            index = index +1
            if index == 1:
                print singDate
                print paid
                print weeks
                print cstatus

            if singDate and paid > -1 and weeks > -1 and cstatus == 0:
                print 'can add contract'
                beginDate = cellToDate(row[c_beginDate])
                multi = 1
                try:
                    multi = int(cellToStr(row[c_multi]))
                except:
                    multi = 1
                contractType = None
                try:
                    contractType = ccts[cellToStr(row[c_type])]
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
                for c in ccs:
                    c.delete()

                contract.save()

                csss = []
                csss.append(contract)
                student.contract = csss
                student.save()
                cindex = cindex + 1

            if student.status == 1:
              gcstudents = []
              try:
                gcs = GradeClass.objects.filter(name=classname).filter(branch=branch.id)
                gc = None
                if gcs and len(gcs)>0:
                    #print classname + '-' + student.name
                    gc = gcs[0]
                    gcstudents = gc.students
                    if gcstudents and len(gcstudents)>0:
                        okmsg = 1
                    else:
                        gcstudents = []
                    gcstudents.append(student)
                    gc.students = gcstudents

                    gc.save()
                    student.gradeClass = str(gc.id)
                    student.save()
              except Exception,e:
                print e
                gc=None
          except Exception,e:
              print e
        else:
            dup = 0
  print '[students]' + str(index)
  print '[contracts]' + str(cindex)
  return index

def getUserFromExcel2(filepath,branch_oid):
  index = 0
  if True:
    reload(sys)
    sys.setdefaultencoding('utf8')  # @UndefinedVariable
    branch = Branch.objects.get(id=branch_oid)# @UndefinedVariable
    print branch.branchCode
    excel = None
    try:
        excel = xlrd.open_workbook(BASE_DIR+USER_IMAGE_DIR+filepath)
    except:
        excel = xlrd.open_workbook(BASE_DIR+USER_IMAGE_DIR+filepath+"x")
    table = excel.sheet_by_name(u'学籍')
    nrows = table.nrows #行数
    ncols = table.ncols #列数

    name_col = 0
    gender_col = 1
    callInTime_col = 4

    branch_col = 6
    demo_col = 7
    source_col = 9
    proba_col = 10
    mobile_col = 12
    pr1 = 13
    mobile2_col = 14
    pr2 = 15
    birthday_col= 18
    school_col = 20
    regTeacher_col = 24
    co_teacher_col = 25
    memo1_col = 27
    memo2_col = 29
    remind_col = 30
    memo3_col = 32
    regTime_col = 33

    row = table.row_values(0)


    dup = 0


    noindex = 0
    lastName = 'name'
    for i in range(1,nrows):
        row = table.row_values(i)
        student = Student()

        student.name = cellToStr(row[name_col])
        if not student.name:
            if not lastName:
                noindex = noindex + 1
        else:
            noindex = 0
        if noindex > 2:
            break
        lastName = student.name


        mstr = cellToStr(row[mobile_col])

        if mstr and len(mstr)>6:
            student.prt1mobile = mstr
            students = Student.objects.filter(prt1mobile=student.prt1mobile)
            if students: #记录已存在
                if len(students) >= 1: #有重复记录
                    st = None
                    for s in students:

                        st = s
                        if str(st.branch.id) == branch_oid:#重复记录是本校区的
                            student = s
                            break
                        else:
                            student.dup = -1
                            student.resolved = -1
        else:
            dup = 1
        student.branch = branch
        student.branchName = branch.branchName
        if not student.gender:
            student.gender = cellToStr(row[gender_col])

        if dup == 0:
            student.save()
            index = index +1

  return index

def cellToStr(cell,debug=None):

    mstr = ''
    if type(cell) is float:
        if debug:
           print 'isFloat'
        mstr = repr(cell).split(".")[0]
    else:
        if debug:
            print 'isStr'
        mstr = str(cell)
    mstr = mstr.strip()

    return mstr

def cellToDate(cell,debug=None):
    res = None
    try:
        mstr = str(cell)
        #if type(cell) is float:
         #   mstr = repr(cell).split(".")[0]
        if debug:
            print '[date 0]'+str(mstr)
        if len(mstr.split('.'))<3:
            mstr = '2017.'+mstr
        if mstr[0:2] != '20':
            mstr = '20'+mstr
        if debug:
            print '[date 1]'+str(mstr)
        if mstr and len(mstr)>=8:
            mstr = mstr[0:len(mstr)]
            res = datetime.datetime.strptime(mstr,"%Y.%m.%d")
        if debug:
            print  '[date----end]'+str(res)
    except Exception,e:
        print e

    return res

def getMessage(login_teacher,isRead,isDone=None):
    messages = None
    if login_teacher:
        query = Q(toTeacher_oid=str(login_teacher))
        if isRead == 0 or isRead == 1:
            query = query&Q(isRead=isRead)
        messages = Message.objects.filter(query).order_by("-sendTime")  # @UndefinedVariable
    return messages

def sendMessage(fromBranch,from_teacher,from_teacher_name,to_teacher,txt,isDone,url):
    try:
        query = Q(message=txt)&Q(toTeacher_oid=to_teacher)
        m = Message.objects.filter(query)  # @UndefinedVariable
        if m and len(m) > 0:
            return
        message = Message()
        message.isRead = 0
        message.toTeacher_oid = to_teacher
        message.fromTeacher_oid = from_teacher
        message.fromTeacherName = from_teacher_name
        message.fromBranchName = fromBranch
        message.message = txt
        message.todoUrl = url
        message.sendTime = getDateNow(8)
        message.save()
        #print '[to teacher]'+str(message.toTeacher_oid)
    except Exception,e:
        #print to_teacher
        print e
    return

def addTrackToStudent(student):
    has = False
    try:
       query = Q(student=student.id)&Q(track_txt__ne=u'总部新推送')&Q(track_txt__ne=u'总部新分配')
       tracks = StudentTrack.objects.filter(query).order_by("-trackTime")
       if tracks and len(tracks)>0:
           student.track = "["+tracks[0].trackTime.strftime('%Y%m%d')+"]"+tracks[0].track_txt
           student.save()
           has = True
    except Exception,e:
        print student
    return has

def saveTrack(isAdd,student,trackId,trackTime,teacher_oid,track_txt,important=None):
    if isAdd:
        studentTrack = StudentTrack(student=student)
    else:
        studentTrack = StudentTrack.objects.get(id=trackId)
    if True:#try:
        studentTrack.recordTime = getDateNow()+datetime.timedelta(hours=8)
        if not trackTime:
            studentTrack.trackTime = studentTrack.recordTime
        else:
            studentTrack.trackTime = trackTime
        t = Teacher.objects.get(id=teacher_oid)# @UndefinedVariable
        studentTrack.teacher = t
        studentTrack.branch = str(t.branch.id)
        studentTrack.track_txt = track_txt
        if important:
            studentTrack.important = important
        studentTrack.save()
        #=======================================================================
        # 联络记录保存进学生信息
        #=======================================================================
        addTrackToStudent(student)
        return 0

def getNoClassStudent(branch):
    query = Q(branch=branch)&Q(gradeClass__ne=None)&Q(status=constant.StudentStatus.sign)
    students = Student.objects.filter(query)
    i = 0
    for s in students:

        if s.gradeClass:
            try:
                query = Q(id=s.gradeClass)&Q(gradeClass_type=1)&Q(deleted__ne=1)
                gc = GradeClass.objects.filter(query)
                if not gc or len(gc) < 1:
                    print 'has no gc:---' + str(s.id)
                    s.gradeClass = None
                    s.save()
                elif len(gc[0].students) > 0:
                    has = False
                    for gcss in gc[0].students:
                        if gcss.id == s.id:
                            print 'has this student-----------'
                            has = True
                            break
                #print gc.name
                    if not has:
                        print 'has no gc ---2 :---' + str(s.id)
                        i = i + 1
                        print i
                        s.gradeClass = None
                        s.save()
            except Exception,e:
                print e
                print
                s.gradeClass = None
                s.save()
        #print i
    noclassquery = Q(branch=branch)&(Q(gradeClass=None)|Q(gradeClass=''))&Q(status=constant.StudentStatus.sign)

    students = Student.objects.filter(noclassquery).order_by('name')

    return students

def getCheckins(studentId):
            lessonCheckin = 0
            mtime = int(round(time.time() * 1000))
            begin = mtime
            query = Q(student=str(studentId))&(Q(type=1)|Q(type=3))&Q(checked=True)&Q(value__ne=0)

            ls = Lesson.objects.filter(query)  # @UndefinedVariable

            if constant.DEBUG:
                        print '5'

            if ls and len(ls) > 0:
                if constant.DEBUG:
                        print '6'
                temp = []
                i = 0

                for l in ls:
                  i = i + 1
                  try:
                    mtime = int(round(time.time() * 1000))

                    gc = GradeClass.objects.get(id=l.gradeClass.id)
                    oriLesson = Lesson.objects.get(id=l.lessonId)  # @UndefinedVariable
                    if oriLesson and oriLesson.value and oriLesson.value != l.value:
                        l.value = oriLesson.value
                        l.save()
                        #print '[value wrong]'
                    if not l.value:
                        l.value = 1
                    if constant.DEBUG:
                        print '[lesson value]' + str(l.value)

                    lessonCheckin = float(lessonCheckin + l.value)
                    if constant.DEBUG:
                        print 'lessons after add one' + str(lessonCheckin)


                  except Exception,e:
                      print e
                      err = 1
            if constant.DEBUG:
                        print '[checkin lessons]' + str(lessonCheckin)

            return lessonCheckin

def getCheckins2(studentId,thisMonth,nextMonth):
            lessonCheckin = 0.0
            before = 0.0
            thisMonthCheckin = 0.0
            mtime = int(round(time.time() * 1000))
            begin = mtime
            query = Q(student=str(studentId))&(Q(type=1)|Q(type=3))&Q(checked=True)&Q(value__ne=0)

            ls = Lesson.objects.filter(query)  # @UndefinedVariable

            if constant.DEBUG:
                        print '5'

            if ls and len(ls) > 0:
                if constant.DEBUG:
                        print '6'
                temp = []
                i = 0

                for l in ls:
                  i = i + 1
                  try:
                    mtime = int(round(time.time() * 1000))

                    gc = GradeClass.objects.get(id=l.gradeClass.id)
                    oriLesson = Lesson.objects.get(id=l.lessonId)  # @UndefinedVariable
                    if oriLesson and oriLesson.value and oriLesson.value != l.value:
                        l.value = oriLesson.value
                        l.save()
                        #print '[value wrong]'
                    if not l.value:
                        l.value = 1
                    if constant.DEBUG:
                        print '[lesson value]' + str(l.value)

                    lessonCheckin = float(lessonCheckin + l.value)
                    if l.lessonTime < nextMonth and l.lessonTime >= thisMonth:
                        thisMonthCheckin = thisMonthCheckin + l.value
                    if l.lessonTime < thisMonth:
                        before = before + l.value
                    if constant.DEBUG:
                        print 'lessons after add one' + str(lessonCheckin)


                  except Exception,e:
                      print e
                      err = 1
            if constant.DEBUG:
                        print '[checkin lessons]' + str(lessonCheckin)

            return lessonCheckin,before,thisMonthCheckin


def getLessonLeft(student,thisMonth=None,nextMonth=None):
        thisMonthCheckin = 0
        if constant.DEBUG:
                        print '[in getLessonLeft]'
        before = 0.0
        thisMonthCheck = 0.0
        id = student.id
        sd = None #最近签约日期
        allLesson = 0 #全部合同周数
        lessonCheckin = 0 #本人签到数
        commonCheckin = 0 #共用合同者总计的签到数
        lessonLeft = 0
        query2 = None
        contracts = None #全部有效或已正常结束合同，不包括退费
        sibling = None
        searchId = None

        memberCT = None
        notMemberCT = None
        try:

            city = None
            try:
                city = City.objects.get(id=student.branch.city.id)  # @UndefinedVariable
                print city.cityName
            except:
                city = None
            ct = None
            try:
                query = Q(type=1)
                if city:
                    query = query&Q(city=city.id)
                cts = ContractType.objects.filter(query) # @UndefinedVariable
                ct = cts[0]
            except:
                ct = None

            query = Q(city=student.branch.city.id)&Q(type=constant.ContractType.memberFee)
            memberCTs = ContractType.objects.filter(query)# @UndefinedVariable

            memberCT = memberCTs[0]
            memberCT = Q(contractType=memberCTs[0].id)
            notMemberCT = Q(contractType__ne=memberCTs[0].id)
            i = 0
            for mct in memberCTs:
                if i > 0:
                    memberCT = memberCT|Q(contractType=mct.id)
                    notMemberCT = notMemberCT&Q(contractType__ne=mct.id)
                i = i + 1
        except Exception,e:
            print e
            memberCT = None



        query = Q(status__lt=2)&((notMemberCT)|(Q(multi=constant.MultiContract.memberLesson)&Q(paid__gt=0)))
        if ct:
            query = query&Q(contractType__ne=ct)
        if student.siblingId: #是附账户，找到主账户
            try:
               sibling = Student.objects.get(id=student.siblingId)
               searchId = student.siblingId

               #contracts = Contract.objects.filter(student_oid=student.siblingId).filter(status__lt=2)
            except:
                contracts = None
        else:
            searchId = str(id)
            #contracts = Contract.objects.filter(student_oid=str(id)).filter(status__lt=2)
        query = Q(student_oid=searchId)&query
        contracts = Contract.objects.filter(query)
        #print contracts._query
        if constant.DEBUG:
                        print '2'

        for c in contracts:
            if c.weeks:
                allLesson = allLesson + c.weeks
            elif c.contractType:
                allLesson = allLesson + c.contractType.duration
            if not sd:
                if c.status == 0:
                    sd = c.singDate
            if sd:
                if c.status == 0 and c.singDate > sd:
                    sd = c.singDate
        if constant.DEBUG:
                        print '3'

        if sibling:#本人附账户，查主账户及所有附账户签到
            commonCheckin = getCheckins(sibling.id)
            if sibling.lessons != commonCheckin:
                sibling.lessons = commonCheckin
                sibling.save() #保存主账户已签到课程

            query = Q(siblingId=student.siblingId)
            siblings = Student.objects.filter(query)
            for sib in siblings: #附账户
                sibLessons = getCheckins(sibling.id)
                if sib.lessons != sibLessons:
                    sib.lessons = sibLessons
                    sib.save()
                commonCheckin = commonCheckin + sib.lessons
                if sib.id == student.id: #本人的签到数
                    lessonCheckin = sib.lessons
            lessonLeft = allLesson - commonCheckin
            if sibling.lessonLeft !=lessonLeft or sibling.commonCheckin != commonCheckin:
                sibling.lessonLeft = lessonLeft
                sibling.commonCheckin = commonCheckin
                sibling.save()
            for sib in siblings:
                if sib.lessonLeft != lessonLeft or sib.commonCheckin != commonCheckin:
                    sib.lessonLeft = lessonLeft
                    sib.commonCheckin = commonCheckin
                    sib.save()

        elif student.siblingName or student.siblingName2 or student.siblingName3: #本人主账户，查所有附账户签到
            commonCheckin = getCheckins(student.id)
            if student.lessons != commonCheckin:
                student.lessons = commonCheckin
                student.save() #保存主账户已签到课程
            query = Q(siblingId=str(id))
            siblings = Student.objects.filter(query)
            for sib in siblings: #附账户
                sibLessons = getCheckins(sib.id)
                if sib.lessons != sibLessons:
                    sib.lessons = sibLessons
                    sib.save()
                commonCheckin = commonCheckin + sib.lessons

            lessonLeft = allLesson - commonCheckin
            if student.lessonLeft !=lessonLeft  or student.commonCheckin != commonCheckin:
                student.lessonLeft = lessonLeft
                student.commonCheckin = commonCheckin
                student.save()
            for sib in siblings:
                if sib.lessonLeft != lessonLeft or sib.commonCheckin != commonCheckin:
                    sib.lessonLeft = lessonLeft
                    sib.commonCheckin = commonCheckin
                    sib.save()

        else:

            if constant.DEBUG:
                        print '4'
            if thisMonth and nextMonth:
                lessonCheckin,before,thisMonthCheckin = getCheckins2(student.id,thisMonth,nextMonth)#
            else:
                lessonCheckin = getCheckins(student.id)
            lessonLeft = allLesson - lessonCheckin
            toSave = False
            if student.lessons != lessonCheckin:
                student.lessons = lessonCheckin
                toSave = True
            if student.lessonLeft != lessonLeft:
                student.lessonLeft = lessonLeft
                toSave = True
            if toSave:
                student.save()


        return allLesson,sd,lessonLeft#,before,thisMonthCheckin

def getCityBranch(cityId,all=None,delete=None):

    query = Q(city=cityId)&Q(type__ne=1)&Q(type__ne=2)&Q(type__ne=3)
    if all:
        query = Q(city=cityId)
    if not delete:
        query = query&Q(deleted__ne=True)
    elif delete == 1:
        query = query
    branches = Branch.objects.filter(query).order_by("sn")  # @UndefinedVariable
    return branches

def getTeacherClasses(teacherId):
    query = Q(teacher=teacherId)&Q(gradeClass_type=constant.GradeClassType.normal)&Q(deleted__ne=1)
    gradeClasses = GradeClass.objects.filter(query).order_by("start_date")
    return gradeClasses

def getBranches(login_teacher,all=None,type=None):
    branchs = None
    if all:
        branchs = Branch.objects.all().order_by("sn")  # @UndefinedVariable
    else:
        query = Q(deleted__ne=True)
        if login_teacher.username != 'admin':
            query = query&Q(city=login_teacher.cityId)
        if type != None:
            query = query&Q(type=type)
        branchs = Branch.objects.filter(query).order_by("sn")  # @UndefinedVariable
        print branchs._query
    #else:
     #   branchs = Branch.objects.all().order_by("sn")  # @UndefinedVariable
    return branchs

def isFinance(branchId):
    isFinance = False
    if branchId == constant.BJ_CAIWU:
        isFinance = True
    return isFinance

#return the begin day of last month
def subtract_one_month(dt0):
    dt1 = dt0.replace(day=1)
    dt2 = dt1 - datetime.timedelta(days=1)
    dt3 = dt2.replace(day=1)
    dt3 = dt3.replace(hour=0)
    dt3 = dt3.replace(minute=0)
    dt3 = dt3.replace(second=0)
    dt3 = dt3.replace(microsecond=0)
    return dt3

#return the last day of last month
def lastMonthLastDay(dt0):
    dt1 = dt0.replace(day=1)
    dt2 = dt1 - datetime.timedelta(days=1)
    dt3 = dt2.replace(hour=23)
    dt3 = dt3.replace(minute=59)
    dt3 = dt3.replace(second=59)
    dt3 = dt3.replace(microsecond=999999)
    return dt3

#return the last day of a given date's month
def monthLastDay(dt0):
    m = dt0.month+1
    y = dt0.year

    if m > 12:
        m = 1
        y = y + 1
    dt1 = dt0.replace(day=1)
    dt1 = dt1.replace(month=m)
    dt1 = dt1.replace(year=y)


    dt2 = dt1 - datetime.timedelta(days=1)
    dt3 = dt2.replace(hour=23)
    dt3 = dt3.replace(minute=59)
    dt3 = dt3.replace(second=59)
    dt3 = dt3.replace(microsecond=999999)

    return dt3

#return the begin and last day of a given date's 3month
def month3day(dt0):
    d1 = dt0
    d2 = dt0
    m1 = 0
    m2 = 0
    lastday = 0
    y1 = dt0.year
    y2 = dt0.year
    if dt0.month == 9 or dt0.month == 10 or dt0.month == 11:
        m1 = 9
        m2 = 11
        lastday = 30
    if dt0.month == 6 or dt0.month == 7 or dt0.month == 8:
        m1 = 6
        m2 = 8
        lastday = 31
    if dt0.month == 3 or dt0.month == 4 or dt0.month == 5:
        m1 = 3
        m2 = 5
        lastday = 31
    if dt0.month == 12 or dt0.month == 1 or dt0.month == 2:
        m1 = 12
        m2 = 2
        if dt0.month == 12:
            y2 = y1 + 1
        else:
            y1 = y1 - 1
        isLeap = False
        if y2%100 == 0:
           if y2%400 == 0:
               isLeap = True
        elif y2%4 == 0:
            isLeap = True
        if isLeap:
            lastday = 29
        else:
            lastday = 28

    d1 = d1.replace(day=1)
    d1 = d1.replace(month=m1)
    d1 = d1.replace(year=y1)
    d1 = d1.replace(hour=0)
    d1 = d1.replace(minute=0)
    d1 = d1.replace(second=0)
    d1 = d1.replace(microsecond=0)

    d2 = d2.replace(month=m2)
    d2 = d2.replace(year=y2)
    d2 = d2.replace(day=lastday)

    d2 = d2.replace(hour=23)
    d2 = d2.replace(minute=59)
    d2 = d2.replace(second=59)
    d2 = d2.replace(microsecond=999999)

    return d1,d2

def yearBeginEnd(now):
    d1 = getDateNow(8)
    d2 = d1
    if now:
        d1 = now
        d2 = now
    m1 = 0
    m2 = 0
    lastday = 0
    y1 = d1.year
    y2 = d1.year
    if d1.month == 9 or d1.month == 10 or d1.month == 11 or d1.month == 12:
        m1 = 9
        m2 = 8
        lastday = 31
        y2 = y2 + 1
    if d1.month >0 and d1.month < 9:
        m1 = 9
        m2 = 8
        lastday = 31
        y1 = y1 - 1
    d1 = d1.replace(year=y1)
    d1 = d1.replace(day=1)
    d1 = d1.replace(month=m1)

    d1 = d1.replace(hour=0)
    d1 = d1.replace(minute=0)
    d1 = d1.replace(second=0)
    d1 = d1.replace(microsecond=0)

    d2 = d2.replace(month=m2)
    d2 = d2.replace(year=y2)
    d2 = d2.replace(day=lastday)

    d2 = d2.replace(hour=23)
    d2 = d2.replace(minute=59)
    d2 = d2.replace(second=59)
    d2 = d2.replace(microsecond=999999)

    return d1,d2

def getThisMonthBegin(d):
    thisMonthBegin = d.replace(day=1)
    thisMonthBegin = thisMonthBegin.replace(hour=0)
    thisMonthBegin = thisMonthBegin.replace(minute=0)
    thisMonthBegin = thisMonthBegin.replace(second=0)
    thisMonthBegin = thisMonthBegin.replace(microsecond=0)
    return thisMonthBegin

def getDayBegin(d):
    d = d.replace(hour=0)
    d = d.replace(minute=0)
    d = d.replace(second=0)
    d = d.replace(microsecond=0)

    return d

def getY19qrcode(num):
    fpath = BASE_DIR+'/go_static/img/y19code/'
    import os
    from os import path
    i = 0
    for f in os.listdir(fpath):
        fname = str(f)

        qcode = fname[0:fname.find('.png')]
        if y19poster(qcode,num):
            i = i + 1
        print qcode
    print '[DONE]'+str(i)

def y19poster(qrcode,num):
  ok = False
  try:
    img1 = Image.open(BASE_DIR+'/go_static/img/y19poster'+num+'.jpg')
    img2 = Image.open(BASE_DIR+'/go_static/img/y19code/'+qrcode+'.png')
    img2 = img2.resize((1000,1000))
    if num == '2':
        img1.paste(img2,(300,5400))
    if num == '1':
        img1.paste(img2,(200,5000))
    if num == '4':
        img1.paste(img2,(900,5700))

    img1.save(BASE_DIR+'/go_static/img/poster'+num+'/'+qrcode+num+'.jpg')
    ok = True
  except:
      ok = False
      err  = 1
  return ok

#将某个日期时分秒置0
def onlyDate(date):
    date = date.replace(hour=0)
    date = date.replace(minute=0)
    date = date.replace(second=0)
    date = date.replace(microsecond=0)
    return date

#应上课程
def getWeekLesson(v,searchBegin,searchEnd,weekday):
    num = 0
    if v:
        if v.beginDate >= searchBegin and v.beginDate <= searchEnd:
            searchEnd = v.beginDate + datetime.timedelta(days=-1)
        if v.endDate >= searchBegin and v.endDate <= searchEnd:
            searchBegin = v.endDate + datetime.timedelta(days=1)

    sb = searchBegin.weekday() + 1
    if sb == weekday:

        date = searchBegin
    else:
        dif = 0
        if weekday > sb:
            dif = weekday - sb
        else:
            dif = weekday + 7 - sb
        date = searchBegin + datetime.timedelta(days=dif)
    if date < searchEnd:
        num = 1
    else:
        return 0,searchBegin,searchEnd
    while date < searchEnd:
        date = date + datetime.timedelta(days=7)

        if date < searchEnd:
            num = num + 1

    return num,searchBegin,searchEnd

#应上课程除去放假
def getWeekLessons(searchBegin,searchEnd,weekday,cityId):
    num = 0
    v = None
    query = Q(city=cityId)&((Q(beginDate__lte=searchEnd)&Q(beginDate__gte=searchBegin))|(Q(endDate__lte=searchEnd)&Q(endDate__gte=searchBegin)))
    vs = Vocation.objects.filter(query)  # @UndefinedVariable
    if len(vs) > 0:
        v = vs[0]


    num,begin,end = getWeekLesson(v,searchBegin,searchEnd,weekday)


    return num,begin,end

#应上课程除去休学
def getWeekLessonsExSus(v,searchBegin,searchEnd,weekday,cityId):
    n,begin,end = getWeekLessons(searchBegin,searchEnd,weekday,cityId)
    num = 0

    num,begin,end = getWeekLesson(v,begin,end,weekday)

    return num

def nextDueDate(dueDate):
        dueDate = dueDate + timedelta(days=91)
        return dueDate

if __name__ == "__main__":

    searchBegin = datetime.datetime.strptime("20181101","%Y%m%d")
    searchEnd = datetime.datetime.strptime("20181130","%Y%m%d")
    weekday = 6
    cityId = '5867c05d3010a51fa4f5abe5'
    month = int(searchBegin.strftime("%Y"))
    print month
