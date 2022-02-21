# -*- coding:utf-8 -*-
#from _ast import Dict
from teacher.models import Login_teacher
from webpage.models import WXToken
from tools import util3
__author__ = 'bee'

from mongoengine.queryset.visitor import Q
from django.http import HttpResponse
import json,ast,sys,os,time
import constant,utils
import urllib, urllib2,cookielib,logging
import datetime
from statistic.models import PageVisit,VisitIp
from utils import getDateNow,getTeachers
from student.models import User,History
from regUser.models import Student,Teacher
from branch.models import City, Branch
from go2 import settings
logger = logging.getLogger('utils')

ZHENPUWEIQI_URL = 'http://zhenpuweiqi.com'
ZENWEIQI_URL = 'http://www.zenweiqi.com/weiqinews'
LOG_PATH = '/data/go2/log/'
LOG_FILE = 'go2crm.log'
ERR_GO_FILE = 'ERR_getGoUser.log'
class JSONResponse(HttpResponse):
    def __init__(self, obj):
        if isinstance(obj, dict):
            _json_str = json.dumps(obj)
        else:
            _json_str = obj
        super(JSONResponse, self).__init__(_json_str, content_type="application/json;charset=utf-8")



def http_get(url):
    f = urllib.urlopen(url)
    s = f.read()
    return s


def http_post(url, _data=None):
    _data = urllib.urlencode(_data)
    req = urllib2.Request(url=url, data=_data)
    res_data = urllib2.urlopen(req)
    res = res_data.read()
    return res

def login_visit(login_url,visit_url,postdata):
    postdata = urllib.urlencode(postdata)
    cj=cookielib.CookieJar()
    opender=urllib2.build_opener(urllib2.HTTPCookieProcessor(cj))

    re=opender.open(login_url)
    res = re.read()
    re=opender.open(visit_url)
    res = re.read()
    return res

def getBranchStudentData(branchId,branchCodeLength):
    i = 0
    if not branchId:
        branchId = "5867c0c33010a51fa4f5abe6"
    branchName = ''
    
    if branchId:
        try:
            branch = Branch.objects.get(id=branchId)  # @UndefinedVariable
            branchName = branch.branchName
            
        except:
            branch = None
        teachers = getTeachers(branchId)   
        
        try:
          for teacher in teachers:
            
            try:
              if teacher.go_login and teacher.go_password:
                
                res = teacherlogin_zhenpuweiqi_com(teacher.go_login,teacher.go_password,branchId,teacher.id,branchCodeLength)

                if type(res) == int and res > 0:
                    i = i + res
            except Exception,e:
                print 'err 85'
        except Exception,e:
                print 'err 87'
    r = '0'
    if i > 0:
        r = str(i)
    try:    
        saveLog(LOG_FILE,'['+branch.city.cityName.encode('utf-8')+'-'+branchName.encode('utf-8')+'],'+r)
    except:
        print 'err save log 94'
    return i

