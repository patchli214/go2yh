"""go2 URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.10/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.conf.urls import url, include
    2. Add a URL to urlpatterns:  url(r'^blog/', include('blog.urls'))
"""
from django.conf.urls import url
from django.contrib import admin
from regUser.views import student_list,dboard
from teacher.views import show_login ,logout, noright,questionnaire,api_questionnaire
from webpage.views import showPage,weixinTXT
from django.conf.urls import include
import settings
from django.conf.urls.static import static

urlpatterns = [
    url(r'^admin/', admin.site.urls),
    url(r'^$', dboard,name="dboard"),
    url(r'^MP_verify_khiOZqwCFngYL7Tg.txt$', weixinTXT,name="weixinTXT"),
    url(r'^go2/regUser/', include('regUser.urls', namespace="regUser")),
    url(r'^go2/branch/', include('branch.urls', namespace="branch")),
    url(r'^go2/contract/', include('contract.urls', namespace="contract")),
    url(r'^go2/teacher/', include('teacher.urls', namespace="teacher")),
    url(r'^go2/gradeClass/', include('gradeClass.urls', namespace="gradeClass")),
    url(r'^go2/statistic/', include('statistic.urls', namespace="statistic")),
    url(r'^go2/student/', include('student.urls', namespace="student")),
    url(r'^web/', include('webpage.urls', namespace="web")),
    url(r'^go2/workflow/', include('workflow.urls', namespace="workflow")),
    url(r'^go2/login/$', show_login,name="login"),
    url(r'^go2/logout/$', logout,name="logout"),
    url(r'^go2/noright/$', noright,name="noright"),
    url(r'^go2/q$', questionnaire,name="q"),
    url(r'^go2/api_questionnaire$', api_questionnaire,name="api_q"),
    url(r'^page/(?P<sn>[\w]{1,5})/$', showPage,name="showPage"),
    
]

urlpatterns += static(settings.MEDIA_URL , document_root = settings.MEDIA_ROOT )

