from django.db import models
from django.contrib import admin
from ourstorybook.adventure.models import Branch
from tinymce.widgets import TinyMCE
class BranchAdmin(admin.ModelAdmin):
    formfield_overrides = {
        models.TextField: {'widget': TinyMCE(attrs={'cols': 80, 'rows': 20}, )},
    }
admin.site.register(Branch, BranchAdmin)