def checkNameWithBranch(branchId,username,branchCodeLength):
    searchname = ''
    if str(branchId) == "58bffe2c97a75d6de3380be3":#重庆－财富中心  cf    
            searchname = username[2:len(username)]
    elif str(branchId) == "58e5f16497a75d08b67ad55d":#重庆－西城天街  xc    
            searchname = username[2:len(username)]
    elif str(branchId) == "58e5f18597a75d08b67ad565":#重庆－时代天街   sd   
            searchname = username[2:len(username)]
    elif str(branchId) == "5929442597a75d0eb14f8860":#重庆－上海城 shc      
            searchname = username[3:len(username)]
    elif str(branchId) == "595f2cc797a75d64ad6f8bcc": #重庆－U城  uc  
            searchname = username[2:len(username)]
    elif str(branchId) == "59c7541297a75d102914c917":#南京－万达  wd    
            searchname = username[2:len(username)]
    elif str(branchId) == '58beeaf597a75d4cb2744e71': #富力城
        if username[0:2] == u'富富':
            searchname = username[2:len(username)]
        elif username[0:1] == u'富':
            searchname = username[1:len(username)]
        elif username[0:2].upper() == 'FL':
            searchname = username[2:len(username)]
        else:
            searchname = username
    elif str(branchId) == '58bef43f97a75d4e65592abb': #中观村
        if username[0:3] == u'中关村':
            searchname = username[3:len(username)]
        elif username[0:3].upper() == 'ZGC':
            searchname = username[3:len(username)]
    elif str(branchId) == '58be210b97a75d14f33cfc1e': #公主坟
        if username[0:3] == u'公主坟':
            searchname = username[3:len(username)]
        elif username[0:2].upper() == 'GZ':
            searchname = username[2:len(username)]        
    
    elif str(branchId) == '58dcb1c797a75d734389eb7f': #亚运村
        if username[0:3].upper() == 'YYC':
            searchname = username[3:len(username)]
        elif username[0:2].upper() == 'YY':
            searchname = username[2:len(username)]
        else:
            searchname = username
    elif str(branchId) == '58bef4da97a75d4e65592abd': #西局
        if username[0:1].upper() == 'S':
            searchname = username[1:len(username)]
        elif username[0:2].upper() == 'FT':
            searchname = username[2:len(username)]
        else:
            searchname = username
    elif str(branchId) == '58c1343b97a75d4702a2d5e1': #方庄
        if username[len(username)-2:len(username)] == u'方庄':
            searchname = username[0:len(username)-2]
        elif username[0:2].upper() == 'FZ':
            searchname = username[2:len(username)]
        elif username[0:2].upper() == u'方庄':
            searchname = username[2:len(username)]    
        else:
            searchname = username
    
    elif str(branchId) == '58c25e9997a75d495208acbd': #望京
        if username[0:1] == u'望':
            searchname = username[1:len(username)]
        elif username[0:2].upper() == 'WJ':
            searchname = username[2:len(username)]
        elif username[0:1].upper() == 'W':
            searchname = username[1:len(username)]
        else:
            searchname = username
    elif str(branchId) == '59f6e25497a75d0d7fda120d': #上海七宝
        if username[0:2].upper() == u'七宝':
            searchname = username[2:len(username)]
        elif username[0:2].upper() == 'QB':
            searchname = username[2:len(username)]
        else:
            searchname = username
    else:
        searchname = username[branchCodeLength:len(username)]

    return searchname

