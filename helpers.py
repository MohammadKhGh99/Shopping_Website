import os
import smtplib

from flask_login import current_user, LoginManager, UserMixin
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart


cities = sorted(open("cities.txt", "r", encoding="utf8").readlines())
statuses = ["تم تأكيد الطلب", "تم تجهيز الطلب", "تم التوصيل"]

GMAIL_PASS = os.getenv("GMAIL_APP_PASSWORD")


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



def send_email(sender, app_password, to, subject, message_text, msg_type):
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

    # send email
    smtp_server.send_message(msg)

    smtp_server.quit()


def send_error(e, subject):
    send_email("mohammad.gh454@gmail.com", 
               GMAIL_PASS,
               "m7md.gh.99@hotmail.com",
               subject,
               str(e),
               "plain")
    

# converting cart_items from Orders SQL table from string to dictionary to use it in creating orders page
def convert_str_to_dic(string: str) -> dict:
    keys = []
    values = []
    # string = "{'10': ('2', (10, 'كتاب1', 'كتب', 'static/images/books/10/product2.png', '30', 12, 'asdfghjk', '2000', 'مش أنا', 'قصص أطفال')), '9': ('3', (9, 'كتاب', 'كتب', 'static/images/books/9/product1.png', '50', 5, 'asd', '2022', 'أنا', 'روايات'))}"
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