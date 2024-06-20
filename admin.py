from django.contrib import admin
from . import models

# Register your models here.
admin.site.register(models.Survey)
admin.site.register(models.Response_type)
admin.site.register(models.Question)
admin.site.register(models.Question_translation)
admin.site.register(models.Survey_key)
admin.site.register(models.Submission)
admin.site.register(models.Response)
