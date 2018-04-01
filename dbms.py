
from flask import *
import MySQLdb
import requests
import sys
app = Flask(__name__)

conn = MySQLdb.connect(host = "localhost", user = "root", passwd = "root", db="dbms")
c = conn.cursor()
logged_in = False
name = ""
@app.route("/")
def hello():
    return render_template("index.html",logged_in=logged_in,name=name)
@app.route("/register")
def reg():
    return render_template("register.html",logged_in=logged_in,name=name)
@app.route("/add_user", methods=['GET','POST'])
def add():
    uemail = request.form["email"]
    upwd = request.form["password"]
    uname = request.form["name"]
    already_taken = False
    if request.method == 'POST':
        qu = "select count(email) from users where email='" + uemail + "'"
        c.execute(qu)
        cnt = int(c.fetchone()[0])
        if cnt > 0:

            return render_template("register.html",already_taken = True, logged_in = logged_in,name=name)
        else:
            c.execute("select count(*) from users")
            total_users = int(c.fetchone()[0])
            qu = "insert into users values (%s,%s,%s,%s)"
            c.execute(qu,(total_users+1,uname,uemail,upwd))
            conn.commit()
            return redirect("/")

@app.route("/login", methods=['GET','POST'])
def log():
    uemail = request.form["email"]
    upwd = request.form["password"]
    wrong_password = False
    wrong_email = False
    if request.method == 'POST':
        qu = "select count(email) from users where email = %s AND password = %s"
        c.execute(qu,(uemail,upwd))
        cnt = int(c.fetchone()[0])
        if cnt > 0:
            qu = "select name from users where email = %s AND password = %s "
            c.execute(qu,(uemail,upwd))
            session['username'] = c.fetchone()[0]
            global logged_in,name
            logged_in = True
            name = session['username']
            return render_template("index.html",logged_in = logged_in, name = name)
        else:
            return render_template("register.html", wrong_email = True, logged_in = logged_in,name=name)

@app.route("/myaccount", methods=['GET','POST'])
def myacc():
    return render_template("customer-account.html", logged_in = logged_in, name = name)

@app.route("/logout", methods=['GET','POST'])
def logout():
    global logged_in,name
    name = ""
    logged_in = False
    session.pop('username')
    return render_template("index.html",logged_in=logged_in,name=name)

app.secret_key = 'asd'
if __name__ == "__main__":
    app.run(debug=True, use_reloader=True)

