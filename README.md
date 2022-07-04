# Motor Insurance Renewal Online Website
Introduction: [here](https://www.youtube.com/watch?v=oIk2hTPxFqs "here")
Insurance Renewal Online Website is the website for customers to renew their insurances every years without passing motor insurance agents or motor insurance companies

A number of small motor insurance agents have gotten used to manually contacting customers for asking them to renew insurance every year. This process is quite hard if agents have a large number of customers. However, agents can skip from the asking step to renewing their customers' insurances by this website because this website will do this role instead of agents. The website will ask customers whether they want to renew their insurance or not. If they accept, the website system will go to the payment page and when they finish checking out, the system will notify the agent to renew the customer's insurance.

In addition, besides renewing insurance, this website also has a role to show collected customers information in the form of a website  such as the list of vehicles  which customers are insured with agent renewal insurance history. By this way, customers will be able to see their information clearly. Moreover, it is really helpful to some customers who have a lot of vehicles because it's hard to remember what vehicles they are insured with this agent.


## Features
##### Customer side:
- Renew a couple insurances in a single payment
- Collect information of vehicles and insurances in each year
- Show history of renewal insurances
- Be able to editing own user information e.g. username, password or e-mail

##### Agent side:
- Edit all information e.g.  user, vehicle and insurance informatoin
- Insert new information e.g. new user's vehicle and renewal insurance
- Create new user
- Notifiy agent for new user's online renewal

#####To Do:
- Be able to import new data from Excel or csv to database directly
- Notify users when it's time for renewing thier insurance via Line
- Design new agent side's UI to be easy to use

## Specification
- Python 3.9
- Flask 1.1.2
- Flask-Session 0.4.0
- Pip 22.0.4
- SQLite

##Setup

##Database Scheme
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
