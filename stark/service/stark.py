import functools
from django.conf.urls import url
from django.shortcuts import HttpResponse, render, redirect
from django.utils.safestring import mark_safe
from django.urls import reverse
from django import forms
from django.db.models import Q
from django.http import QueryDict
from django.db.models.fields.related import ForeignKey, ManyToManyField, OneToOneField


class Row(object):
	def __init__(self, data_list, option, query_dict):
		"""
		元组
		:param data_list:元组或queryset
		"""
		self.data_list = data_list
		self.option = option
		self.query_dict = query_dict

	def __iter__(self):
		yield '<div class="whole">'

		tatal_query_dict = self.query_dict.copy()
		tatal_query_dict._mutable = True

		origin_value_list = self.query_dict.getlist(self.option.field)  # [2,]
		if origin_value_list:
			tatal_query_dict.pop(self.option.field)
			yield '<a href="?%s">全部</a>' % (tatal_query_dict.urlencode(),)
		else:
			yield '<a class="active" href="?%s">全部</a>' % (tatal_query_dict.urlencode(),)

		yield '</div>'
		yield '<div class="others">'

		for item in self.data_list:  # item=(),queryset中的一个对象
			val = self.option.get_value(item)
			text = self.option.get_text(item)

			query_dict = self.query_dict.copy()
			query_dict._mutable = True

			if not self.option.is_multi:  # 单选
				if str(val) in origin_value_list:
					query_dict.pop(self.option.field)
					yield '<a class="active" href="?%s">%s</a>' % (query_dict.urlencode(), text)
				else:
					query_dict[self.option.field] = val
					yield '<a href="?%s">%s</a>' % (query_dict.urlencode(), text)
			else:  # 多选
				multi_val_list = query_dict.getlist(self.option.field)
				if str(val) in origin_value_list:
					# 已经选，把自己去掉
					multi_val_list.remove(str(val))
					query_dict.setlist(self.option.field, multi_val_list)
					yield '<a class="active" href="?%s">%s</a>' % (query_dict.urlencode(), text)
				else:
					multi_val_list.append(val)
					query_dict.setlist(self.option.field, multi_val_list)
					yield '<a href="?%s">%s</a>' % (query_dict.urlencode(), text)

		yield '</div>'


class Option(object):

	def __init__(self, field, condition=None, is_choice=False, text_func=None, value_func=None, is_multi=False):
		self.field = field
		self.is_choice = is_choice
		if not condition:
			condition = {}
		self.condition = condition
		self.text_func = text_func
		self.value_func = value_func
		self.is_multi = is_multi

	def get_queryset(self, _field, model_class, query_dict):
		if isinstance(_field, ForeignKey) or isinstance(_field, ManyToManyField):
			row = Row(_field.rel.model.objects.filter(**self.condition), self, query_dict)
		else:
			if self.is_choice:
				row = Row(_field.choices, self, query_dict)
			else:
				row = Row(model_class.objects.filter(**self.condition), self, query_dict)
		return row

	def get_text(self, item):
		if self.text_func:
			return self.text_func(item)
		return str(item)

	def get_value(self, item):
		if self.value_func:
			return self.value_func(item)
		if self.is_choice:
			return item[0]
		return item.pk


class ChangeList(object):
	"""
	封装列表页面需要的所有内容
	"""

	def __init__(self, config, queryset, q, search_list, page):
		self.q = q
		self.search_list = search_list
		self.page = page

		self.config = config
		# 无法在前端页面使用双下方法，只有在后端获取后传过去
		self.action_list = [{'name': func.__name__, 'text': func.text} for func in config.get_action_list()]
		# 获取添加按钮
		self.add_btn = config.get_add_btn()

		self.queryset = queryset

		self.list_display = config.get_list_display()
		self.list_filter = config.get_list_filter()

	def gen_list_filter_rows(self):
		for option in self.list_filter:
			_field = self.config.model_class._meta.get_field(option.field)
			yield option.get_queryset(_field, self.config.model_class, self.config.request.GET)


