import os
import smtplib
import datetime


from dotenv import load_dotenv
from flask_login import current_user, LoginManager, UserMixin
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from images_handler import CloudflareR2Handler


project_folder = os.path.expanduser(os.path.abspath(os.path.curdir))  # adjust as appropriate
load_dotenv(os.path.join(project_folder, '.env'))

BUCKET_NAME = os.getenv("BUCKET_NAME")
ACCESS_KEY = os.getenv("ACCESS_KEY")
SECRET_ACCESS_KEY = os.getenv("SECRET_ACCESS_KEY")
TOKEN_VALUE = os.getenv("TOKEN_VALUE")
ENDPOINT_URL = os.getenv("ENDPOINT_URL")
R2_DEV_BUCKET_URL = os.getenv("R2-DEV-BUCKET-URL")
DB_FILE = os.getenv("DB_FILE")
WEBSITE_EMAIL = os.getenv("WEBSITE_EMAIL")
DEV_EMAIL = os.getenv("DEV_EMAIL")
GMAIL_PASS = os.getenv("GMAIL_APP_PASSWORD")

# CONFIG_FILE = "backup_config.json"
CONFIG_FILE = "backup_time.txt"
# Initialize the handler
r2_handler = CloudflareR2Handler(ACCESS_KEY, SECRET_ACCESS_KEY, BUCKET_NAME, ENDPOINT_URL)

cities = sorted(open("cities.txt", "r", encoding="utf8").readlines())
statuses = ["تم تأكيد الطلب", "تم تجهيز الطلب", "تم التوصيل"]



class User(UserMixin):
    def __init__(self, id_number, phone_number, first_name, last_name, role, date_joined, city, address, backup_phone,
                 password, email, forgot_password=0):
        self.id_number = id_number
        self.phone_number = phone_number
        self.first_name = first_name
        self.last_name = last_name
        self.role = role
        self.date_joined = date_joined
        self.city = city
        self.address = address
        self.backup_phone = backup_phone
        self.password = password
        self.email = email
        self.forgot_password = forgot_password

    def get_id(self):
        return self.id_number

    def is_admin(self):
        return True if self.role == "admin" else False


def check_role():
    if current_user.is_anonymous:
        user_role = "guest"
    else:
        user_role = current_user.role

    return user_role



def send_email(sender, app_password, to, subject, message_text, msg_type, attachment=None):

    # Create a secure connection to the Gmail SMTP server
    # with smtplib.SMTP('smtp.gmail.com', 587) as smtp_server:
    smtp_server = smtplib.SMTP('smtp.gmail.com', 587)

    smtp_server.starttls()

    # Log in to your Gmail account using the App Password
    smtp_server.login(sender, app_password)

    msg = MIMEMultipart()
    msg['From'] = sender
    msg['To'] = to
    msg['Subject'] = subject
    msg.attach(MIMEText(message_text, msg_type))

    # If there's an attachment, add it to the email
    if attachment:
        with open(attachment, 'rb') as f:
            part = MIMEBase('application', 'octet-stream')
            part.set_payload(f.read())
            encoders.encode_base64(part)
            part.add_header(
                'Content-Disposition',
                f'attachment; filename={os.path.basename(f.name)}'
            )
            msg.attach(part)

    # send email
    smtp_server.send_message(msg)

    smtp_server.quit()


def send_error(e, subject):
    send_email(WEBSITE_EMAIL, GMAIL_PASS, DEV_EMAIL, subject, str(e), "plain")
    

# converting cart_items from Orders SQL table from string to dictionary to use it in creating orders page
def convert_str_to_dic(string: str) -> dict:
    keys = []
    values = []
    tmp = string[1:-1].split(":")
    ind = -1
    for i, x in enumerate(tmp):
        last_one = True
        if i == 0:
            keys.append(x[1:-1])
        elif i != len(tmp) - 1:
            ind = x.rindex(",")
            keys.append(x[ind + 1:].strip()[1:-1])
            last_one = False

        if i != 0:
            if last_one:
                value = x[:-1].strip().replace("\'", "")
            else:
                value = x[:ind].strip()[1:-1].replace("\'", "")
            item = []
            value = value[1:] if value[0] == "(" else value
            indx = value.index(",")
            tup = value[:indx].strip(), value[indx + 1:].strip()
            for j, v in enumerate(tup[1][1:-1].split(",")):
                if j == 0 or j == 5:
                    item.append(int(v.strip()))
                else:
                    item.append(v.strip())

            value = int(tup[0]), tuple(item)
            values.append(value)

    dic = {keys[i]: values[i] for i in range(len(keys))}
    return dic


def update_last_backup_time_in_file():
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    with open(CONFIG_FILE, "w") as file:
        file.write(now)


def get_last_backup_time_from_file():
    try:
        with open(CONFIG_FILE, "r") as file:
            data = file.read()
            return data
    except FileNotFoundError:
        return "-"