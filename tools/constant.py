#!/usr/bin/env python
# -*- coding:utf-8 -*-
from collections import OrderedDict
__author__ = 'patch'

DEBUG = False
TEST_USER_EXPIREDAY = 7
SITE_LOCAL = '127.0.0.1'
SITE_PATCH = 'rang.jieli360.com'
SITE_GO2CRM = 'yh.go2crm.cn'
SITE_TEST = 'test.go2crm.cn'

APPID = 'wx5a9fd47abffd57cc'
APP_SECRET = '8350dfed6f04b4c4e5924ca334200070'
TOKEN_URL = 'https://api.weixin.qq.com/cgi-bin/token?grant_type=client_credential&appid='+APPID+'&secret='+APP_SECRET
TICKET_URL = 'https://api.weixin.qq.com/cgi-bin/ticket/getticket?type=jsapi&access_token='
SIGN_CLASS_EXPIRE_DAY = 3#本月此日后不能修改上月签到，不能修改上月合同
#NET_BRANCH = '5867c26f0bb1e63b74d6cd62'#网络营销部
NET_BRANCH = '5a6299c297a75d4d8c66b531'#市场部
NET_BRANCH2= '5867c26f0bb1e63b74d6cd62'#第二市场部
BEIJING = '5867c05d3010a51fa4f5abe5'
SHANGHAI = '58bf7d9897a75d4e65592c9f'
BJ_CAIWU = '5ab86f5397a75d3c74041a69'
BJ_RENSHI = '5ab86f1f97a75d3c74041a68'

BJ_NETCT1 = '5e70bcede5c5e61faf03655b'
BJ_NETCT2 = '5e8a8896e5c5e6cf894c33e0'
# 学生状态：1签约，2退费，3结束,0-未签约,5-集训
LAST_CONTRACT_EXPIRE_DAY = 365 #上个合同结束多长时间以后，再签约算新招生

CONTRACT_DONE = 48#70 #续费成功周数
OLD_REDEAL_DONE = 40 #老生续费成功周数

RECEIPT_DEADLINE_NEW = 93
RECEIPT_DEADLINE_REDEAL = 123

END_DATE_EXTEND = 60 #合同结课日期向后推延的天数

ASSESS_CODE = OrderedDict([
    ('201808','201808-201809') #考评月，可以填写考评时间
])

REIMBURSE_TYPE = OrderedDict([
    ('A', u'办公费用'),
    ('C', u'办公日用品'),
    ('D', u'学生餐点'),
    ('E', u'水电费'),
    ('G', u'通讯及宽带'),
    ('H', u'网络服务(网站/邮箱/域名/公众号等)'),
    ('H2', u'电脑(主机、显示器)/笔记本电脑'),
    ('H3', u'一体机/触摸屏(教学用)'),
    ('I', u'玩具奖品'),
    ('K', u'活动经费'),
    ('M', u'交通费'),
    ('S', u'保洁费'),
    ('S2', u'旅游费'),
    ('T', u'招待费'),
    ('T2', u'差旅费'),
    ('U', u'广告费'),
    ('V', u'设备维护'),
    ('W', u'房租及物业'),
    ('X', u'宿舍费用'),
    ('Y1',u'社保费用'),
    ('Y9',u'手续费'),
    ('Z', u'其他')])

INCOME_TYPE = OrderedDict([
    ('D', u'零售'),
    ('F', u'星级考'),
    ('G', u'社会考级'),
    ('K', u'杂费')])

CONTRACT_STATUS = OrderedDict([
    ('0',u'正常'),
    ('-1',u'申请退费'),
    ('2',u'退费'),
    ('4',u'作废'),
    ])

PAY_METHOD = OrderedDict([
    ('A', u'支付宝/微信'),
    ('B', u'现金/转账'),
    ('C', u'刷卡')])

