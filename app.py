from asyncio.windows_events import NULL
from bdb import effective
from os import SEEK_CUR
from unittest import result
from flask import Flask, redirect, render_template, request, session, jsonify, make_response
from flask_session import Session
from werkzeug.security import check_password_hash, generate_password_hash
from werkzeug.utils import secure_filename
import sqlite3
from datetime import datetime, date
from dateutil.relativedelta import relativedelta, MO
import re
import json
import os
import shutil
import string
import random

db = sqlite3.connect('user_data.db', check_same_thread=False)
curdb = db.cursor()

app = Flask(__name__)
# login_manager = LoginManager()
# login_manager.init_app(app)

app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)


@app.route("/")
# @login_required
def index():

    if not session.get("user_id") and not session.get("admin_id"):
        return redirect("/login")
    if session.get("admin_id"):
        return redirect("/admin_main")

    username = curdb.execute(
        "SELECT name_title, first_name, last_name FROM users WHERE id= ?", (str(session["user_id"]),))
    username = username.fetchone()
    cars = curdb.execute("SELECT cars.brand, cars.model, cars.license_number, MAX(insurance.effective_date), cars.id FROM cars JOIN insurance ON insurance.car_id = cars.id WHERE users_id = ? AND status != '-1' GROUP BY cars.id",
                         (str(session["user_id"]),)).fetchall()
    return render_template("user_main.html", username=username, cars=cars)

@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    if request.method == "POST":
        row_admin = curdb.execute(
            "SELECT * FROM admins WHERE username = ?", (request.form.get("username"),)).fetchone()

        if row_admin != None or (row_admin != None and row_admin[2] == request.form.get("password")):
            session["admin_id"] = row_admin[0]
            return redirect("/admin_main")

        row_user = curdb.execute(
            "SELECT id, hash_password FROM users WHERE username = ?", (request.form.get("username"),)).fetchone()
        if row_user == None or (row_user != None and not(check_password_hash(str(row_user[1]), str(request.form.get("password"))))):
            return error("invalid username or password")

        session["user_id"] = row_user[0]
        return redirect("/")

    else:
        return render_template("login.html")

@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")

@app.route("/user_detail", methods=["GET", "POST"])
@app.route("/user_detail/<action>", methods=["GET", "POST"])
def user_detail(action=None):
    if request.method == "POST":
        today = date.today().strftime("%Y-%m-%d")
        if action == 'change_email':
            if not request.form.get("email"):
                return error("must provide email")
            email = str(request.form.get("email"))
            if not(re.search("@", email)) or not(re.search(".", email)) or re.search(" ", email):
                return error("gmail invalid")
            curdb.execute("UPDATE users SET e_mail = ?, modified_by = 0, modified_date = ? WHERE id = ?",
                          (email, today, str(session["user_id"])))
            db.commit()

        elif action == 'change_password':
            if (not request.form.get("password")) or (not request.form.get("new_password")) or (not request.form.get("password_confirmation")):
                return error("must provied password")
            old_password = str(request.form.get("password"))
            new_password = str(request.form.get("new_password"))
            confirmation = str(request.form.get("password_confirmation"))
            password = curdb.execute("SELECT hash_password FROM users WHERE id= ?", (str(
                session["user_id"]),)).fetchone()

            if old_password != password[0]:
                return error("password invalid")
            if new_password != confirmation:
                return error("new password is mismatch")
            if len(new_password) < 6:
                return error("new password too short")

            curdb.execute('UPDATE users SET hash_password = ?, modified_by = 0, modified_date = ? WHERE id = ?',
                          (new_password, today, str(session["user_id"])))
            db.commit()

    user = curdb.execute("SELECT first_name, last_name, phone_number,e_mail FROM users WHERE id = ?", (str(
        session["user_id"]),)).fetchone()
    return render_template("user_detail.html", user=user)


@app.route("/user_insurance/<car_id>")
def user_insurance(car_id):
    today = date.today().strftime("%Y-%m-%d")
    last_year = (date.today() - relativedelta(years=1)).strftime("%Y-%m-%d")
    next_year = (date.today() + relativedelta(years=1)).strftime("%Y-%m-%d")
    insurances = curdb.execute("SELECT type, sum_insure, price, effective_date, discount, car_id, id, status FROM insurance WHERE car_id = ? AND ((effective_date BETWEEN ? AND ? AND status != '-1') or (status = '-1' AND effective_date >= ?))",
                               (car_id, last_year, next_year, today)).fetchall()
    histories = curdb.execute(
        "SELECT id, status FROM insurance WHERE car_id = ?", (car_id,)).fetchall()
    name = curdb.execute(
        "SELECT brand, model, license_number ,id FROM cars WHERE id= ?", (car_id,)).fetchone()
    return render_template("user_insurance.html", insurances=insurances, name=name, histories=histories)


