
from flask import *
import MySQLdb
import requests
import sys
app = Flask(__name__)

conn = MySQLdb.connect(host = "localhost", user = "root", passwd = "root", db="dbms")
c = conn.cursor()
logged_in = False
name = ""
wrong_email = False
already_taken = False
wrong = False
uid = ""
@app.route("/")
def hello():
    return render_template("index.html",logged_in=logged_in,name=name)

@app.route("/404")
def error():
    return render_template("404.html",logged_in=logged_in,name=name)

@app.route("/register")
def reg():
    if logged_in ==  True:
        return redirect('/404')
    return render_template("register.html",logged_in=logged_in,name=name,already_taken=already_taken,wrong_email=wrong_email)
@app.route("/add_user", methods=['GET','POST'])
def add():
    uemail = request.form["email"]
    upwd = request.form["password"]
    uname = request.form["name"]
    if request.method == 'POST':
        qu = "select count(email) from users where email='" + uemail + "'"
        c.execute(qu)
        cnt = int(c.fetchone()[0])
        if cnt > 0:
            global already_taken,wrong_email
            already_taken = True
            wrong_email = False
            return redirect("/register")
        else:
            c.execute("select count(*) from users")
            total_users = int(c.fetchone()[0])
            qu = "insert into users(user_id,name,email,password) values (%s,%s,%s,%s)"
            c.execute(qu,(total_users+1,uname,uemail,upwd))
            conn.commit()
            return redirect("/")

@app.route("/login", methods=['GET','POST'])
def log():
    uemail = request.form["email"]
    upwd = request.form["password"]
    if request.method == 'POST':
        qu = "select count(email) from users where email = %s AND password = %s"
        c.execute(qu,(uemail,upwd))
        cnt = int(c.fetchone()[0])
        if cnt > 0:
            qu = "select name from users where email = %s AND password = %s "
            c.execute(qu,(uemail,upwd))
            session['username'] = c.fetchone()[0]
            qu = "select user_id from users where email = %s AND password = %s "
            c.execute(qu, (uemail, upwd))
            global logged_in,name,uid
            logged_in = True
            name = session['username']
            uid = c.fetchone()[0]
            return redirect("/")
        else:
            global wrong_email,already_taken
            wrong_email = True
            already_taken = False
            return redirect("/register")

@app.route("/myaccount", methods=['GET','POST'])
def myacc():
    if logged_in == False:
        return redirect("/404")
    qu = "select * from users where user_id=%s and name=%s"
    c.execute(qu,(uid,name))
    data = c.fetchone()
    return render_template("customer-account.html", data = data, wrong = wrong, logged_in = logged_in, name = name)

@app.route("/logout", methods=['GET','POST'])
def logout():
    global logged_in,name,uid
    name = ""
    uid = ""
    logged_in = False
    session.pop('username')
    return redirect("/")

@app.route("/change_password", methods=['GET','POST'])
def cp():
    oldp = request.form["old_password"]
    newp = request.form["new_password"]
    rnewp = request.form["r_new_password"]
    if newp != rnewp:
        global wrong
        wrong = True
        return redirect("/myaccount")
    qu = "select count(*) from users where password=%s and user_id=%s"
    c.execute(qu,(oldp,uid))
    cnt = int(c.fetchone()[0])
    if cnt > 0:
        qu = "update users set password=%s where user_id=%s and password=%s"
        c.execute(qu,(newp,uid,oldp))
        global wrong
        wrong = False
        conn.commit()
        return redirect("/myaccount")
    else:
        global wrong
        wrong = True
        return redirect("/myaccount")

@app.route("/add_details", methods=['GET','POST'])
def add_details():
    uname = request.form["fname"]
    uemail = request.form["email"]
    uaddress1 = request.form["address1"]
    uaddress2 = request.form["address2"]
    ucity = request.form["city"]
    ustate = request.form["state"]
    ucountry = request.form["country"]
    uzip = request.form["zip"]
    utelephone = request.form["telephone"]

    qu = "update users set name=%s, email=%s, address1=%s, address2=%s, city=%s, state=%s, country=%s, zip=%s, telephone=%s where user_id=%s"
    c.execute(qu,(uname,uemail,uaddress1,uaddress2,ucity,ustate,ucountry,uzip,utelephone,uid))
    conn.commit()
    global name
    name = uname
    return redirect("\myaccount")

@app.route("/photos", methods=['GET','POST'])
def photos():
    return render_template("photos.html",logged_in=logged_in, name=name)

@app.route("/products", methods=['GET','POST'])
def products():
    return render_template("products.html",logged_in=logged_in, name=name)

app.secret_key = 'asd'
if __name__ == "__main__":
    app.run(debug=True, use_reloader=True)

