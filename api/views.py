from django.shortcuts import render, HttpResponse
from rest_framework.response import Response
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.contrib.auth import authenticate
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.tokens import RefreshToken
import smtplib
import ssl
import email
from email import encoders
from email.mime.base import MIMEBase
from email.mime.image import MIMEImage
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import jwt
from api.models import Account, Zone, PostCode, SkillCostForZone, WorkerSkill, PublicHoliday, Voucher, CleanerBooking, BookingStatus, UserRole, Addon, FrequencyDiscount, Worker
from api.serializers import AccountSerializer, BookingHistorySerializer
from rest_framework_simplejwt.tokens import RefreshToken
from google.oauth2 import id_token
from google.auth.transport import requests
import datetime


global sender_email, sender_name, password, sessions, config

sender_email = "hayamedotmy@gmail.com"
sender_name = "Hayame Admin"
password = "dnndjbtorrxpyowx"


config = {
    'sessions': 4
}


# Create your views here.

def send_notification(receiver_email, subject, body):
    try:
        html_body = """\
        <html>
        <head>
            <style>
                .container{{
                    border: 2px solid black;
                }}
                .header{{
                    text-align: center;
                    background-color: #2FB0AA;
                    padding: 10px 0px;
                }}
                .header img{{
                    width: 200px;
                }}
                .content{{
                    background-color: #E9EBF8;
                }}
                p{{
                    margin: 0px;
                    padding: 8px;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <img src="cid:Mailtrapimage">
                </div>
                <div class="content">
                    {body}
                </div>
            </div>
        </body>
        </html>""".format(body=body)

        fp = open('static/logo.png', 'rb')
        image = MIMEImage(fp.read())
        fp.close()
        
        smtpObj = smtplib.SMTP(host='smtp.gmail.com', port=587)
        smtpObj.starttls()
        smtpObj.login(sender_email, password)
        message = MIMEMultipart()
        message["From"] = sender_name
        message["To"] = receiver_email
        message["Subject"] = subject
        image.add_header('Content-ID', '<Mailtrapimage>')
        message.attach(MIMEText(html_body, "html"))
        message.attach(image)
        text = message.as_string()
        smtpObj.sendmail(sender_email, receiver_email, text)
        return True
    except smtplib.SMTPException:
        print("Some problem occured")
        return False
    
def get_tokens_for_user(user):
    refresh = RefreshToken.for_user(user)

    return {
        'refresh': str(refresh),
        'access': str(refresh.access_token),
    }

@api_view(['POST'])
def login_view(request):
    username = request.data['username']
    password = request.data['password']
    user = authenticate(request, username=username, password=password)
    data = {}
    if user is not None:
        if user.is_verified == False:
            token = RefreshToken.for_user(user)
            data['success'] = False
            data['response'] = "Please verify your email before login."
            access_token = str(token.access_token)
            # body = "Hello " + account.first_name + ",\nPlease click on the given link to verify your email address.\nLink: http://hayame.my/verify-user?user=" + token
            body = '''<p>Hello {first_name},</p>
            <p>Please click on the given link to verify your email address.</p>
            <p>Verification Link: http://127.0.0.1:3000/user-verification?user={token}</p>'''.format(first_name=user.first_name, token=access_token)
            subject = "Hayame: Email Verification"
            send_notification(user.email, subject, body)
        else:
            token = RefreshToken.for_user(user)
            data['success'] = True
            data['response'] = "Login Successful"
            data['access_token'] = str(token.access_token)
            data['refresh_token'] = str(token)
            data['user_id'] = user.id
            data['first_name'] = user.first_name
            data['last_name'] = user.last_name
            data['email'] = user.email
            data['phone'] = user.phone
            data['user_role'] = user.user_role.user_role
    else:
        data['response'] = "Wrong Credentials. Please try again."
        data['success'] = False
    return Response(data)  


@api_view(['GET'])
@permission_classes((IsAuthenticated,))
def get_user_details_view(request):
    data = {
        'first_name': request.user.first_name,
        'last_name': request.user.last_name,
        'email': request.user.email,
        'phone': request.user.phone,
    }

    return Response(data)


@api_view(['GET'])
def verify_user_view(request, access_token):

    decodedPayload = jwt.decode(access_token, algorithms=["HS256"], options={"verify_signature": False})

    data = {}
    user = Account.objects.get(id=decodedPayload['user_id'])
    user.is_verified = True
    user.save()
    data['success'] = True
    data['response'] = "Successfully verified the user."
    return Response(data) 