@app.route("/user_renew", methods=["GET", "POST"])
def user_renew():
    if request.method == "POST":
        today = date.today().strftime("%Y-%m-%d")
        tranfer_name = request.form.get('name')
        bank = request.form.get('bank')
        amount = request.form.get('amount')
        carts = request.form.get('carts')
        f = request.files.get('filename', None)
        ran = ''.join(random.choices(
            string.ascii_uppercase + string.digits, k=10))
        filename = str(ran) + '.jpg'
        f.save(os.path.join('static/storages/', filename))
        curdb.execute("INSERT INTO payment (tranfer_name, payment_amount, bank_acount, pay_date, confirm_payment, created_date, modified_date) VALUES (?,?,?,?,?,?,?)",
                      (tranfer_name, amount, bank, today, os.path.join('static/storages/', filename), today, today))
        db.commit()
        payment_id = curdb.execute("SELECT LAST_INSERT_ROWID()").fetchone()
        for row in json.loads(carts):
            curdb.execute("INSERT INTO type_in_payment (payment_id, insurance_id) VALUES (?,?)",
                          (payment_id[0], row['insurance_id']))
            curdb.execute(
                "UPDATE insurance SET status = '0' WHERE id = ?", (row['insurance_id'],))
            db.commit()

        return jsonify(result=True)

    username = curdb.execute("SELECT first_name, last_name, phone_number, e_mail FROM users WHERE id= ?", (str(
        session["user_id"]),)).fetchone()
    return render_template("user_renew.html", username=username)


@app.route("/user_history/<car_id>",)
def user_history(car_id):
    insurances = curdb.execute(
        "SELECT type, sum_insure, price, effective_date, discount, car_id, id, status FROM insurance WHERE car_id = ? AND status != '-1'", (car_id,)).fetchall()
    name = curdb.execute(
        "SELECT brand, model, license_number FROM cars WHERE id= ?", (car_id,)).fetchone()
    return render_template("user_history.html", insurances=insurances, name=name)


@app.route("/user_confirm", methods=["GET", "POST"])
def user_confirm():
    return render_template("user_confirm.html")


@app.route("/admin_main", methods=["GET", "POST"])
def admin_main():
    admin = curdb.execute(
        "SELECT * FROM admins WHERE id= ?", str(session["admin_id"])).fetchone()

    return render_template("admin_main.html", admin=admin)


@app.route("/search")
def search():
    q = request.args.get("q")
    category = request.args.get("category")
    if category == 'user':
        searching = curdb.execute(
            "SELECT DISTINCT users.id, users.first_name, users.last_name, users.phone_number,users.code FROM cars JOIN users ON cars.users_id = users.id where users.first_name LIKE ? OR users.last_name LIKE ? OR cars.license_number LIKE ?", ("%" + q + "%", "%" + q + "%", "%" + q + "%")).fetchall()

    elif category == 'car':
        searching = curdb.execute(
            "SELECT cars.id, cars.brand, cars.model, cars.license_number, users.first_name, users.last_name FROM cars INNER JOIN users ON cars.users_id = users.id where users.first_name LIKE ? OR users.last_name LIKE ? OR cars.license_number LIKE ?", ("%" + q + "%", "%" + q + "%", "%" + q + "%")).fetchall()

    else:
        searching = curdb.execute(
            "SELECT insurance.id, insurance.effective_date, insurance.type, users.first_name, users.last_name FROM insurance INNER JOIN cars ON insurance.car_id = cars.id INNER JOIN users ON cars.users_id = users.id where users.first_name LIKE ? OR users.last_name LIKE ? OR cars.license_number LIKE ?", ("%" + q + "%", "%" + q + "%", "%" + q + "%")).fetchall()

    return jsonify(searching)


