from django.apps import AppConfig


class StarkConfig(AppConfig):
    name = 'stark'

    # config.py下的一个空方法，什么都没写
    def ready(self):
        from django.utils.module_loading import autodiscover_modules
        # 自动找寻添加的模块，这里调用的是它的内部方法
        autodiscover_modules('stark')
