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
from api.models import Account, Zone, PostCode, SkillCostForZone, WorkerSkill, PublicHoliday, Voucher, CleanerBooking, BookingStatus, UserRole
from api.serializers import AccountSerializer, BookingHistorySerializer
from rest_framework_simplejwt.tokens import RefreshToken
from google.oauth2 import id_token
from google.auth.transport import requests


global sender_email, sender_name, password, sessions

sender_email = "hayamedotmy@gmail.com"
sender_name = "Hayame Admin"
password = "dnndjbtorrxpyowx"

sessions = 4


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


def get_cost(frequency, start_date, no_of_hours, skill, postcode, voucher):
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

    if(frequency != "one-time"):
        worker_cost = sessions * worker_cost

    total_cost = worker_cost + transportation_cost

    voucher_obj = None

    try:
        voucher_obj = Voucher.objects.get(voucher_code=voucher, is_active=True)
    except:
        print("No voucher available")

    discount = 0
    if(voucher_obj != None):
        discount = total_cost * voucher_obj.discount
        total_cost = total_cost - discount

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

    data = get_cost(frequency, start_date, no_of_hours, skill, postcode, voucher)

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

    cost_dic = get_cost(frequency, start_date, no_of_hours, "Cleaner", postcode, voucher)
    postcode_obj = PostCode.objects.get(post_code=postcode)
    manager = postcode_obj.zone.manager
    booking_status_obj = BookingStatus.objects.get(status="Booking Complete")

    booking_obj = CleanerBooking(address=address, post_code=postcode_obj, property_type=property_type, customer=request.user, frequency=frequency, start_date=start_date, start_time=start_time, no_of_hours=no_of_hours, worker_count=1, worker_gender="Male", transportation_cost=cost_dic['transportation_cost'], worker_cost=cost_dic['worker_cost'], total_cost=cost_dic['total_cost'], booking_status=booking_status_obj, managed_by=manager)

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