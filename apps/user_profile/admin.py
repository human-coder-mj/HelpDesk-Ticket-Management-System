from django.contrib import admin
from .models import UserProfile

class AdminModel(admin.ModelAdmin):
    list_display = ('first_name','role', 'department',)

admin.site.register(UserProfile, AdminModel)