# Motor Insurance Renewal Website
Project Introduction video: [here](https://www.youtube.com/watch?v=oIk2hTPxFqs "here")

A multitude of smaller motor insurance agents have adopted the inefficient practice of individually contacting and asking customers to renew their insurance. As one can imagine this process does not scale well at all and limits the company’s growth potential. As this is clearly a problem that would create a lot of cost and inefficiency within a company and its operations, I have thus deemed it a worthy problem to tackle
 
This website acts as an intermediary between the customers and the insurance agents in order to automate the process  of insurance renewal. The website will notify and ask the customers to choose whether or not they would like to renew their insurance. If they so happen to choose to renew their insurance the website will direct them to the payment page in order to complete the transaction. As the transaction is completed the insurance agents using the website’s service will be notified of the renewal.
 
Apart from merely automating the insurance renewal process this website is also capable of collecting and displaying customer information such as the list of vehicles the customers have under the agent’s insurance and the customer’s renewal history. The customers will also be able access these quality of life functions.

## Features
##### Customer side:
- Renewing multiple insurance contracts in a single transaction
- Displays active insurance contracts
- Transaction history
- Edit personal information e.g. username, password and e-mail

##### Agent side:
- Edit contract information e.g. user, vehicle and insurance information
- Inserting new information e.g. new contracted vehicles and insurance renewals
- Creating new users
- Contract renewal notifications

##### To Do:
- The ability to import data from Excel or csv to the database directly
- Notifying users about their renewals via line
- Better UI
- Adding admin page

## Specification
- Python 3
- Pip 22.0.4
- SQLite
- Test on Chrome browser

## Setup
- Install Python 3 and Pip
- Download any SQLite IDE
- Download project
- Run command `pip install -r requirements.txt`
- Run `flask run`
- Open a website, login as admin and create a user account in the insertion page (for registering as admin, you have to do it via SQLite IDE only)
**Login page is used for both admins and users

## Database Scheme
```sh
CREATE TABLE "admins" (
	"id"	INTEGER NOT NULL,
	"username"	TEXT NOT NULL,
	"password"	TEXT NOT NULL,
	PRIMARY KEY("id" AUTOINCREMENT)
);
CREATE TABLE "users" (
	"id"	INTEGER NOT NULL,
	"code"	TEXT,
	"phone_number"	TEXT NOT NULL,
	"username"	TEXT NOT NULL,
	"hash_password"	TEXT NOT NULL,
	"e_mail"	TEXT DEFAULT '',
	"name_title"	TEXT DEFAULT '',
	"first_name"	TEXT NOT NULL,
	"last_name"	TEXT NOT NULL,
	"created_by"	INTEGER NOT NULL,
	"modified_by"	INTEGER NOT NULL,
	"created_date"	datetime,
	"modified_date"	datetime,
	PRIMARY KEY("id" AUTOINCREMENT)
);
CREATE TABLE "cars" (
	"id"	INTEGER NOT NULL,
	"users_id"	INTEGER NOT NULL,
	"brand"	TEXT,
	"model"	TEXT,
	"license_number"	TEXT,
	"modified_by"	INTEGER,
	"created_by"	INTEGER,
	"created_date"	datetime,
	"modified_date"	datetime,
	PRIMARY KEY("id" AUTOINCREMENT),
	FOREIGN KEY("users_id") REFERENCES "users"("id")
);
CREATE TABLE "insurance" (
	"id"	INTEGER NOT NULL,
	"car_id"	INTEGER NOT NULL,
	"type"	TEXT NOT NULL,
	"price"	FLOAT NOT NULL,
	"discount"	FLOAT DEFAULT 0,
	"sum_insure"	FLOAT DEFAULT '',
	"effective_date"	datetime NOT NULL,
	"status"	TEXT,
	"modified_by"	INTEGER,
	"created_by"	INTEGER,
	"created_date"	datetime,
	"modified_date"	datetime,
	PRIMARY KEY("id" AUTOINCREMENT)
);
CREATE TABLE "payment" (
	"id"	INTEGER NOT NULL,
	"tranfer_name"	TEXT NOT NULL,
	"payment_amount"	FLOAT NOT NULL,
	"bank_acount"	TEXT NOT NULL,
	"pay_date"	datetime,
	"confirm_payment"	TEXT,
	"modified_by"	INTEGER,
	"created_by"	TEXT,
	"created_date"	datetime,
	"modified_date"	datetime,
	PRIMARY KEY("id" AUTOINCREMENT)
);
CREATE TABLE "type_in_payment" (
	"id"	INTEGER NOT NULL,
	"payment_id"	INTEGER NOT NULL,
	"insurance_id"	INTEGER NOT NULL,
	FOREIGN KEY("insurance_id") REFERENCES "insurance"("id"),
	FOREIGN KEY("payment_id") REFERENCES "payment"("id") ON DELETE CASCADE,
	PRIMARY KEY("id" AUTOINCREMENT)
);
```
