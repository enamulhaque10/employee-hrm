"""
admin.py
"""

from django.contrib import admin

from aiz_audit.models import AuditTag, aizAuditInfo, aizAuditLog

# Register your models here.

admin.site.register(AuditTag)