class StarkConfig(object):

	def __init__(self, model_class, site):
		self.model_class = model_class
		self.site = site
		self.request = None
		self.back_condition_key = "_filter"

	# 左边的id栏
	def display_checkbox(self, row=None, header=False):
		if header:
			return "选择"
		return mark_safe("<input type='checkbox' name='pk' value='%s'/>" % row.pk)

	def display_edit(self, row=None, header=False):
		if header:
			return "编辑"
		return mark_safe('<a href="%s"><i class="fa fa-edit" aria-hidden="true"></i></a>' % self.reverse_edit_url(row))

	def display_del(self, row=None, header=False):
		if header:
			return "删除"
		return mark_safe(
			'<a href="%s"><i class="fa fa-trash-o" aria-hidden="true"></i></a>' % self.reverse_del_url(row))

	# 编辑和删除放在一起
	def display_edit_del(self, row=None, header=False):
		if header:
			return "操作"
		tpl = """<a href="%s"><i class="fa fa-edit" aria-hidden="true"></i></a> |
		<a href="%s"><i class="fa fa-trash-o" aria-hidden="true"></i></a>
		""" % (self.reverse_edit_url(row), self.reverse_del_url(row),)
		return mark_safe(tpl)


	def multi_delete(self, request):
		"""
		批量删除
		"""
		# 批量选择按钮的pk
		pk_list = request.POST.getlist('pk')
		self.model_class.objects.filter(pk__in=pk_list).delete()

	multi_delete.text = "批量删除"

	order_by = []
	list_display = []
	model_form_class = None
	action_list = []
	search_list = []
	list_filter = []

	# 这个在changelist_view调用过
	def get_order_by(self):
		"""
		列表字段排序函数，参数常放id
		"""
		return self.order_by

	# 预留的一个钩子,可以在这里使用默认自带编辑和删除功能
	def get_list_display(self):
		return self.list_display

	# 添加按钮
	def get_add_btn(self):
		return mark_safe('<a href="%s" class="btn btn-success">添加</a>' % self.reverse_add_url())

	def get_model_form_class(self):
		"""
		获取ModelForm类
		"""
		if self.model_form_class:
			return self.model_form_class

		class AddModelForm(forms.ModelForm):
			class Meta:
				model = self.model_class
				fields = "__all__"

		return AddModelForm

	# app01/stark.py下传入的action_list = [multi_init, StarkConfig.multi_delete]
	def get_action_list(self):
		val = []
		val.extend(self.action_list)
		return val  # 列表嵌套列表

	def get_action_dict(self):
		val = {}
		for item in self.action_list:
			val[item.__name__] = item
		return val

	# val值:
	# {'multi_delete': <function StarkConfig.multi_delete at 0x05BDCBB8>,
	# 'multi_init': <function DepartConfig.multi_init at 0x05BDF4B0>}
	def get_search_list(self):
		val = []
		val.extend(self.search_list)
		return val


	def get_search_condition(self, request):
		"""
		搜索栏，支持模糊搜索
		"""
		search_list = self.get_search_list()
		q = request.GET.get('q', "")  # 获取关键字
		con = Q()
		con.connector = "OR"
		if q:
			for field in search_list:
				con.children.append(('%s__contains' % field, q))
		return search_list, q, con

	def get_list_filter(self):
		val = []
		val.extend(self.list_filter)
		return val

	def get_list_filter_condition(self):
		comb_condition = {}
		for option in self.get_list_filter():
			element = self.request.GET.getlist(option.field)
			if element:
				comb_condition['%s__in' % option.field] = element

		return comb_condition

	def changelist_view(self, request):
		"""
		所有URL的查看列表页面
		"""
		if request.method == "POST":
			action_name = request.POST.get("action")
			action_dict = self.get_action_dict()
			if action_name not in action_dict:
				return HttpResponse('非法请求')

			response = getattr(self, action_name)(request)
			if response:
				return response

		############ 搜索处理 ################
		search_list, q, con = self.get_search_condition(request)

		############ 分页处理 ################
		from stark.utils.pagination import Pagination
		total_count = self.model_class.objects.filter(con).count()
		query_params = request.GET.copy()
		query_params._mutable = True
		# 实例化,每页显示7条数据
		page = Pagination(request.GET.get('page'), total_count, request.path_info, query_params, per_page=7)

		list_filter = self.get_list_filter()
		# 获取组合搜索筛选
		queryset = self.model_class.objects.filter(con).filter(**self.get_list_filter_condition()).order_by(
			*self.get_order_by()).distinct()[page.start:page.end]

		cl = ChangeList(self, queryset, q, search_list, page)

		############ 组合搜索 ################

		context = {
			'cl': cl,
		}
		return render(request, 'stark/changelist.html', context)

	def add_view(self, request):
		"""
		所有添加页面
		"""
		AddModelForm = self.get_model_form_class()
		if request.method == "GET":
			form = AddModelForm()
			return render(request, 'stark/change.html', {'form': form})

		form = AddModelForm(request.POST)
		if form.is_valid():
			form.save()
			return redirect(self.reverse_list_url())
		return render(request, 'stark/change.html', {'form': form})

	def change_view(self, request, pk):
		"""
		所有编辑页面
		"""
		obj = self.model_class.objects.filter(pk=pk).first()
		if not obj:
			return HttpResponse('数据不存在')

		ModelFormClass = self.get_model_form_class()
		if request.method == 'GET':
			form = ModelFormClass(instance=obj)
			return render(request, 'stark/change.html', {'form': form})
		form = ModelFormClass(data=request.POST, instance=obj)
		if form.is_valid():
			form.save()
			return redirect(self.reverse_list_url())
		return render(request, 'stark/change.html', {'form': form})

	def delete_view(self, request, pk):
		"""
		所有删除页面
		"""
		if request.method == "GET":
			return render(request, 'stark/delete.html', {'cancel_url': self.reverse_list_url()})

		self.model_class.objects.filter(pk=pk).delete()
		return redirect(self.reverse_list_url())

	def wrapper(self, func):
		@functools.wraps(func)  # 帮助保留原函数信息，建议写上
		def inner(request, *args, **kwargs):
			self.request = request
			return func(request, *args, **kwargs)

		return inner

	def get_urls(self):

		info = self.model_class._meta.app_label, self.model_class._meta.model_name

		urlpatterns = [
			url(r'^list/$', self.wrapper(self.changelist_view), name='%s_%s_changelist' % info),
			url(r'^add/$', self.wrapper(self.add_view), name='%s_%s_add' % info),
			url(r'^(?P<pk>\d+)/change/', self.wrapper(self.change_view), name='%s_%s_change' % info),
			url(r'^(?P<pk>\d+)/del/', self.wrapper(self.delete_view), name='%s_%s_del' % info),
		]

		# 执行可扩展url的钩子函数
		extra = self.extra_url()
		if extra:
			urlpatterns.extend(extra)

		return urlpatterns

	# 预留的可扩展的url钩子函数
	def extra_url(self):
		pass

	def reverse_list_url(self):
		app_label = self.model_class._meta.app_label
		model_name = self.model_class._meta.model_name
		namespace = self.site.namespace
		name = '%s:%s_%s_changelist' % (namespace, app_label, model_name)
		list_url = reverse(name)

		origin_condition = self.request.GET.get(self.back_condition_key)
		if not origin_condition:
			return list_url

		list_url = "%s?%s" % (list_url, origin_condition,)
		return list_url

	def reverse_add_url(self):
		"""
		添加url
		"""
		app_label = self.model_class._meta.app_label
		model_name = self.model_class._meta.model_name
		namespace = self.site.namespace
		name = '%s:%s_%s_add' % (namespace, app_label, model_name)
		add_url = reverse(name)

		if not self.request.GET:
			return add_url
		# url里面显示格式如q=aaa&page=2
		param_str = self.request.GET.urlencode()
		new_query_dict = QueryDict(mutable=True)
		new_query_dict[self.back_condition_key] = param_str
		add_url = "%s?%s" % (add_url, new_query_dict.urlencode(),)

		return add_url

	def reverse_edit_url(self, row):
		# 为了拼接出一个路径
		app_label = self.model_class._meta.app_label
		model_name = self.model_class._meta.model_name
		namespace = self.site.namespace
		name = '%s:%s_%s_change' % (namespace, app_label, model_name)
		edit_url = reverse(name, kwargs={'pk': row.pk})

		if not self.request.GET:
			return edit_url
		param_str = self.request.GET.urlencode()  # q=aaa&page=2
		new_query_dict = QueryDict(mutable=True)
		new_query_dict[self.back_condition_key] = param_str
		edit_url = "%s?%s" % (edit_url, new_query_dict.urlencode(),)

		return edit_url

	def reverse_del_url(self, row):
		app_label = self.model_class._meta.app_label
		model_name = self.model_class._meta.model_name
		namespace = self.site.namespace
		name = '%s:%s_%s_del' % (namespace, app_label, model_name)
		del_url = reverse(name, kwargs={'pk': row.pk})
		if not self.request.GET:
			return del_url
		param_str = self.request.GET.urlencode()  # q=嘉瑞&page=2
		new_query_dict = QueryDict(mutable=True)
		new_query_dict[self.back_condition_key] = param_str
		del_url = "%s?%s" % (del_url, new_query_dict.urlencode(),)

		return del_url

	@property
	def urls(self):
		return self.get_urls()


