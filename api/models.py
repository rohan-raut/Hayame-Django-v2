from enum import unique
from tabnanny import verbose
from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from traitlets import default

from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver
from rest_framework.authtoken.models import Token
from datetime import datetime

# Create your models here.

# Static Classes

class UserRole(models.Model):
    id = models.AutoField(primary_key=True)
    user_role = models.CharField(max_length=50)

    def __str__(self):
        return self.user_role



class PublicHoliday(models.Model):
    id = models.AutoField(primary_key=True)
    holiday_date = models.DateField()
    event = models.CharField(max_length=100)

    def __str__(self):
        return self.event
    

class BookingStatus(models.Model):
    id = models.AutoField(primary_key=True)
    status = models.CharField(max_length=50)
    status_sequence = models.IntegerField()


class WorkerSkill(models.Model):
    id = models.AutoField(primary_key=True)
    skill = models.CharField(max_length=50)
    is_active = models.BooleanField()

    def __str__(self):
        return self.skill
    

class PaymentMethod(models.Model):
    id = models.AutoField(primary_key=True)
    payment_method = models.CharField(max_length=50)

class Voucher(models.Model):
    id = models.AutoField(primary_key=True)
    voucher_code = models.CharField(max_length=50)
    discount = models.DecimalField(max_digits=10, decimal_places=4, null=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.voucher_code


# Master Tables

class MyAccountManager(BaseUserManager):
    def create_user(self, email, username, first_name, last_name, user_role=None, phone=None, password=None):
        if not email:
            raise ValueError("User must have an email address")
        if not username:
            raise ValueError("User must have a username")

        user = self.model(
            email = self.normalize_email(email),
            username = username,
            first_name = first_name,
            last_name = last_name,
            phone = phone,
            user_role = user_role,
        )

        user.set_password(password)
        user.save(using=self.db)
        return user

    
    def create_superuser(self, email, username, first_name, last_name, password, phone=None):
        user = self.create_user(
            email = email,
            username = username,
            password = password,
            first_name = first_name,
            last_name = last_name,
            phone = phone,
        )
        user.is_verified = True
        user.is_admin = True
        user.is_superuser = True
        user.is_staff = True
        user.save(using=self.db)

        return user



class Account(AbstractBaseUser, PermissionsMixin):
    id = models.AutoField(primary_key=True)
    email = models.EmailField(verbose_name="email", max_length=254, unique=True)
    username = models.CharField(max_length=100, unique=True)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    user_role = models.ForeignKey(UserRole, on_delete=models.PROTECT, null=True)
    phone = models.CharField(max_length=20, null=True)
    is_verified = models.BooleanField(default=False)
    date_joined = models.DateTimeField(verbose_name="date joined", auto_now_add=True)
    last_login = models.DateTimeField(verbose_name="last login", auto_now=True)
    is_admin = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["username", "first_name", "last_name", "phone"]

    objects = MyAccountManager()

    def __str__(self):
        return self.email

    def has_perm(self, perm, obj=None):
        return self.is_admin

    def has_module_perm(self, app_label):
        return True


class Zone(models.Model):
    id = models.AutoField(primary_key=True)
    zone = models.CharField(max_length=100)
    city = models.CharField(max_length=100)
    start_postcode = models.IntegerField()
    end_postcode = models.IntegerField()
    manager = models.ForeignKey(Account, on_delete=models.PROTECT)

    def __str__(self):
        return self.zone + " - " + self.city


class SkillCostForZone(models.Model):
    id = models.AutoField(primary_key=True)
    zone = models.ForeignKey(Zone, on_delete=models.CASCADE)
    skill = models.ForeignKey(WorkerSkill, on_delete=models.CASCADE)
    cost_per_hour_normal_day = models.DecimalField(max_digits=10, decimal_places=2)
    cost_per_hour_public_holiday = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return self.skill.skill + " - " + self.zone.city


class PostCode(models.Model):
    id = models.AutoField(primary_key=True)
    post_code = models.IntegerField()
    zone = models.ForeignKey(Zone, on_delete=models.CASCADE)

    def __str__(self):
        return str(self.post_code)



class Addon(models.Model):
    id = models.AutoField(primary_key=True)
    skill = models.CharField(max_length=50)
    addon_service = models.CharField(max_length=50)
    cost_per_hour = models.DecimalField(max_digits=10, decimal_places=2)


class CleanerBooking(models.Model):
    id = models.AutoField(primary_key=True)
    booking_id = models.CharField(max_length=50, null=True)
    address = models.CharField(max_length=500)
    post_code = models.IntegerField(null=True)
    property_type = models.CharField(max_length=50, null=True)
    customer = models.ForeignKey(Account, on_delete=models.PROTECT, related_name='cleaner_customer')
    frequency = models.CharField(max_length=50, null=True)
    start_date = models.DateField()
    start_time = models.TimeField()
    no_of_hours = models.DecimalField(max_digits=10, decimal_places=2, null=True)
    worker_count = models.IntegerField()
    worker_gender = models.CharField(max_length=20)
    addons = models.ForeignKey(Addon, on_delete=models.PROTECT, null=True)
    addons_service_hours = models.DecimalField(max_digits=10, decimal_places=2, null=True)
    transportation_cost = models.DecimalField(max_digits=10, decimal_places=2)
    worker_cost = models.DecimalField(max_digits=10, decimal_places=2)
    total_cost = models.DecimalField(max_digits=10, decimal_places=2, null=True)
    voucher = models.ForeignKey(Voucher, on_delete=models.PROTECT, null=True)
    booking_status = models.ForeignKey(BookingStatus, on_delete=models.PROTECT)
    booking_created_date = models.DateField(null=True)
    managed_by = models.ForeignKey(Account, on_delete=models.PROTECT, null=True, related_name='cleaner_booking_manager')

    def __str__(self):
        return str(self.booking_id)


class GardenerBooking(models.Model):
    id = models.AutoField(primary_key=True)
    booking_id = models.CharField(max_length=50)
    address = models.CharField(max_length=500)
    post_code = models.ForeignKey(PostCode, on_delete=models.PROTECT, null=True)
    property_type = models.CharField(max_length=50, null=True)
    customer = models.ForeignKey(Account, on_delete=models.PROTECT, related_name='gardener_customer')
    frequency = models.CharField(max_length=50, null=True)
    start_date = models.DateField()
    start_time = models.TimeField()
    no_of_hours = models.DecimalField(max_digits=10, decimal_places=2, null=True)
    square_feet = models.IntegerField()
    worker_count = models.IntegerField()
    worker_gender = models.CharField(max_length=20)
    transportation_cost = models.DecimalField(max_digits=10, decimal_places=2)
    worker_cost = models.DecimalField(max_digits=10, decimal_places=2)
    total_cost = models.DecimalField(max_digits=10, decimal_places=2, null=True)
    voucher = models.ForeignKey(Voucher, on_delete=models.PROTECT, null=True)
    booking_status = models.ForeignKey(BookingStatus, on_delete=models.PROTECT)
    managed_by = models.ForeignKey(Account, on_delete=models.PROTECT, null=True, related_name='gardener_booking_manager')


class MoverPackerBooking(models.Model):
    id = models.AutoField(primary_key=True)
    booking_id = models.CharField(max_length=50)
    start_address = models.CharField(max_length=500)
    end_address = models.CharField(max_length=500)
    start_post_code = models.ForeignKey(PostCode, on_delete=models.PROTECT, null=True, related_name='start_postcode')
    end_post_code = models.ForeignKey(PostCode, on_delete=models.PROTECT, null=True, related_name='end_postcode')
    property_type = models.CharField(max_length=50, null=True)
    has_lift = models.BooleanField()
    floors = models.IntegerField()
    customer = models.ForeignKey(Account, on_delete=models.PROTECT, related_name='mover_packer_customer')
    start_date = models.DateField()
    start_time = models.TimeField()
    no_of_boxes_to_pack = models.IntegerField() # esitmates box size needs to be considered
    transportation_cost = models.DecimalField(max_digits=10, decimal_places=2)
    worker_cost = models.DecimalField(max_digits=10, decimal_places=2)
    total_cost = models.DecimalField(max_digits=10, decimal_places=2, null=True)
    booking_status = models.ForeignKey(BookingStatus, on_delete=models.PROTECT)
    managed_by = models.ForeignKey(Account, on_delete=models.PROTECT, null=True, related_name='mover_packer_booking_manager')


class GeneralWorkerBooking(models.Model):
    id = models.AutoField(primary_key=True)
    booking_id = models.CharField(max_length=50)
    address = models.CharField(max_length=500)
    post_code = models.ForeignKey(PostCode, on_delete=models.PROTECT, null=True)
    property_type = models.CharField(max_length=50, null=True)
    customer = models.ForeignKey(Account, on_delete=models.PROTECT, related_name='general_worker_customer')
    frequency = models.CharField(max_length=50, null=True)
    start_date = models.DateField()
    start_time = models.TimeField()
    no_of_hours = models.DecimalField(max_digits=10, decimal_places=2, null=True)
    worker_count = models.IntegerField()
    worker_gender = models.CharField(max_length=20)
    transportation_cost = models.DecimalField(max_digits=10, decimal_places=2)
    worker_cost = models.DecimalField(max_digits=10, decimal_places=2)
    total_cost = models.DecimalField(max_digits=10, decimal_places=2, null=True)
    voucher = models.ForeignKey(Voucher, on_delete=models.PROTECT, null=True)
    booking_status = models.ForeignKey(BookingStatus, on_delete=models.PROTECT)
    managed_by = models.ForeignKey(Account, on_delete=models.PROTECT, null=True, related_name='general_worker_booking_manager')



class ElderlyCareBooking(models.Model):
    id = models.AutoField(primary_key=True)
    booking_id = models.CharField(max_length=50)
    address = models.CharField(max_length=500)
    post_code = models.ForeignKey(PostCode, on_delete=models.PROTECT, null=True)
    customer = models.ForeignKey(Account, on_delete=models.PROTECT, related_name='elderly_care_customer')
    frequency = models.CharField(max_length=50, null=True)
    start_date = models.DateField()
    start_time = models.TimeField()
    no_of_hours = models.DecimalField(max_digits=10, decimal_places=2, null=True)
    worker_count = models.IntegerField()
    worker_gender = models.CharField(max_length=20)
    transportation_cost = models.DecimalField(max_digits=10, decimal_places=2)
    worker_cost = models.DecimalField(max_digits=10, decimal_places=2)
    total_cost = models.DecimalField(max_digits=10, decimal_places=2, null=True)
    voucher = models.ForeignKey(Voucher, on_delete=models.PROTECT, null=True)
    booking_status = models.ForeignKey(BookingStatus, on_delete=models.PROTECT)
    managed_by = models.ForeignKey(Account, on_delete=models.PROTECT, null=True, related_name='elderly_care_booking_manager')


class TaskErrandsBooking(models.Model):
    id = models.AutoField(primary_key=True)
    booking_id = models.CharField(max_length=50)
    address = models.CharField(max_length=500)
    post_code = models.ForeignKey(PostCode, on_delete=models.PROTECT, null=True)
    property_type = models.CharField(max_length=50, null=True)
    customer = models.ForeignKey(Account, on_delete=models.PROTECT, related_name='task_errands_customer')
    task_type = models.CharField(max_length=50)
    start_date = models.DateField()
    start_time = models.TimeField()
    transportation_cost = models.DecimalField(max_digits=10, decimal_places=2)
    worker_cost = models.DecimalField(max_digits=10, decimal_places=2)
    total_cost = models.DecimalField(max_digits=10, decimal_places=2, null=True)
    voucher = models.ForeignKey(Voucher, on_delete=models.PROTECT, null=True)
    booking_status = models.ForeignKey(BookingStatus, on_delete=models.PROTECT)
    managed_by = models.ForeignKey(Account, on_delete=models.PROTECT, null=True, related_name='task_errands_booking_manager')


class Worker(models.Model):
    id = models.AutoField(primary_key=True)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    skill = models.ForeignKey(WorkerSkill, on_delete=models.CASCADE, null=True)
    manager = models.ForeignKey(Account, on_delete=models.PROTECT)
    email = models.EmailField(verbose_name="email", max_length=254, unique=True)
    passport_no = models.CharField(max_length=100)
    phone = models.CharField(max_length= 20)

    def __str__(self):
        return str(self.email)


class AllocateWorker(models.Model):
    id = models.AutoField(primary_key=True)
    booking_id = models.ForeignKey(CleanerBooking, on_delete=models.PROTECT)
    worker_id = models.ForeignKey(Worker, on_delete=models.PROTECT)


class Notifications(models.Model):
    id = models.AutoField(primary_key=True)
    message = models.CharField(max_length=500)
    user_id = models.ForeignKey(Account, on_delete=models.CASCADE)
    is_read = models.BooleanField(default=False)
    date_time = models.DateTimeField()


class Payment(models.Model):
    id = models.AutoField(primary_key=True)
    booking_id = models.ForeignKey(CleanerBooking, on_delete=models.CASCADE)
    payment_status = models.CharField(max_length=50)
    transaction_id = models.CharField(max_length=100)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    PaymentMethod = models.ForeignKey(PaymentMethod, on_delete=models.PROTECT)





class FrequencyDiscount(models.Model):
    id = models.AutoField(primary_key=True)
    skill = models.CharField(max_length=50)
    frequency = models.CharField(max_length=50)
    discount_perc = models.DecimalField(max_digits=10, decimal_places=2)