@api_view(['POST'])
def registration_view(request):
    if request.method == 'POST':
        serializer = AccountSerializer(data=request.data)
        data = {}
        if serializer.is_valid():
            account = serializer.save()

            data['response'] = 'Successfully Registered. Verify your email before login.'
            data['success'] = True

            # send verification email
            access_token = get_tokens_for_user(account)
            access_token = access_token['access']
            body = '''<p>Hello {first_name},</p>
            <p>Please click on the given link to verify your email address.</p>
            <p>Verification Link: http://127.0.0.1:3000/user-verification?user={token}</p>'''.format(first_name=account.first_name, token=access_token)
            subject = "Hayame: Email Verification"
            send_notification(account.email, subject, body)

        else:
            data = serializer.errors
            data['response'] = "Account with this email already exists. Try to Login."
            data['success'] = False
        return Response(data)
    

@api_view(['POST'])
def forgot_password_view(request):
    email = request.data['email']
    user = Account.objects.filter(email=email).exists()

    data = {}
    if(user == True):
        user = Account.objects.get(email=email)
        access_token = get_tokens_for_user(user)
        access_token = access_token['access']
        data['success'] = True
        data["response"] = "Password reset link sent on your email."
        data["token"] = access_token
        subject = "Hayame: Password Reset Link."
        body = "Hello " + user.first_name + ",\nThis is your password reset link.\nLink: http://hayame.my/reset-password?user=" + access_token
        body = '''<p>Hello {first_name},</p>
            <p>This is your password reset link.</p>
            <p>Password Reset Link: http://127.0.0.1:3000/reset-password?user={token}</p>'''.format(first_name=user.first_name, token=access_token)
        send_notification(receiver_email=email, subject=subject, body=body)
    else:
        data['success'] = False
        data["response"] = "User with the given email does not exists. Please try to Register."
    
    return Response(data)



@api_view(['POST'])
def reset_password_view(request, access_token):
    # pk is user's token
    # fields: password, change_password
    password = request.data['password']
    confirm_password = request.data['confirm_password']
    
    data = {}
    if(password != confirm_password):
        data['response'] = "Password does not match."
    else:
        decodedPayload = jwt.decode(access_token, algorithms=["HS256"], options={"verify_signature": False})
        user = Account.objects.get(id=decodedPayload['user_id'])
        user.set_password(password)
        user.save()
        data['response'] = "Password changed successfully."

    return Response(data)


@api_view(['POST'])
@permission_classes((IsAuthenticated,))
def change_password_view(request):
    password = request.data['password']
    confirm_password = request.data['confirm_password']

    data = {}
    if(password == confirm_password):
        user = Account.objects.get(id=request.user.id)
        user.set_password(password)
        user.save()
        data = {
            'success': True,
            'response': 'Password changed successfully'
        }
    else:
        data = {
            'success': False,
            'response': "Password and Confirm Password doesn't match"
        }

    return Response(data)


@api_view(['POST'])
def google_signin_view(request):
    email = request.data['email']
    first_name = request.data['first_name']
    last_name = request.data['last_name']
    data = {}
    
    user = None
    try:
        user = Account.objects.get(email=email)
    except:
        pass


    if(user == None):
        user_role = UserRole.objects.get(user_role="Customer")
        password = Account.objects.make_random_password(length=100)
        new_user = Account.objects.create_user(email=email, username=email, first_name=first_name, last_name=last_name, password=password, user_role=user_role)
        new_user.is_verified = True
        new_user.save()
        user = new_user


    data['success'] = True
    data['response'] = "Login Successful"
    token = get_tokens_for_user(user)
    token = token['access']
    data['access_token'] = token
    data['user_id'] = user.id
    data['first_name'] = user.first_name
    data['last_name'] = user.last_name
    data['email'] = user.email
    data['phone'] = user.phone
    data['user_role'] = user.user_role.user_role   

    return Response(data)


@api_view(['GET'])
def refresh_postcode_view(request):
    PostCode.objects.all().delete()
    zones = Zone.objects.all()

    for zone in zones:
        for postcode in range(zone.start_postcode, (zone.end_postcode + 1)):
            postcode_obj = PostCode(post_code=postcode, zone=zone)
            postcode_obj.save()

    return HttpResponse("<p>Refresh Success</p>")


@api_view(['POST'])
def send_query_view(request):
    first_name = request.data['first_name']
    last_name = request.data['first_name']
    email = request.data['email']
    subject = request.data['subject']
    message = request.data['message']

    data = {}
    body = '''<p><<Query from {name} - {email}>></p>
    <p>{message}</p>'''.format(name=(first_name + " " + last_name), email=email, message=message)
    send_notification('support@hayame.my', subject, body)

    data['success'] = True
    data['message'] = "Message sent successfully"
    return Response(data)


