class Pagination:
	def __init__(self, page_num, total_num, per_page_num=10, max_show=11):
		self.page_num = page_num  # 当前页面数
		self.total_num = total_num  # 总数据量
		self.per_page_num = per_page_num  # 每页显示数据条数
		self.max_show = max_show  # 最多显示页码数
		self.half_show = self.max_show // 2
		self.total_page, more = divmod(total_num, per_page_num)
		if more:
			self.total_page += 1
		if self.page_num > self.total_page:
			self.page_num = self.total_page
		elif self.page_num < 1:
			self.page_num = 1

	@property
	def start(self):
		return (self.page_num - 1) * self.per_page_num

	@property
	def end(self):
		return self.page_num * self.per_page_num

	@property
	def page_html(self):
		page_start = self.page_num - self.half_show
		page_end = self.page_num + self.half_show + 1
		if self.page_num + self.half_show >= self.total_page:
			page_end = self.total_page + 1
			page_start = self.total_page - self.max_show + 1
		if self.page_num <= self.half_show:
			page_start = 1
			page_end = self.max_show + 1
		page_num_list = []





		return page_html