@app.route("/catesortsearch/<method>/<category>")
def catesortsearch(method, category):
    q = request.args.get("q")
    if method == 'latest':
        if category == 'user':
            sorting = curdb.execute(
                "SELECT DISTINCT users.id, users.first_name, users.last_name, users.phone_number,users.code FROM cars JOIN users ON cars.users_id = users.id where users.first_name LIKE ? OR users.last_name LIKE ? OR cars.license_number LIKE ? ORDER BY users.id DESC", ("%" + q + "%", "%" + q + "%", "%" + q + "%")).fetchall()

        elif category == 'car':
            sorting = curdb.execute(
                "SELECT cars.id, cars.brand, cars.model, cars.license_number, users.first_name, users.last_name FROM cars INNER JOIN users ON cars.users_id = users.id where users.first_name LIKE ? OR users.last_name LIKE ? OR cars.license_number LIKE ? ORDER BY users.id DESC", ("%" + q + "%", "%" + q + "%", "%" + q + "%")).fetchall()

        else:
            sorting = curdb.execute(
                "SELECT insurance.id, insurance.effective_date, insurance.type, users.first_name, users.last_name FROM insurance INNER JOIN cars ON insurance.car_id = cars.id INNER JOIN users ON cars.users_id = users.id where users.first_name LIKE ? OR users.last_name LIKE ? OR cars.license_number LIKE ? ORDER BY users.id DESC", ("%" + q + "%", "%" + q + "%", "%" + q + "%")).fetchall()

    if method == 'name':
        if category == 'user':
            sorting = curdb.execute(
                "SELECT DISTINCT users.id, users.first_name, users.last_name, users.phone_number,users.code FROM cars JOIN users ON cars.users_id = users.id where users.first_name LIKE ? OR users.last_name LIKE ? OR cars.license_number LIKE ? ORDER BY users.first_name", ("%" + q + "%", "%" + q + "%", "%" + q + "%")).fetchall()

        elif category == 'car':
            sorting = curdb.execute(
                "SELECT cars.id, cars.brand, cars.model, cars.license_number, users.first_name, users.last_name FROM cars INNER JOIN users ON cars.users_id = users.id where users.first_name LIKE ? OR users.last_name LIKE ? OR cars.license_number LIKE ? ORDER BY users.first_name", ("%" + q + "%", "%" + q + "%", "%" + q + "%")).fetchall()

        else:
            sorting = curdb.execute(
                "SELECT insurance.id, insurance.effective_date, insurance.type, users.first_name, users.last_name FROM insurance INNER JOIN cars ON insurance.car_id = cars.id INNER JOIN users ON cars.users_id = users.id where users.first_name LIKE ? OR users.last_name LIKE ? OR cars.license_number LIKE ? ORDER BY users.first_name", ("%" + q + "%", "%" + q + "%", "%" + q + "%")).fetchall()

    if method == 'renew_date':
        if category == 'user':
            sorting = curdb.execute(
                "SELECT DISTINCT users.id, users.first_name, users.last_name, users.phone_number, users.code FROM insurance INNER JOIN cars ON insurance.car_id=cars.id JOIN users ON cars.users_id=users.id where users.first_name LIKE ? OR users.last_name LIKE ? OR cars.license_number LIKE ? ORDER BY insurance.effective_date", ("%" + q + "%", "%" + q + "%", "%" + q + "%")).fetchall()

        elif category == 'car':
            sorting = curdb.execute(
                "SELECT cars.id, cars.brand, cars.model, cars.license_number, users.first_name, users.last_name FROM insurance JOIN cars ON insurance.car_id=cars.id JOIN users ON cars.users_id=users.id where users.first_name LIKE ? OR users.last_name LIKE ? OR cars.license_number LIKE ? ORDER BY insurance.effective_date", ("%" + q + "%", "%" + q + "%", "%" + q + "%")).fetchall()

        else:
            sorting = curdb.execute(
                "SELECT insurance.id, insurance.effective_date, insurance.type, users.first_name, users.last_name FROM insurance INNER JOIN cars ON insurance.car_id=cars.id INNER JOIN users ON cars.users_id=users.id where users.first_name LIKE ? OR users.last_name LIKE ? OR cars.license_number LIKE ? ORDER BY insurance.effective_date", ("%" + q + "%", "%" + q + "%", "%" + q + "%")).fetchall()

    return jsonify(sorting)