class AdminSite(object):
	def __init__(self):
		self._registry = {}
		self.app_name = 'stark'
		self.namespace = 'stark'

	# 这里在app01/stark.py下我们site.register(models.UserInfo,UserinfoConfig)调用，UserinfoConfig类继承了
	# 上面的StarkConfig类
	def register(self, model_class, stark_config=None):
		if not stark_config:
			stark_config = StarkConfig
		self._registry[model_class] = stark_config(model_class, self)
		"""
		{
		#　app1下的model　  models.UserInfo: StarkConfig(models.UserInfo),  # 封装：model_class=UserInfo，site=site对象
		#  app2下的model	   -------
		}
		"""

	def get_urls(self):
		urlpatterns = []
		# urlpatterns.append(url(r'^x1/', self.x1))
		# urlpatterns.append(url(r'^x2/', self.x2))
		# urlpatterns.append(url(r'^x3/', ([
		#                                      url(r'^add/', self.x1),
		#                                      url(r'^change/', self.x1),
		#                                      url(r'^del/', self.x1),
		#                                      url(r'^edit/', self.x1),
		#                                  ],None,None)))

		for k, v in self._registry.items():
			# k=modes.UserInfo,v=StarkConfig(models.UserInfo), # 封装：model_class=UserInfo，site=site对象
			# k=modes.Role,v=RoleConfig(models.Role)           # 封装：model_class=Role，site=site对象
			app_label = k._meta.app_label  # 获取app名称
			model_name = k._meta.model_name  # 获取model名

			urlpatterns.append(url(r'^%s/%s/' % (app_label, model_name,), (v.urls, None, None)))
		return urlpatterns

	# 总的url里面调用urls
	@property
	def urls(self):
		return self.get_urls(), self.app_name, self.namespace


site = AdminSite()
