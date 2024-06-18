from django.contrib import admin
from api.models import Account, UserRole, Zone, PostCode, WorkerSkill, SkillCostForZone, PublicHoliday, CleanerBooking, Voucher, BookingStatus, Addon, GardenerBooking, MoverPackerBooking, GeneralWorkerBooking, ElderlyCareBooking, TaskErrandsBooking, FrequencyDiscount, Worker

# Register your models here.

admin.site.register(Account)
admin.site.register(UserRole)
admin.site.register(Zone)
admin.site.register(PostCode)
admin.site.register(WorkerSkill)
admin.site.register(SkillCostForZone)
admin.site.register(PublicHoliday)
admin.site.register(CleanerBooking)
admin.site.register(Voucher)
admin.site.register(BookingStatus)
admin.site.register(Addon)
admin.site.register(GardenerBooking)
admin.site.register(MoverPackerBooking)
admin.site.register(GeneralWorkerBooking)
admin.site.register(ElderlyCareBooking)
admin.site.register(TaskErrandsBooking)
admin.site.register(FrequencyDiscount)
admin.site.register(Worker)
