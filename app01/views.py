from django.shortcuts import render
from django.shortcuts import HttpResponse,redirect
from django.urls import reverse

def login(request):
    url1 = reverse('rbac:xxx:n1')
    url2 = reverse('rbac:xxx:n2')

    print(url1)
    print(url2)
    return HttpResponse('login')

def logout(request):
    return HttpResponse('logout')

def add(request):
    return HttpResponse('add')

def change(request):
    return HttpResponse('change')


# 测试函数1
def test1(request):
    from app01 import models

    list_display = ['id','title']

    # head_list内容
    # ['ID', '名称啊']
    # [1, 'roan']
    # [2, 'bob']
    # [3, 'alex']
    # [4, 'wusir']

    header_list = []
    for name in list_display:
        header_list.append(models.UserInfo._meta.get_field(name).verbose_name)

    user_queryset = models.UserInfo.objects.all()

    for item in user_queryset:
        row = []    # 行内容
        for field in list_display:
            row.append(getattr(item,field))
        print(row)
    return HttpResponse('...')


import copy
def test2(request):
    from django.http.request import QueryDict
    url_params_str = request.GET.urlencode() # _filter = k1=v1&k2=v2&k2=v3

    query_dict = QueryDict(mutable=True)
    query_dict['_filter'] = url_params_str

    new_params = query_dict.urlencode()

    target_url = "/add_stu/?%s" %new_params
    return redirect(target_url)


def add_stu(request):

    if request.method == "GET":
        return render(request,'add_stu.html')
    # 接收到数据，保存到数据库
    origin_params = request.GET.get('_filter')
    back_url = "/test/?%s" % origin_params
    return redirect(back_url)





