@app.route("/user_edit", methods=["GET", "POST"])
@app.route("/user_edit/<type>/<action>", methods=["GET", "POST"])
def user_edit(type=None, action=None):
    user_id = request.args.get('user_id')
    user = curdb.execute(
        "SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
    cars = curdb.execute(
        "SELECT id FROM cars WHERE users_id = ?", (user_id,)).fetchall()
    pay_n = curdb.execute("SELECT DISTINCT payment.id FROM insurance JOIN type_in_payment ON insurance.id = type_in_payment.insurance_id JOIN payment ON type_in_payment.payment_id = payment.id JOIN cars ON cars.id = insurance.car_id JOIN users ON users.id = cars.users_id where users.id = ? ORDER BY payment.id DESC", (user_id,)).fetchall()
    insurances = curdb.execute(
        "SELECT insurance.id FROM insurance JOIN cars ON cars.id = insurance.car_id WHERE users_id = ?", (user_id,)).fetchall()
    type_in_payments = curdb.execute(
        "SELECT  type_in_payment.id FROM insurance JOIN type_in_payment ON insurance.id = type_in_payment.insurance_id JOIN payment ON type_in_payment.payment_id = payment.id JOIN cars ON cars.id = insurance.car_id JOIN users ON users.id = cars.users_id where users.id = ?", (user_id,)).fetchall()
    if request.method == "POST":
        today = date.today().strftime("%Y-%m-%d")
        if type == "user":
            if action == "add":
                edit_user = request.form
                code = edit_user.get("code")
                tel = edit_user.get("phone_number")
                username = edit_user.get("username")
                if edit_user.get("hash_password") == '':
                    password = edit_user.get("hash_password")
                else:
                    password = generate_password_hash(
                        edit_user.get("hash_password"))
                email = edit_user.get("e_mail")
                title = edit_user.get("name_title")
                first = edit_user.get("first_name")
                last = edit_user.get("last_name")
                value = (code, code,
                         tel, tel,
                         username, username,
                         password, password,
                         email, email,
                         title, title,
                         first, first,
                         last, last,
                         1,
                         today,
                         user_id)
                curdb.execute("UPDATE users SET code=CASE WHEN ? != '' THEN ? ELSE code END, phone_number=CASE WHEN ? != '' THEN ? ELSE phone_number END, username=CASE WHEN ? != '' THEN ? ELSE username END, hash_password=CASE WHEN ? != '' THEN ? ELSE hash_password END, e_mail=CASE WHEN ? != '' THEN ? ELSE e_mail END, name_title=CASE WHEN ? != '' THEN ? ELSE name_title END, first_name=CASE WHEN ? != '' THEN ? ELSE first_name END, last_name=CASE WHEN ? != '' THEN ? ELSE last_name END, modified_by = ?, modified_date = ? WHERE id = ?", value)
                db.commit()
                returning = '/user_edit?user_id=' + user_id
                return redirect(returning)

            elif action == "delete":
                curdb.execute("DELETE FROM payment WHERE payment.id IN (SELECT type_in_payment.payment_id FROM type_in_payment WHERE type_in_payment.insurance_id IN (SELECT insurance.id FROM insurance WHERE car_id IN (SELECT cars.id FROM cars WHERE users_id = ?)))", (user_id,))
                curdb.execute(
                    "DELETE FROM type_in_payment WHERE type_in_payment.insurance_id IN (SELECT insurance.id FROM insurance WHERE car_id IN (SELECT cars.id FROM cars WHERE users_id = ?))", (user_id,))
                curdb.execute(
                    "DELETE FROM insurance WHERE car_id IN (SELECT cars.id FROM cars WHERE users_id = ?)", (user_id,))
                curdb.execute(
                    "DELETE FROM cars WHERE users_id = ?", (user_id,))
                curdb.execute("DELETE FROM users WHERE id = ?", (user_id,))
                db.commit()
                return redirect('/admin_main')

        elif type == "payment":
            payment_id = request.args.get('payment_id')
            if action == "add":
                edit_payment = request.form
                tranfer_name = edit_payment.get('tranfer_name')
                bank_account = edit_payment.get('bank_account')
                payment_amount = edit_payment.get('payment_amount')
                pay_date = edit_payment.get('pay_date')
                f = request.files.get('confirm_payment', None)
                if f.filename != '':
                    ran = ''.join(random.choices(
                        string.ascii_uppercase + string.digits, k=10))
                    filename = str(ran) + '.jpg'
                    f.save(os.path.join('static/storages/', filename))
                    old_file = curdb.execute(
                        "SELECT confirm_payment FROM payment WHERE id = ?", (payment_id,)).fetchone()[0]
                    trash_old_file = 'static/storages/bin/' + old_file[16:]
                    shutil.move(old_file, trash_old_file)
                else:
                    filename = 'error'
                value = (tranfer_name, tranfer_name,
                         bank_account, bank_account,
                         payment_amount, payment_amount,
                         pay_date, pay_date,
                         str(f.filename), os.path.join(
                             'static/storages/', filename),
                         1,
                         today,
                         str(payment_id))
                curdb.execute("UPDATE payment SET tranfer_name = CASE WHEN ? != '' THEN ? ELSE tranfer_name END, bank_acount = CASE WHEN ? != '' THEN ? ELSE bank_acount END, payment_amount=CASE WHEN ? != '' THEN ? ELSE payment_amount END, pay_date = CASE WHEN ? != '' THEN ? ELSE pay_date END, confirm_payment = CASE WHEN ? != '' THEN ? ELSE confirm_payment END, modified_by = ?, modified_date = ? WHERE id = ?", value)
                db.commit()
                returning = '/user_edit?user_id=' + user_id
                return redirect(returning)

            elif action == "delete":
                old_file = curdb.execute(
                    "SELECT confirm_payment FROM payment WHERE id = ?", (payment_id,)).fetchone()[0]
                trash_old_file = 'static/storages/bin/' + old_file[16:]
                try:
                    shutil.move(old_file, trash_old_file)
                except:
                    pass
                curdb.execute(
                    "DELETE FROM type_in_payment WHERE payment_id = ?", (payment_id,))
                curdb.execute(
                    "DELETE FROM payment WHERE id = ?", (payment_id,))
                db.commit()
                redirect_value = ['user_edit?user_id=', user_id]
                ''.join(redirect_value)
                returning = '/user_edit?user_id=' + user_id
                return redirect(returning)

            elif action == "create":
                all = request.form
                insurelist = []
                for i in all:
                    if 'insurance' in i:
                        insurelist.append(all.get(i))
                tranfer_namec = all.get('tranfer_name')
                bank_accountc = all.get('bank_account')
                payment_amountc = all.get('payment_amount')
                pay_datec = all.get('pay_date')
                fc = request.files.get('confirm_payment', None)
                ran = ''.join(random.choices(
                    string.ascii_uppercase + string.digits, k=10))
                filenamec = str(ran) + '.jpg'
                fc.save(os.path.join('static/storages/', filenamec))
                curdb.execute("INSERT INTO payment (tranfer_name, payment_amount, bank_acount, pay_date, confirm_payment, created_by, created_date) VALUES (?,?,?,?,?,?,?)",
                              (tranfer_namec, payment_amountc, bank_accountc, pay_datec, os.path.join('static/storages/', filenamec), 1, today))
                db.commit()
                payment_id = curdb.execute(
                    "SELECT LAST_INSERT_ROWID()").fetchone()
                for i in insurelist:
                    curdb.execute(
                        "INSERT INTO type_in_payment (payment_id, insurance_id) VALUES (?,?)", (payment_id[0], i))
                    db.commit()
                returning = '/user_edit?user_id=' + user_id
                return redirect(returning)
        elif type == 'car':
            car_id = request.args.get('car_id')
            if action == 'add':
                edit_user = request.form
                brand = edit_user.get("brand")
                model = edit_user.get("model")
                license_number = edit_user.get("license_number")
                value = (brand, brand,
                         model, model,
                         license_number, license_number,
                         1,
                         today,
                         car_id)
                curdb.execute("UPDATE cars SET brand=CASE WHEN ? != '' THEN ? ELSE brand END, model=CASE WHEN ? != '' THEN ? ELSE model END, license_number=CASE WHEN ? != '' THEN ? ELSE license_number END, modified_by = ?, modified_date = ? WHERE id = ?", value)
                db.commit()
                returning = '/user_edit?user_id=' + user_id
                return redirect(returning)
            elif action == "delete":
                curdb.execute("DELETE FROM cars WHERE id = ?", (car_id,))
                curdb.execute(
                    "DELETE FROM insurance WHERE car_id = ?", (car_id,))
                db.commit()
                returning = '/user_edit?user_id=' + user_id
                return redirect(returning)
            elif action == "create":
                create_carins_car = json.loads(request.form.get('car'))
                create_carins_insurances = json.loads(
                    request.form.get('insurance'))
                curdb.execute("INSERT INTO cars (users_id, brand, model, license_number, created_by, created_date) VALUES (?,?,?,?,?,?)",
                              (user_id, create_carins_car['brand'], create_carins_car['model'], create_carins_car['license_number'], '1', today))
                db.commit()
                creation_car_id = curdb.execute(
                    "SELECT LAST_INSERT_ROWID()").fetchone()[0]
                for create_carins_insurance in create_carins_insurances:
                    curdb.execute("INSERT INTO insurance (car_id, type, price, discount, sum_insure, effective_date, status, created_by, created_date) VALUES (?,?,?,?,?,?,?,?,?)",
                                  (creation_car_id, create_carins_insurance['type'], create_carins_insurance['price'], create_carins_insurance['discount'], create_carins_insurance['sum_insure'], create_carins_insurance['effective_date'], create_carins_insurance['status'], '1', today))
                    db.commit()
                return jsonify(result=True)

        elif type == 'insurance':
            insurance_id = request.args.get('insurance_id')
            if action == 'add':
                edit_user = request.form
                typei = edit_user.get("type")
                effective_date = edit_user.get("effective_date")
                sum_insure = edit_user.get("sum_insure")
                price = edit_user.get("price")
                discount = edit_user.get("discount")
                status = edit_user.get("status")
                value = (typei, typei,
                         effective_date, effective_date,
                         sum_insure, sum_insure,
                         price, price,
                         discount, discount,
                         status, status,
                         1,
                         today,
                         insurance_id)
                curdb.execute("UPDATE insurance SET type=CASE WHEN ? != '' THEN ? ELSE type END, effective_date=CASE WHEN ? != '' THEN ? ELSE effective_date END, sum_insure=CASE WHEN ? != '' THEN ? ELSE sum_insure END, price=CASE WHEN ? != '' THEN ? ELSE price END, discount=CASE WHEN ? != '' THEN ? ELSE discount END, status=CASE WHEN ? != '' THEN ? ELSE status END, modified_by = ?, modified_date = ? WHERE id = ?", value)
                db.commit()
                returning = '/user_edit?user_id=' + user_id
                return redirect(returning)
            elif action == "delete":
                curdb.execute(
                    "DELETE FROM insurance WHERE id = ?", (insurance_id,))
                db.commit()
                returning = '/user_edit?user_id=' + user_id
                return redirect(returning)
            elif action == "create":
                carc_id = request.args.get('car_id')
                create_insurances = json.loads(request.form.get('form'))
                for create_insurance in create_insurances:
                    if create_insurance['discount'] == '':
                        inusurance_discount = NULL
                    else:
                        inusurance_discount = create_insurance['discount']
                    curdb.execute("INSERT INTO insurance (car_id, type, price, discount, sum_insure, effective_date, status, created_by, created_date) VALUES (?,?,?,?,?,?,?,?,?)",
                                  (carc_id, create_insurance['type'], create_insurance['price'], inusurance_discount, create_insurance['sum_insure'], create_insurance['effective_date'], create_insurance['status'], '1', today))
                    db.commit()
                return jsonify(result=True)

    carins = []
    payments = []
    for car in cars:
        carin = curdb.execute(
            "SELECT cars.id, cars.brand, cars.model, cars.license_number, insurance.type, insurance.effective_date, insurance.sum_insure, insurance.price, insurance.discount, insurance.created_by, insurance.created_date, insurance.modified_by, insurance.modified_date, insurance.id, cars.created_by, cars.created_date, cars.modified_by, cars.modified_date, cars.id, insurance.status FROM cars INNER JOIN insurance ON cars.id = insurance.car_id WHERE cars.id = ? ORDER BY insurance.id DESC", (car[0],)).fetchall()
        if len(carin) > 0:
            carins.append(carin)
    carlist = curdb.execute(
        "SELECT id, brand, model FROM cars WHERE users_id = ?", (user_id,)).fetchall()
    for id in pay_n:
        payment = []
        dcar = curdb.execute(
            "SELECT cars.brand, cars.model, cars.license_number, insurance.type, insurance.price, insurance.discount, insurance.effective_date, insurance.id FROM insurance JOIN type_in_payment ON insurance.id = type_in_payment.insurance_id JOIN payment ON type_in_payment.payment_id = payment.id JOIN cars ON cars.id = insurance.car_id JOIN users ON users.id = cars.users_id where users.id = ? AND payment.id = ?", (user_id, id[0])).fetchall()
        dpay = curdb.execute(
            "SELECT DISTINCT payment.tranfer_name, payment.bank_acount, payment.payment_amount, payment.pay_date, payment.confirm_payment, payment.id, payment.modified_by, payment.created_by, payment.created_date, payment.modified_date FROM insurance JOIN type_in_payment ON insurance.id = type_in_payment.insurance_id JOIN payment ON type_in_payment.payment_id = payment.id JOIN cars ON cars.id = insurance.car_id JOIN users ON users.id = cars.users_id where users.id = ? AND payment.id = ?", (user_id, id[0])).fetchall()
        if len(dcar) > 0:
            payment.append(dcar)
        if len(dpay) > 0:
            payment.append(dpay)
        if len(payment) > 0:
            payments.append(payment)

    return render_template("user_edit.html", user=user, carins=carins, payments=payments, carlist=carlist)


@app.route("/admin_create", methods=["GET", "POST"])
def admin_create():
    if request.method == "POST":
        today = date.today().strftime("%Y-%m-%d")
        form = json.loads(request.form.get('form'))
        user = form[0]
        curdb.execute("INSERT INTO users (name_title, first_name, last_name, code, phone_number, e_mail, username, hash_password, created_by, modified_by, created_date, modified_date) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
                      (user['name_title'], user['first_name'], user['last_name'], user['code'], user['phone_number'], user['e_mail'], user['username'], generate_password_hash(user['hash_password']), '1', '1', today, today))
        db.commit()
        user_id = str(curdb.execute(
            "SELECT LAST_INSERT_ROWID()").fetchone()[0])
        insurances = form[2]
        for insurance in insurances:
            car = insurance[0]
            curdb.execute("INSERT INTO cars (users_id, brand, model, license_number, created_by, modified_by, created_date, modified_date) VALUES (?,?,?,?,?,?,?,?)",
                          (user_id, car['brand'], car['model'], car['license_number'], '1', '1', today, today))
            db.commit()
            car_id = str(curdb.execute(
                "SELECT LAST_INSERT_ROWID()").fetchone()[0])
            insurance1 = insurance[1]
            if insurance1['discount'] == '':
                inusurance_discount = NULL
            else:
                inusurance_discount = insurance1['discount']
            curdb.execute("INSERT INTO insurance (car_id, type, price, discount, sum_insure, effective_date, status, created_by, created_date) VALUES (?,?,?,?,?,?,?,?,?)",
                          (car_id, insurance1['type'], insurance1['price'], inusurance_discount, insurance1['sum_insure'], insurance1['effective_date'], insurance1['status_'], '1', today))
            db.commit()

            if len(insurance) == 3:
                insurance2 = insurance[2]
                if insurance2['discount'] == '':
                    inusurance_discount2 = NULL
                else:
                    inusurance_discount2 = insurance2['discount']
                curdb.execute("INSERT INTO insurance (car_id, type, price, discount, sum_insure, effective_date, status, created_by, created_date) VALUES (?,?,?,?,?,?,?,?,?)",
                              (car_id, insurance2['type'], insurance2['price'], inusurance_discount2, insurance2['sum_insure'], insurance2['effective_date'], insurance1['status_'], '1', today))
                db.commit()
        return jsonify(user_id)
    return render_template("admin_create.html")


@app.route("/admin_notification", methods=["GET", "POST"])
def admin_notification():
    admin = curdb.execute(
        "SELECT * FROM admins WHERE id= ?", str(session["admin_id"])).fetchone()

    return render_template("admin_notification.html", admin=admin)


@app.route("/catesortsearch_notification/<method>/<category>")
def catesortsearch_notification(method, category):
    q = request.args.get("q")
    if method == 'latest':
        if category == 'insurance':
            sorting = curdb.execute(
                "SELECT DISTINCT payment.id, payment.pay_date, payment.payment_amount, users.first_name, users.last_name FROM payment INNER JOIN type_in_payment ON payment.id = type_in_payment.payment_id INNER JOIN insurance ON type_in_payment.insurance_id = insurance.id INNER JOIN cars ON insurance.car_id = cars.id INNER JOIN users ON cars.users_id = users.id where insurance.status = 0 AND (users.first_name LIKE ? OR users.last_name LIKE ? OR cars.license_number LIKE ?) ORDER BY users.id DESC",
                ("%" + q + "%", "%" + q + "%", "%" + q + "%")).fetchall()

    if method == 'name':
        if category == 'insurance':
            sorting = curdb.execute(
                "SELECT DISTINCT payment.id, payment.pay_date, payment.payment_amount, users.first_name, users.last_name FROM payment INNER JOIN type_in_payment ON payment.id = type_in_payment.payment_id INNER JOIN insurance ON type_in_payment.insurance_id = insurance.id INNER JOIN cars ON insurance.car_id = cars.id INNER JOIN users ON cars.users_id = users.id where insurance.status = 0 AND (users.first_name LIKE ? OR users.last_name LIKE ? OR cars.license_number LIKE ?) ORDER BY users.first_name",
                ("%" + q + "%", "%" + q + "%", "%" + q + "%")).fetchall()

    if method == 'renew_date':
        if category == 'insurance':
            sorting = curdb.execute(
                "SELECT DISTINCT payment.id, payment.pay_date, payment.payment_amount, users.first_name, users.last_name FROM payment INNER JOIN type_in_payment ON payment.id = type_in_payment.payment_id INNER JOIN insurance ON type_in_payment.insurance_id = insurance.id INNER JOIN cars ON insurance.car_id = cars.id INNER JOIN users ON cars.users_id = users.id where insurance.status = 0 AND (users.first_name LIKE ? OR users.last_name LIKE ? OR cars.license_number LIKE ?) ORDER BY payment.pay_date DESC",
                ("%" + q + "%", "%" + q + "%", "%" + q + "%")).fetchall()
    return jsonify(sorting)


@app.route("/admit/<id>", methods=["POST"])
def admit(id):
    insurance_ids = curdb.execute(
        "SELECT type_in_payment.insurance_id FROM type_in_payment JOIN payment ON payment.id = type_in_payment.payment_id WHERE payment.id = ?", (id,)).fetchone()
    print(insurance_ids)
    for insurance_id in insurance_ids:
        curdb.execute(
            "UPDATE insurance SET status = '1' WHERE id = ?", (insurance_id,))
    db.commit()
    return jsonify(result=True)


@app.route("/admin_renew_insurance/<id>")
def admin_renew_insurance(id):
    user_payment = curdb.execute(
        "SELECT DISTINCT users.first_name, users.last_name, users.phone_number, users.e_mail, payment.tranfer_name, payment.bank_acount, payment.payment_amount, payment.pay_date, payment.confirm_payment FROM payment INNER JOIN type_in_payment ON payment.id = type_in_payment.payment_id INNER JOIN insurance ON type_in_payment.insurance_id = insurance.id INNER JOIN cars ON insurance.car_id = cars.id INNER JOIN users ON cars.users_id = users.id WHERE payment.id = ?", (id,)).fetchone()
    return render_template("admin_renew_insurance.html", user_payment=user_payment, payment_id=id)


@app.route("/get_admin_renew/<id>")
def get_admin_renew(id):
    carins = curdb.execute("SELECT cars.id, insurance.id, cars.brand, cars.model, cars.license_number, insurance.type, insurance.sum_insure, insurance.effective_date, insurance.discount, insurance.price FROM payment INNER JOIN type_in_payment ON payment.id=type_in_payment.payment_id INNER JOIN insurance ON type_in_payment.insurance_id=insurance.id INNER JOIN cars ON insurance.car_id=cars.id WHERE payment.id=?", (id,)).fetchall()
    return jsonify(carins)


@app.route("/get_data_base")
def get_data_base():
    data_base = curdb.execute("SELECT users.id, cars.id, insurance.id, users.code, insurance.effective_date, users.name_title, users.first_name, users.last_name, cars.brand, cars.model, cars.license_number, insurance.type, insurance.sum_insure, insurance.price, insurance.discount, insurance.status FROM insurance INNER JOIN cars ON insurance.car_id=cars.id INNER JOIN users ON users.id = cars.users_id").fetchall()
    return jsonify(data_base)


def error(massage):

    return render_template("error.html", massage=massage)


def baht(value):
    """Format value as baht"""
    if value != '':
        value = int(value)
        return format(value, ",") + " ฿"


app.add_template_filter(baht)
 