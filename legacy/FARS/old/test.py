import firebase_admin
from firebase_admin import credentials, storage
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

cred = credentials.Certificate("ServiceAccountKey.json")
firebase_admin.initialize_app(cred, {
    'databaseURL': "https://fars-81b18-default-rtdb.firebaseio.com/",
    'storageBucket': "fars-81b18.appspot.com"
})
bucket = storage.bucket()

smtp_server = 'smtp.gmail.com'
smtp_port = 587
sender_email = 'sit23sc011@sairamtap.edu.in'
# sumar sender_password = 'svivtdwbyuslgphy'
sender_password = 'lzgdtakiaezdjseu'
recipient_email = 'hodsc@sairamit.edu.in'
student_info = []

def send_email():
    subject = "FARS - TEST EMAIL"
    body = ("Hi Sir. This is the AUTOMATED TEST email from FARS ( FULLY AUTOMATED ROBOTIC SYSTEMS )")
    # Student ID: {student_info['id']}
    # Name: {student_info['name']}
    # Department: {student_info['Department']}
    # Starting Year: {student_info['starting_year']}
    # Total Attendance: {student_info['total_attendance']}
    # Standing: {student_info['standing_Rank']}
    # Year: {student_info['year']}
    # Last Attendance Time: {student_info['last_attendance_time']}
    # """
    message = MIMEMultipart()
    message['From'] = sender_email
    message['To'] = recipient_email
    message['Subject'] = subject
    message.attach(MIMEText(body, 'plain'))

    try:
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(sender_email, sender_password)
            server.sendmail(sender_email, recipient_email, message.as_string())
        print("Email sent successfully")
    except Exception as e:
        print(f"Failed to send email: {e}")


send_email()