def teacherlogin_zhenpuweiqi_com(login_name,password,branchId,teacherId,branchCodeLength=2):
    
    query = Q(branch=branchId)&Q(status=1)&Q(teacher=teacherId)
    students = None#Student.objects.filter(query)  # @UndefinedVariable
    thisbranch = Branch.objects.get(id=branchId)  # @UndefinedVariable
    thisteacher = Teacher.objects.get(id=teacherId)  # @UndefinedVariable
    url = ZHENPUWEIQI_URL
    login_url = url+'/admin/teacher/teacher_login?login_name='+login_name+'&password='+password
    login_url = login_url.encode(encoding='UTF-8')
    cj=cookielib.CookieJar()
    opender=urllib2.build_opener(urllib2.HTTPCookieProcessor(cj))
    re=None
    res = None
    r = None
    
    try:
        re = opender.open(login_url)
        res = re.read()
        r = eval(res)
    except Exception,e:
        print 'err 186'
        try:
            saveLog(ERR_GO_FILE,thisbranch.branchCode+','+str(thisteacher.name)+',login fail')
        except:
            print 'err save log 193'
        #=======================================================================
        # file_object = open(ERR_GO_FILE, 'a')
        # time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        # file_object.seek(0, 2)
        # file_object.write(time+','+thisbranch.branchCode+','+str(thisteacher.id)+',login fail\n')
        # file_object.close( )
        #=======================================================================
        return
    
    

    if r['code'] != 200: #login err
        
        logInfo = thisbranch.branchName+','+thisteacher.name+',login fail'
        try:
            saveLog(ERR_GO_FILE,logInfo)
        except:
            print 'err save log 205'
        #=======================================================================
        # file_object = open(ERR_GO_FILE, 'a')
        # time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        # file_object.seek(0, 2)
        # file_object.write(time+','+thisbranch.branchName+','+str(thisteacher.name)+',login fail\n')
        # file_object.close( )
        #=======================================================================
        if constant.DEBUG:
            print 'login err' 
        return 'err'
    classes_url = url+'/admin/class_rooms'
    re=opender.open(classes_url)
    res = re.read()
    spage = None
    cindex = 0
    sindex = 0
    
    while True:
        
        begin = res.find('javascript:changeClassroomName(')
        if constant.DEBUG:
            print 'changeClassroomName---'+str(begin)
        if begin > -1:
            res = res[begin+31:len(res)]
            
            end = res.find(',')
            classId = None
            if end>=0:
                classId = res[0:end]
            class_url = url+'/admin/class_rooms/'+classId+'?type='
            urlmess = u'统计'
            urlmess2 = urllib.quote(urlmess.encode('utf8'), ':/')
            class_url = class_url + urlmess2
            re=opender.open(class_url)
            page = re.read()
            cindex = cindex + 1
            studentSids = []
            while True:
                
                begin = page.find('{id')
                if constant.DEBUG:
                    print '{id---|'+str(begin)

                if begin > -1:

                    page = page[begin+4:len(page)]
                    end = page.find(',')

                    if constant.DEBUG:
                        print 'end---'+str(end)
                    if end>=0:
                        
                        sid = page[0:end]
                        intSid = 0
                        try:
                            intSid = int(sid)
                        except:
                            intSid = 0
                        
                        if constant.DEBUG:
                            print 'sid---'+sid
                        if intSid == 0:
                            continue
                        if intSid in studentSids:
                            continue
                        else:
                            studentSids.append(intSid)
                        user_url = url+'/admin/class_rooms/turn_to_student_account?id='+str(intSid)
                        
                        
                        re=opender.open(user_url)
                        spage = re.read()
                        sindex = sindex + 1
                        user = getUser(User(),spage)

                        if user:

                            a = 1#print user.name
                        else:
                            print '[get user wrong]'

                        u = None
                        try:
                            u = User.objects.get(name=user.name)  # @UndefinedVariable
                        except:
                            u = None


                        if u:

                            user.id=u.id

                            if user.rank - u.rank != 0.0:
                                h = History(user=u)
                                h.type = 1
                                h.memo = str(user.rank-u.rank)
                                h.date = getDateNow()
                                h.save()
                            if user.yesterday_total_question_count > 0:
                                hdate = getDateNow()-datetime.timedelta(days=1)
                                hdate = datetime.datetime.strptime(hdate.strftime("%Y-%m-%d")+' 00:00:00',"%Y-%m-%d %H:%M:%S")
                                
                                query = Q(user=u.id)&Q(date=hdate)&Q(type=5)
                                try:
                                    h = History.objects.get(query)  # @UndefinedVariable
                                except:
                                    h = History(user=u.id)
                                    h.date = hdate
                                    h.type = 5
                                h.memo = str(user.yesterday_total_question_count)
                                if user.yesterday_correct_question_count > 0:
                                    h.memo = h.memo + '|' + str(user.yesterday_correct_question_count)
                                h.save()

                        user.goid = sid
                        student = None
                        searchname = ''
                        try:
                        
                            searchname = checkNameWithBranch(branchId,user.name,branchCodeLength)
                        
                            #searchname = user.name[branchCodeLength:len(user.name)] 
                            query = Q(name__icontains=searchname)&Q(branch=branchId)
                            students = Student.objects.filter(query)  # @UndefinedVariable
                            if constant.DEBUG:
                                print students._query
                            if constant.DEBUG:
                                print '[searchname]'+searchname+'[got]'+str(len(students))
                            if students and len(students) > 0:
                                student = students[0]
                            else:
                                searchname = user.name 
                                query = Q(name__icontains=searchname)&Q(branch=branchId)
                                
                                students = Student.objects.filter(query)  # @UndefinedVariable
                                print students._query
                                if students and len(students) > 0:
                                    student = students[0]
                                else:
                                    print 'err 346'
                                    #saveLog(ERR_GO_FILE,thisbranch.branchName+','+thisteacher.name+','+searchname)
                                    #===========================================
                                    # file_object = open(ERR_GO_FILE, 'a')
                                    # time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                                    # file_object.seek(0, 2)
                                    # file_object.write(time+','+thisbranch.branchName+','+thisteacher.name+','+searchname+'\n')
                                    # file_object.close( )
                                    #===========================================
                            user.student = student
                        except Exception,e:
                            print 'err 357'
                            student = None
                        user.save()
                        
                        match_url = url+'/question_bank_of_go/my_matches'
                        re=opender.open(match_url)
                        mpage = re.read()
                        getMatches(user,mpage)
                else:
                    break
        else:
            break
        

    try:
        r = '0'
        if sindex > 0:
            r = str(sindex)
        saveLog(LOG_FILE,'[' + thisbranch.branchName + '-' + thisteacher.name+'],'+r)
    except:
        print '[save log err]377'

    return sindex