@api_view(['GET'])
def get_all_postcodes_view(request):
    data = []
    postcodes = PostCode.objects.all()
    for postcode in postcodes:
        data.append(postcode.post_code)

    return Response(data)


def get_cost(frequency, start_date, no_of_hours, skill, postcode, voucher, addon, addon_service_hours, worker_count):
    skill = WorkerSkill.objects.get(skill=skill)
    postcode = PostCode.objects.get(post_code=postcode)

    worker_cost = 0
    transportation_cost = 0
    total_cost = 0

    cost_for_skill = SkillCostForZone.objects.get(skill=skill, zone=postcode.zone)
    is_public_holiday = PublicHoliday.objects.filter(holiday_date=start_date)

    if(len(is_public_holiday) == 0):
        worker_cost = cost_for_skill.cost_per_hour_normal_day * int(no_of_hours)
    else:
        worker_cost = cost_for_skill.cost_per_hour_public_holiday * int(no_of_hours)

    if(frequency == "weekly" or frequency == "fortnightly"):
        worker_cost = sessions * worker_cost

    worker_cost = worker_cost * int(worker_count)
    total_cost = worker_cost + transportation_cost

    try:
        addon_obj = Addon.objects.get(addon_service=addon)
        addon_cost = float(float(addon_obj.cost_per_hour) * addon_service_hours)
        total_cost = float(total_cost) + addon_cost
    except Exception as e:
        print("Not able to find the addon - " + addon)
        print(e)


    voucher_obj = None

    try:
        voucher_obj = Voucher.objects.get(voucher_code=voucher, is_active=True)
    except:
        print("No voucher available")

    discount = 0
    if(voucher_obj != None):
        discount = round(float(total_cost) * float(voucher_obj.discount), 2)
        total_cost = float(total_cost) - discount

    data = {
        "worker_cost": worker_cost,
        "transportation_cost": transportation_cost,
        "total_cost": total_cost,
        "discount": discount
    }

    return data


@api_view(['POST'])
def get_cleaner_booking_cost_view(request):
    frequency = request.data['frequency']
    start_date = request.data['start_date']
    no_of_hours = request.data['no_of_hours']
    skill = request.data['skill']
    postcode = request.data['postcode']
    voucher = request.data['voucher']
    addon = request.data['addon']
    addon_service_hours = request.data['addon_service_hours']
    worker_count = request.data['worker_count']

    data = get_cost(frequency, start_date, no_of_hours, skill, postcode, voucher, addon, addon_service_hours, worker_count)

    return Response(data)


@api_view(['POST'])
@permission_classes((IsAuthenticated,))
def book_cleaner_view(request):
    frequency = request.data['frequency']
    start_date = request.data['start_date']
    no_of_hours = request.data['no_of_hours']
    start_time = request.data['start_time']
    address = request.data['address']
    postcode = int(request.data['postcode'])
    property_type = request.data['property_type']
    voucher = request.data['voucher']
    payment_method = request.data['payment_method']
    phone = request.data['phone']
    addon = request.data['addon']
    addon_service_hours = request.data['addon_service_hours']
    worker_count = request.data['worker_count']

    if(phone != ""):
        user = Account.objects.get(id=request.user.id)
        user.phone = phone
        user.save()

    months = ["JAN", "FEB", "MAR", "APR", "MAY", "JUN", "JUL", "AUG", "SEP", "OCT", "NOV", "DEC"]
    curr_date = datetime.datetime.now()

    booking_complete_obj = BookingStatus.objects.get(status="Booking Complete")
    successful_bookings = CleanerBooking.objects.filter(booking_status=booking_complete_obj, booking_created_date=datetime.date.today())

    booking_id = str(curr_date.year) + months[curr_date.month - 1] + str(curr_date.day) + "-" + str(len(successful_bookings) + 1)
    cost_dic = get_cost(frequency, start_date, no_of_hours, "Cleaner", postcode, voucher, addon, addon_service_hours, worker_count)
    postcode_obj = PostCode.objects.get(post_code=postcode)
    manager = postcode_obj.zone.manager
    booking_status_obj = BookingStatus.objects.get(status="Booking Complete")

    addon_obj = None
    try:
        addon_obj = Addon.objects.get(addon_service=addon)
    except:
        print("cannot find addon")

    booking_obj = CleanerBooking(booking_id=booking_id, address=address, post_code=postcode, property_type=property_type, customer=request.user, frequency=frequency, start_date=start_date, start_time=start_time, no_of_hours=no_of_hours, worker_count=worker_count, worker_gender="Male", addons=addon_obj, addons_service_hours=addon_service_hours, transportation_cost=cost_dic['transportation_cost'], worker_cost=cost_dic['worker_cost'], total_cost=cost_dic['total_cost'], booking_status=booking_status_obj, booking_created_date=datetime.date.today(), managed_by=manager)

    booking_obj.save()
    
    data = {
        "success": True,
        "response": "Booked Cleaner Successfully"
    }

    return Response(data)



