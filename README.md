# Motor Insurance Renewal Online Website
Introduction: [here](https://www.youtube.com/watch?v=oIk2hTPxFqs "here")
Insurance Renewal Online Website is the website for customers to renew their insurances every years without passing motor insurance agents or motor insurance companies

A number of small motor insurance agents have gotten used to manually contacting customers by asking them to renew insurance every year. This process is quite hard if agents have a large number of customers. However, agents can skip from the asking step to renewing their customers' insurances by this website because this website will do this role instead of agents. The website will ask customers whether they want to renew their insurance or not. If they accept, the website system will go to the payment page and when they finish checking out, the system will notify the agent to renew the customer's insurance.

In addition, besides renewing insurance, this website also has a role to show collected customers information in the form of a website  such as the list of vehicles  which customers are insured with agent renewal insurance history. By this way, customers will be able to see their information clearly. Moreover, it is really helpful to some customers who have a lot of vehicles because it's hard to remember what vehicles they are insured with this agent.


## Features
##### Customer side
- Renewing a couple insurances in a single payment
- Collecting information of vehicles and insurances in each year
- Showing history of renewal insurances
- Being able to editing own user information e.g. username, password or e-mail

##### Agent side
- Editing all information e.g.  user, vehicle and insurance informatoin
- Inserting new information e.g. new user's vehicle and renewal insurance
- Creating new user
- Notifiying agent for new user's online renewal

## Specification
- Python 3.9
- Flask 1.1.2
- Flask-Session 0.4.0
- Pip 22.0.4

##Database Scheme
```sh
CREATE TABLE "admins" (
	"id"	INTEGER NOT NULL,
	"username"	TEXT NOT NULL,
	"password"	TEXT NOT NULL,
	PRIMARY KEY("id" AUTOINCREMENT)
);
```