def getUser(s,p): #s is User
    if constant.DEBUG:
                    print 'into getUser function---'
    begin = p.find('var currentUser = {')
    if constant.DEBUG:
                    print 'getUser-begin--'+str(begin)
    user = {}
    if begin>=0:
        begin = begin+18
        end = p.find('K"};')
        end = end + 3
        if end > 0 and end > begin:
            userstr = p[begin:end]
            user = json.loads(userstr)
    try:
        rank = user['rank']
        end = rank.find('K')
        cd = user['created_at']
        cd = cd[0:10]
        rank = rank[0:end]
        s.created_at = datetime.datetime.strptime(cd,"%Y-%m-%d")
    except:
        err = 1
    
        
    try:
        s.rank = float(rank)
    except:
        s.rank = 30
    try:
        s.name = user['name']
        s.nickname = user['nickname']
        s.goid = user['id']
    except:
        err = 1
    try:
        s.diamonds = int(user['diamonds'])
    except:
        s.diamonds = 0
    try:
        s.coins = int(user['coins'])
    except:
        s.coins = 0
    
    try:
        s.history_total_question_count = int(user['history_total_question_count'])
    except:
        s.history_total_question_count = 0
    try:
        s.history_total_match_count = int(user['history_total_match_count'])
    except:
        s.history_total_match_count = 0
    try:
        s.last_one_week_total_question_count = int(user['last_one_week_total_question_count'])    
    except:
        s.last_one_week_total_question_count = 0
    try:
        s.last_one_week_total_match_count = int(user['last_one_week_total_match_count'])
    except:
        s.last_one_week_total_match_count = 0
    try:
        s.week_tatal_question_count = int(user['week_correct_question_count'])
    except:
        s.week_total_question_count = 0
    try:
        s.week_total_match_count = int(user['week_total_match_count'])
    except:
        s.week_total_match_count = 0
    try:
        s.yesterday_total_question_count = int(user['yesterday_total_question_count'])
    except:
        try:
            s.yesterday_total_question_count = int(user['yesterday_total_question_count'])
        except:
            err = 1
    try:
        s.yesterday_correct_match_count = int(user['yesterday_correct_match_count'])
    except:
        try:
            s.yesterday_correct_match_count = int(user['yesterday_correct_match_count'])
        except:
            err = 1
    return s