GO_LEVEL = OrderedDict([
    ('25K',1),
    ('24K',2),
    ('23K',3),
    ('22K',4),
    ('21K',5),
    ('20K',6),
    ('19K',7),
    ('18K',8),
    ('17K',9),
    ('16K',10),
    ('15K',11),
    ('14K',12),
    ('13K',13),
    ('12K',14),
    ('11K',15),
    ('10K',16),
    ('9K',17),
    ('8K',18),
    ('7K',19),
    ('6K',20),
    ('5K',21),
    ('4K',22),
    ('3K',23),
    ('2K',24),
    ('1K',25),
    ('1D',26),
    ('2D',27),
    ('3D',28),
    ('4D',29),
    ('5D',30),
    ('6D',31)
    ])

class IncomeType:
    sale = 'D'
    level = 'F'
    outLevel = 'G'
    other = 'K'

class BGCOLOR:
    GREEN = '#a5d2a6'
    YELLOW = '#dedc2c'
    RED = '#f5b4b5'
    GRAY = '#eeeeee'
    WHITE = '#ffffff'

class StudentSourceType:
    online = 'A'
    teacher = 'B'
    ref = 'C'
    walkin = 'D'
    marketing = 'E'

class StudentStatus:
    sign = 1  # 签约
    refund = 2  # 退费
    finish = 3  # 结业
    pending = 4  # 休学
    hc = 5  #假期班
    normal = 0


class StudentDemoStatus:
    testing = 1  # 已约试听
    finish = 2  # 试听完


# 班级，日程
class GradeClassType:
    normal = 1  # 普通班级课程
    demo = 2  # 试听课程
    missClass = 3  # 补课
    other = 9  # 其他日程

#合同状态：0：正常 ，1：结束，2：退费，3-休学,4-作废
class ContractStatus:
    sign = 0 #正常
    finish = 1 #结束
    refund = 2 #退费
    pending = 3 #休学
    delete = 4 #作废
    refundWaiting = -1

 # 合同类型0-常规 ，1-假期， 2-赠课
class ContractType:
    normal = 0 #常规班
    hc = 1  #假期班
    free = 2 #赠课
    memberFee= 3 #会员费
    onlineCourse = 4 #20200715--网课类型

class MultiContract:
    newDeal = 0   #新生
    newRedeal = 1 #新生续费
    oldRedeal = 2 #老生续费
    memberLesson = 3

class Role:
    teacher = 3
    staff = 4
    operator = 5
    master = 7
    financial = 8 #出纳
    admin = 9
    caiwu = 10 #一般财务

class HistoryType:
    lesson = 0 #上课
    rankChange = 1 #在线级别上升
    XingJiKao = 2 #星级考
    QiyuanJiwei = 3 #棋院证书
    onlineMatch = 4 #在线对局
    onlineDo = 5 #在线做题
    contribute = 6 #集体贡献

class FileType:#1-pic,2-video,3-branch
    studentPic = 1 #学生照片
    studentVedio = 2 #
    branchPic = 3 #校区
    refundApp = 4 #退费单照片
    contract = 5 #学籍照片
    reimburseAttach = 6 #报销单附件
    reimburseProof = 7 #报销凭证照片
    teacherWXqrcode = 8 #老师微信二维码

    y19member = 9
    y19receipt = 10

class RefundStatus:   #0-未审批，1-通过，2-驳回
    waiting = 0
    approved = 1
    reject = 2

class ReimburseStatus:
    saved = 0  #0-已保存，
    waitBranchApprove = 4 #已提交部门审批人
    waiting = 1 #1-已提交财务
    approved = 2 #2-财务已批准，
    reject = 3 #3-财务已驳回

class BranchType:
    school = 0
    marketing = 1
    function = 2
    management = 3

class StudentDupResolved: #冲突处理阶段
    waiting = -1 #未处理
    keepSide = -2 #单方处理：保留此条数据
    removeSide = -3 #单方处理：删除此条数据
    resolved = 0 #已处理

class MIAO_DI:
    account_sid = '3a2eb2bdb696480f925739c92a175b44'
    auth_token = '22163f0c4d204e868a9a80c49232329e'
    rest_url = 'https://api.miaodiyun.com'
    # 营销模版 sendSmsUrl = 'https://api.miaodiyun.com/20150822/affMarkSMS/sendSMS'
    sendSmsUrl = 'https://api.miaodiyun.com/20150822/industrySMS/sendSMS' #通知模版

class YUN_PIAN:
    apikey = 'efd29a3f520befad51e387db01c92d5f'
