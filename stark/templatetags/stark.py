from django.template import Library
from types import FunctionType

register = Library()

def header_list(cl):
	"""
	表头
	"""
	# 存入显示界面第一列所有名称字段，选择，id，title等
	if cl.list_display:
		for name_or_func in cl.list_display:
			# 判断是不是函数
			if isinstance(name_or_func, FunctionType):
				verbose_name = name_or_func(cl, header=True)
			else:
				verbose_name = cl.config.model_class._meta.get_field(name_or_func).verbose_name
			yield verbose_name
	else:
		yield cl.config.model_class._meta.model_name


def body_list(cl):
	"""
	表格内容
	"""
	for row in cl.queryset:
		row_list = []   # [obj1]
		if not cl.list_display:
			row_list.append(row)      # 追加obj对象
			yield row_list
			continue
		for name_or_func in cl.list_display:
			if isinstance(name_or_func,FunctionType):
				val = name_or_func(cl.config,row=row)
			else:
				val = getattr(row,name_or_func)
			row_list.append(val)
		yield row_list


@register.inclusion_tag('stark/table.html')
def table(cl):

	return {'header_list':header_list(cl),'body_list':body_list(cl)}
