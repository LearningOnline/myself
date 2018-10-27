from stark.service.stark import site, StarkConfig, Option, Row
from app01 import models
from django import forms


class UserinfoConfig(StarkConfig):
	order_by = ['-id']  # 调用排序的函数,倒序生成数据
	list_display = ['id', 'title', StarkConfig.display_edit, StarkConfig.display_del]

	# 使用定制的钩子函数
	# def get_list_display(self):
	# 	return ['id', 'title', StarkConfig.display_edit, StarkConfig.display_del]

	# 关键字搜索项,我可以按照id搜索，也能按照title搜索
	search_list = ['id', 'title']


site.register(models.UserInfo, UserinfoConfig)


class DepartModelForm(forms.ModelForm):
	class Meta:
		model = models.Depart
		fields = "__all__"

	def clean_name(self):
		return self.cleaned_data['name']


class DistinctNameOption(Option):

	def get_queryset(self, _field, model_class, query_dict):
		return Row(model_class.objects.filter(**self.condition).values_list('name').distinct(), self, query_dict)


class DepartConfig(StarkConfig):
	# 这里我们把编辑和删除写在了一起
	list_display = [StarkConfig.display_checkbox, 'id', 'name', 'tel', 'user',
	                StarkConfig.display_edit_del]

	model_form_class = DepartModelForm

	# 预留的一个钩子，自己定义下拉初始化内容
	def multi_init(self, request):
		"""
		自定义初始化内容
		"""
		pass

	multi_init.text = "初始化"

	# multi_delete是后台创建的一个批量删除的函数
	action_list = [multi_init, StarkConfig.multi_delete]

	# 可以查询的字段，关键字搜索
	search_list = ['name', 'tel', 'user__title']

	list_filter = [
		# DistinctNameOption('name',condition={'id__gt':9},value_func=lambda x:x[0],text_func=lambda x:x[0],),
		Option('level', is_choice=True, text_func=lambda x: x[1]),
		Option('user', text_func=lambda x: x.title, is_multi=True),
		# Option('tel',text_func=lambda x:x.tel),
		Option('proj', is_multi=True)
	]  # 配置


# 自定义页面，执行它的扩展功能
# def changelist_view(self, request):
# 	return HttpResponse('自定义列表页面')


site.register(models.Depart, DepartConfig)
