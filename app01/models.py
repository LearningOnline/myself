from django.db import models


class UserInfo(models.Model):
	title = models.CharField(max_length=32, verbose_name='名称')

	def __str__(self):
		return self.title


class Project(models.Model):
	name = models.CharField(verbose_name='名称', max_length=32)

	def __str__(self):
		return self.name


class Depart(models.Model):
	name = models.CharField(verbose_name='部门名称', max_length=32)
	tel = models.CharField(verbose_name='联系电话', max_length=32)
	user = models.ForeignKey(verbose_name='负责人', to='UserInfo')
	level_choices = (
		(1, '高级'),
		(2, '中级'),
		(3, '低级')
	)

	level = models.IntegerField(verbose_name='级别', choices=level_choices, default=2)
	proj = models.ManyToManyField(verbose_name='项目', to='Project')

	def __str__(self):
		return self.name