def getMatches(user,page):
    reload(sys)
    sys.setdefaultencoding('utf8')  # @UndefinedVariable

    page = page.replace(' ','')
    begin = 0
    if True:
        query = Q(user=user.id)&Q(type=4)
        h = None
        oldDate = None
        try:
            h = History.objects.filter(query).order_by("-date")[0]  # @UndefinedVariable
            
        except:
            err = 1
        if h and h.date:
            oldDate = h.date
        if oldDate == None:
            oldDate = datetime.datetime.strptime('1900-12-25','%Y-%m-%d')
        lastDate = None
        sum = 0
        wins = 0
        i = 0
        while begin >= 0:
            
            i = i + 1 
            begin = page.find('<pstyle="width:100%;height:30px;margin:0000;text-align:center">')
            page = page[begin+63:len(page)]
            THIS = page[0:page.find('<pstyle="width:100%;height:30px;margin:0000;text-align:center">')]
            end = page.find('</p>')
            datebegin = page.find('201')
            if datebegin < 0:
                break
            p = page[datebegin:end]
            res = THIS.find('-c5ece4666c67a760db460f7c6307c7587b79862168757f453aacbc43dcc371ff.png')
            win = -1
            if res > -1:
                win = 1
            else:
                res = THIS.find('-56e0e6a281c8d6c1b790136d87925b35538eae545acf2467651d30bcb5cab167.png')
                if res > -1:
                    win = 0
                        
            try:
                date = datetime.datetime.strptime(p,'%Y-%m-%d')
            except:
                break
            if date and date > oldDate:
                if lastDate != date:
                    if lastDate != None:
                        history = History(user=user)
                        history.type = 4
                        history.date = lastDate
                        history.memo = str(sum)+'|'+str(wins)
                        history.save()
                        sum = 0
                        wins = 0 
                    lastDate = date 
                sum = sum + 1
                if win == 1:
                     wins = wins + 1
                win = -1
                #print date.strftime('%Y%m%d')+'['+str(sum)+']'+str(wins)
            else:
                break

        if sum > 0:
            history = History(user=user)
            history.type = 4
            history.date = lastDate
            history.memo = str(sum)+'|'+str(wins)
            history.save()    
       
                
        

