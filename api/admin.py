from django.contrib import admin
from api.models import Account, UserRole, Zone, PostCode, WorkerSkill, SkillCostForZone, PublicHoliday

# Register your models here.

admin.site.register(Account)
admin.site.register(UserRole)
admin.site.register(Zone)
admin.site.register(PostCode)
admin.site.register(WorkerSkill)
admin.site.register(SkillCostForZone)
admin.site.register(PublicHoliday)