@api_view(['GET'])
@permission_classes((IsAuthenticated,))
def get_booking_history_view(request):
    user = request.user

    bookings = CleanerBooking.objects.filter(customer=user)
    serializer = BookingHistorySerializer(bookings, many=True)

    return Response(serializer.data)


@api_view(['GET'])
@permission_classes((IsAuthenticated,))
def check_bookings_view(request):
    user = request.user

    booking_status_obj = BookingStatus.objects.get(status="Booking Complete")

    bookings = CleanerBooking.objects.filter(booking_status=booking_status_obj)

    if(user.user_role == "Manager"):
        bookings = CleanerBooking.objects.filter(managed_by=user ,booking_status=booking_status_obj)

    data = []

    for booking in bookings:
        data.append({
            'id': booking.id,
            'address': booking.address,
            'property_type': booking.property_type,
            'customer_name': booking.customer.first_name + ' ' + booking.customer.last_name,
            'customer_email': booking.customer.email,
            'customer_phone': booking.customer.phone,
            'frequency': booking.frequency,
            'start_date': booking.start_date,
            'start_time': booking.start_time,
            'no_of_hours': booking.no_of_hours,
            'total_cost': booking.total_cost
        })

    return Response(data)


@api_view(['GET'])
def get_all_addons(request):
    data = []
    addons = Addon.objects.all()
    for addon in addons:
        data.append({
            'skill': addon.skill,
            'addon': addon.addon_service,
            'cost': addon.cost
        })
    
    return Response(data)

@api_view(['POST'])
def get_frequency_discount_by_skill_view(request):
    skill = request.data['skill']
    post_code = request.data['post_code']

    post_code_obj = PostCode.objects.get(post_code=post_code)
    skill_obj = WorkerSkill.objects.get(skill=skill)
    worker_cost = SkillCostForZone.objects.get(zone=post_code_obj.zone, skill=skill_obj)
    data = []

    freq_discount_objs = FrequencyDiscount.objects.filter(skill=skill)
    for obj in freq_discount_objs:
        cost_for_normal_day = round(worker_cost.cost_per_hour_normal_day - (worker_cost.cost_per_hour_normal_day * obj.discount_perc), 0)
        cost_for_public_holiday = round(worker_cost.cost_per_hour_public_holiday - (worker_cost.cost_per_hour_public_holiday * obj.discount_perc), 0)
        data.append({
            'frequency': obj.frequency,
            'discount_perc': obj.discount_perc,
            'worker_cost_normal_day': cost_for_normal_day,
            'worker_cost_public_holiday': cost_for_public_holiday
        })
    
    return Response(data)


@api_view(['POST'])
def get_available_slots(request):
    post_code = request.data['post_code']
    skill = request.data['skill']
    start_date = request.data['start_date']
    no_of_hours = request.data['no_of_hours']
    worker_count = int(request.data['worker_count'])

    skill_obj = WorkerSkill.objects.get(skill=skill)
    worker_list = Worker.objects.filter(skill=skill_obj)

    data = []
    all_slots = [
        {'value': '09:00', 'label': '9:00 am'},
        {'value': '10:00', 'label': '10:00 am'},
        {'value': '11:00', 'label': '11:00 am'},
        {'value': '12:00', 'label': '12:00 pm'},
        {'value': '13:00', 'label': '1:00 pm'},
        {'value': '14:00', 'label': '2:00 pm'},
        {'value': '15:00', 'label': '3:00 pm'},
        {'value': '16:00', 'label': '4:00 pm'},
        {'value': '17:00', 'label': '5:00 pm'},
        {'value': '18:00', 'label': '6:00 pm'},
        {'value': '19:00', 'label': '7:00 pm'},
        {'value': '20:00', 'label': '8:00 pm'}
    ]

    data = all_slots

    return Response(data)



# Update API's

@api_view(['POST'])
@permission_classes((IsAuthenticated,))
def update_user_details_view(request):
    first_name = request.data['first_name']
    last_name = request.data['last_name']
    email = request.data['email']
    phone = request.data['phone']

    user = Account.objects.get(id=request.user.id)
    user.first_name = first_name
    user.last_name = last_name
    user.phone = phone
    user.save()

    data = {
        'success': True,
        'response': 'User details updated successfully'
    }

    return Response(data)