"""CollaborativeOptimization URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.9/topics/http/urls/
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
from django.conf.urls import url, include
from django.contrib import admin

from cosite import views as coviews

urlpatterns = [
    url(r'^$', coviews.index),
    url(r'^admin/', admin.site.urls),
    url(r'^co/', include('cosite.urls')),
    url(r'^api/v1/get-data/', coviews.api4get_data),
    url(r'^api/v1/get-exception/', coviews.api4get_exception),
    url(r'^api/v1/get-correlation/', coviews.api4get_correlation),
    # test
    url(r'^api/v1/test/', coviews.api4_test),
    url(r'^api/v1/test2/', coviews.api4_test2),

    # 前端发开始指令，生成uuid并返回
    url(r'^api/v1/vnf1-uuid/', coviews.api4_vnf1_uuid),
    url(r'^api/v1/vnf2-uuid/', coviews.api4_vnf2_uuid),
    url(r'^api/v1/vnf3-uuid/', coviews.api4_vnf3_uuid),

    # 前端发停止测试指令，返回current_state为false
    url(r'^api/v1/stop-task/', coviews.api4_stop_task),

    # 接收iTest的结果
    url(r'^api/v1/vnf1-itest/', coviews.api4_vnf1_itest),
    url(r'^api/v1/vnf2-itest/', coviews.api4_vnf2_itest),
    url(r'^api/v1/vnf3-itest/', coviews.api4_vnf3_itest),
    # 接收CPU MEMORY的结果

    # 接收log结果
    url(r'^api/v1/log/', coviews.api4_log),

    # 接收finalResult结果
    url(r'^api/v1/final-result/', coviews.api4_final_result),

    # ————————欣然接口————————

    # 刷新页面时的请求，返回当前state为true的测试用例id，若无则返回0
    # url(r'^api/v1/current-task-id/', coviews.api4_current_taskid),

    # 返回当前测试用例的具体信息，显示在前端
    # url(r'^api/v1/current-realtime/', coviews.api4_current_realtime),

    # 返回
    # url(r'^api/v1/task-config/', coviews.api4_task_config),

    # 返回
    # url(r'^api/v1/current-task-chart/', coviews.api4_current_task_chart),

    # 返回
    # url(r'^api/v1/task-list/', coviews.api4_task_list),
    # ————————欣然接口————————

    # index页面第一个图结果返回，CPU利用率、Memory利用率
    url(r'^api/v1/get-index-cpu/', coviews.api4_get_index_cpu),
    url(r'^api/v1/get-index-memory/', coviews.api4_get_index_memory),

    # index页面右侧的测试用例运行详情
    url(r'^api/v1/index-task-details', coviews.api4_index_task_details),

    # 判断是否存在正在运行的测试用例
    url(r'^api/v1/if-exist-current-task/', coviews.api4_if_exist_current_task),

    # 下拉菜单中展示所有的task列表
    url(r'^api/v1/history-task-list', coviews.api4_history_task_list),

    # 选择某一项task后，返回三个图表，即三个性能资源比
    url(r'^api/v1/query-task-cpu', coviews.api4_query_task_cpu),
    url(r'^api/v1/query-task-memory', coviews.api4_query_task_memory),
    url(r'^api/v1/query-task-stability', coviews.api4_query_task_stability),

    # 获取CPU和Memory的值，并存入
    url(r'^api/v1/index-get-cpu-memory', coviews.api4_save_cpu_memory),
]