def getVisitIp(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip

#save page view to db
def pageVisit(branch,student,teacher,page,ip,webpage = None):
    pageId = student
    if webpage and webpage.sn:
        pageId = str(webpage.sn)
    if not ipValid(ip,page,pageId):
        return
    pageVisit = None
    try:
        pageVisit = PageVisit.objects.filter(page=page).filter(student=student).order_by("-visitTime")[0]  # @UndefinedVariable
    except:
        pageVisit = PageVisit()
    visitTime = pageVisit.visitTime
    newDay = False
    if visitTime:
        if visitTime.date() < datetime.datetime.today().date():
            newDay = True
    else:
        pageVisit.visitTime = getDateNow()
    if newDay:
        pageVisit = PageVisit()
        pageVisit.visitTime = getDateNow()
    

    pageVisit.branch = branch
    pageVisit.student = pageId
    if teacher:
        pageVisit.teacher = teacher
    pageVisit.page = page
    visit = pageVisit.visit 
    if visit:
        pageVisit.visit = visit + 1
    else:
        pageVisit.visit = 1
    pageVisit.save()
    return

def ipValid(ip,page,student):
    
    visitIps = None
    visitIp = None
    if student:
        visitPage = page+'-'+student
    else:
        visitPage = page
    try:
    
        visitIps = VisitIp.objects.filter(visitIp=ip).filter(visitPage=visitPage)  # @UndefinedVariable
    except:
    
        visitIps = None
    
    if visitIps and len(visitIps)>0:
    
        visitIp = visitIps[0]
    
        if visitIp.visitDate and visitIp.visitDate.date() >= datetime.datetime.today().date(): 
            return False
        else:
            visitIp.visitDate = getDateNow()
    else:
    
        visitIp = VisitIp()
        visitIp.visitIp = ip
        visitIp.visitPage = visitPage
        visitIp.visitDate = getDateNow()
    
    visitIp.save()
    
    return True

def getAllDataFromGo(cityId):
    i = 0
    if not cityId:
        cityId = constant.BEIJING  # @UndefinedVariable
    cityName = ''
    try:
        cityName = City.objects.get(id=cityId).cityName  # @UndefinedVariable
    except:
        cityName = ''
    branches = utils.getCityBranch(cityId)  # @UndefinedVariable
    for branch in branches:
        #print branch.branchCode
        branchCodeLength = len(branch.branchCode)
        #print branchCodeLength
        res = getBranchStudentData(branch.id,branchCodeLength)
        if res and res > 0:
            i = i + res
        print '[branch done]'
    print '[CITY DONE]'
    try:
        r = '0'
        if i > 0:
            r = str(i)
        saveLog(LOG_FILE,u'['+cityName+'TOTAL],'+r)
    except:
        print '[save log err]645'
    return i

def getAllCityDateFromGo():
    i = 0
    logger.debug('[getGoUsers]')
    cities = City.objects.all()  # @UndefinedVariable
    for city in cities:
        #print 'city['+str(city.sn)+']'
        res = getAllDataFromGo(city.id)
        if res and res > 0:
            i = i + res
    print '[ALL DONE]'
    return i
    
def getZenweiiNews():
    url = ZENWEIQI_URL
    cj=cookielib.CookieJar()
    opender=urllib2.build_opener(urllib2.HTTPCookieProcessor(cj))
    re=opender.open(url)
    res = re.read()
    


def getAccessToken():
    accessToken = read('accessToken')
    if not accessToken:
        res = http_get(constant.TOKEN_URL)
        r = eval(res)
        accessToken = r['access_token']
        save('accessToken',accessToken)
    return accessToken
    
def getJsapiTicket(accessToken):
    ticket = read('jsapiTicket')
    if not ticket:
        res = http_get(constant.TICKET_URL+accessToken)
        r = eval(res)
        ticket= r['ticket']
        save('jsapiTicket',ticket)
    return ticket

def saveLog(filename,value):
    file_object = open(LOG_PATH+filename, 'a')
    time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    file_object.seek(0, 2)
    file_object.write(time+','+value+'\n')
    file_object.close( )

def save(name,value):
    timeStr = str(int(time.time()))
    txt = '{"'+name+'":"'+value+'","expireTime":'+timeStr+'}'
    dir = os.path.join(settings.BASE_DIR, 'log')
    filename = name
    if not '.' in filename:
        filename = name + '.txt' 
    file = os.path.join(dir, filename)
    file_w = open(file, "w")
    file_w.write(txt)
    file_w.close()
 
def read(name):
    dir = os.path.join(settings.BASE_DIR, 'log')
    file = os.path.join(dir, name+".txt")
    file_r = open(file,"r") 
    res = file_r.read()
    diff = 0
    try:
        r = eval(res)
        diff = int(time.time())-r['expireTime']

        if diff < 7000 and r[name] and len(str(r[name])) > 0:
            return str(r[name])
        else: 
            return None
    except:
        return None    
         
def getAndLog():
    print '[begin]'
    r = '0'
    res = getAllCityDateFromGo()
    if res and res > 0:
        r = str(res)
    try:
        saveLog(LOG_FILE,u'[TOTAL GOT]'+r)
    except:
        print 'err save log 732'
    print '[END]'
    
def testMessage(url=None):
    keyword3 = '1212432332'
    openId = 'oRcnlt2T_M0N8ohsHTcoAPiQCtO0'
    fromurl = 'zenweiqi.com'
    first = u'上海首页'
    if first.find(u'上海') > -1:
                fromurl = 'shanghai'
    if not url:
        url = u'www.go2crm.cn'
    dburl = u'http://'+url+u'/go2/teacher/api_sendMessage?to='+openId+u'&mess=' + keyword3 + u'&from=' + fromurl
    req = urllib.urlopen(dburl)
    rest = req.read()


def getJieli360WXToken():
    VALID_TIME = 7000#微信token有效期，目前是7200秒，为了避免超时，此处规定为7000
    res = {}
    print 'getWXToken'
    token = None
    validTime = utils.getDateNow(8) - datetime.timedelta(seconds=VALID_TIME)
    query = Q(tokenTime__gt=validTime)
    tokens = WXToken.objects.filter(query)  # @UndefinedVariable
    if tokens and len(tokens) > 0:
        token = tokens[0].token
        res = {'access_token':token}
        print 'get Old Token:' + token
    else:
        APPID = "wx5a9fd47abffd57cc";
        APPSECRET = "8350dfed6f04b4c4e5924ca334200070"; #weixin@jieli360.com/jieli1234
        url = 'https://api.weixin.qq.com/cgi-bin/token?grant_type=client_credential&appid='+APPID+'&secret='+APPSECRET
        ret = http_get(url)
        res = json.loads(ret)
        print res
        token = res['access_token']
        t = WXToken()
        t.token = token
        t.tokenTime = utils.getDateNow(8)
        t.save()
    
    return res

def sendMail(receivers,subject,text,fromBox):
    import smtplib
    from email.mime.text import MIMEText
    host = 'smtp.exmail.qq.com'
    port = 465
    user = 'patch@jieli360.com'
    password = 'hateyou008'
    sender = 'patch@jieli360.com'
    #receivers = ['patch@jieli360.com']
    print '1'
    #text = u'test 内容'
    message = MIMEText(text, "plain", 'utf-8')
    message['Subject'] = subject
    message['From'] = fromBox + '@jieli360.com'
    message['To'] = 'you@jieli360.com'
   
    try:
        print '2'
        smtpObj = smtplib.SMTP_SSL()
        print '3'
        smtpObj.connect(host, port)
        print '3.1'
        #smtpObj.ehlo()
        #smtpObj.starttls()
        smtpObj.login(user,password)
        print '4'  
        smtpObj.sendmail(sender, receivers, message.as_string())         
        print "Successfully sent email"
    except Exception,e:
        print e
        print "Error:"
    return

def statRegEveryday():
    now = utils.getDateNow(8)
    print now
    weekBegin = utils.getWeekBegin(now, False)
    weekEnd = weekBegin + datetime.timedelta(days=7)
    print weekBegin
    print weekEnd
    util3.statWeekReg(constant.BEIJING,weekBegin,weekEnd)
    print '[DONE WEEK]'
    monthBegin = utils.getThisMonthBegin(now)
    monthEnd = monthBegin + datetime.timedelta(days=32)
    monthEnd = utils.getThisMonthBegin(monthEnd)
    print monthBegin
    print monthEnd
    util3.statWeekReg(constant.BEIJING,monthBegin,monthEnd)
    print '[DONE MONTH]'
      
if __name__ == "__main__":
    statRegEveryday()

    #getAndLog() #DO THIS!!!
    #1550736302.36
    #1550736323.38
    #===========================================================================
    # token测试
    #===========================================================================
    #save('accessToken','444')
    #token = getAccessToken()
    #ticket = getJsapiTicket(token)
    #testMessage('127.0.0.1:8000')

    #===========================================================================
    # 某老师导入测试
    #===========================================================================
    #teacher = Teacher.objects.get(username='niujiangang')  # @UndefinedVariable
    #teacherlogin_zhenpuweiqi_com(teacher.go_login,teacher.go_password,teacher.branch.id,teacher.id,2)
    
    #===========================================================================
    # 某城市导入测试
    #===========================================================================
    #checkNameWithBranch("58bffe2c97a75d6de3380be3",u"财富杨谨萌",2)
    #getAllDataFromGo("58bffdf297a75d6de3380be2") #重庆
    #getAllDataFromGo(constant.BEIJING)
    
    #某校区导入测试
        
        #=======================================================================
        # branch = Branch.objects.get(branchCode='sh_qb')  # @UndefinedVariable
        # print branch.branchCode
        # branchCodeLength = len(branch.branchCode)
        # getBranchStudentData(branch.id,branchCodeLength)
        # print '[branch done]'
        #=======================================================================
