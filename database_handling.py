import sqlite3
# import mysql.connector
import re


# connection = mysql.connector.connect(
# 	host="localhost",
# 	user="mohammadgh",
# 	password="0905MmCS*"
# )

def regex_check(s):
	return re.match(r'^[0-9]{10}$', s) is not None


def create_table():
	customers_table = """
	create table if not exists Customers(
		id_number integer primary key autoincrement,
		phone_number char(10),
		first_name nvarchar(15),
		last_name nvarchar(15),
		role nvarchar(10),
		date_joined nvarchar(20),
		city nvarchar(20),
		address nvarchar(50),
		backup_phone nvarchar(10),
		password nvarchar(80)
	 )
	"""
	# check (length(phone_number) == 10),
	# check (phone_number not like backup_phone),
	# check (phone_number GLOB '[0-9][0-9][0-9][0-9][0-9][0-9][0-9][0-9][0-9][0-9]')
	# foreign key (phone_number) references Addresses(user_phone),
	# check (length(password) >= 8 and length(password) <= 20)
	# check (password like '^.{8,20}$')
	
	orders_table = """
	create table if not exists Orders(
		id_number integer primary key autoincrement,
		customer_id integer,
		cart_item_id integer,
		customer_first_name nvarchar(20),
		customer_last_name nvarchar(20),
		role nvarchar(10),
		city nvarchar(20),
		address nvarchar(50),
		email varchar(100),
		backup_phone nvarchar(10),
		customer_phone_number char(10),
		order_date datetime,
		total_amount int,
		status nvarchar(100),
		cart_items varchar(150)
	)
	"""
	
	# ,
	# 		fk_customer_id_number foreign key integer references Customers(id_number),
	# 		fk_product_id_number foreign key integer references Products(id_number)
	
	cart_items_table = """
	create table if not exists Cart_Items (
		product_id integer primary key,
		order_id integer,
		amount int,
		total_price int,
		foreign key (product_id) references Products(id_number),
		foreign key (order_id) references Orders(id_number)
	)
	"""
	
	guests_table = """
	create table if not exists Guests(
		id_number integer primary key autoincrement,
		phone_number char(10),
		first_name nvarchar(15),
		last_name nvarchar(15),
		role nvarchar(10),
		date_joined nvarchar(20),
		city nvarchar(20),
		address nvarchar(50),
		backup_phone nvarchar(10)
	)
	"""
	
	#  todo - add list of addresses or not?
	addresses_table = """
	create table if not exists Addresses(
		user_phone nvarchar(10) primary key,
		phone_number char(10),
		first_name nvarchar(15),
		last_name nvarchar(15),
		city nvarchar(20),
		address nvarchar(50),
		zip nvarchar(7),
		default int
	)
	"""
	
	products_table = """
	create table if not exists Products(
		id_number integer primary key autoincrement,
		name nvarchar(50),
		type nvarchar(20),
		img_path nvarchar(100),
		price nvarchar(10),
		items_left int default 0,
		description nvarchar(200),
		publish_year nvarchar(20),
		author_name nvarchar(20),
		categories nvarchar(100)
	)
	"""
	# phone = '^[0-9]{10}$'
	with sqlite3.connect(database="Shopping.db") as connection:
		cursor = connection.cursor()
		try:
			# cursor.execute(customers_table)
			# cursor.execute(guests_table)
			cursor.execute(orders_table)
			# cursor.execute(cart_items_table)
			
			# cursor.execute(products_table)
			connection.commit()
		except Exception as e:
			print(e)
			connection.rollback()

	
import csv


def csv_to_html(csv_file_path, html_file_path):
	# Read CSV file
	with open(csv_file_path, 'r') as csv_file:
		csv_reader = csv.reader(csv_file)
		data = list(csv_reader)
	
	# Generate HTML
	html_content = '<ul>\n'
	for row in data:
		html_content += f'  <li>{", ".join(row)}</li>\n'
	html_content += '</ul>'
	
	# Write HTML to file
	with open(html_file_path, 'w') as html_file:
		html_file.write(html_content)


if __name__ == "__main__":
	# csv_file_path = 'cities.csv'  # Replace with your CSV file path
	# html_file_path = 'output.html'  # Replace with your desired HTML output file path
	#
	# csv_to_html(csv_file_path, html_file_path)
	create_table()
	# lst = []
	# with open('option_tags.txt', "r", encoding="utf8") as f:
	# 	lst = [x.strip() for x in f.readlines()]
	#
	# print(len(lst))
	#
	# with open('to_translate.txt', "r", encoding="utf8") as f:
	# 	lst1 = [x.strip() for x in f.readlines()]
	# print(len(lst1))
	#
	# for i in range(len(lst1)):
	# 	lst[i] = lst[i].replace("<option", f"<option value=\"{lst1[i]}\"")
	#
	# with open("tags.txt", "w") as f:
	# 	for x in lst:
	# 		f.write(x + "\n")
	#
	# print(lst)

	