# conftest.py
pytest_plugins = ['pytest_django']

# conftest.py
# import pytest
# from django.conf import settings

# def pytest_configure():
#     settings.DATABASES['default']['TEST'] = {
#         'NAME': settings.DATABASES['default']['NAME'],
#         'ENGINE': settings.DATABASES['default']['ENGINE'],
#         'USER': settings.DATABASES['default']['USER'],
#         'PASSWORD': settings.DATABASES['default']['PASSWORD'],
#         'HOST': settings.DATABASES['default']['HOST'],
#         'PORT': settings.DATABASES['default']['PORT'],
#     }