import os
import stripe
from flask import *
from werkzeug.utils import secure_filename
import MySQLdb
import requests
import sys
import datetime
import sendgrid

def send_mail(receiver, email_template, subject):
    sg = sendgrid.SendGridAPIClient(apikey=os.environ.get('SENDGRID_API_KEY'))

    data = {
        "personalizations": [
            {
                "to": [
                    {
                        "email": receiver
                    }
                ],
                "subject": subject
            }
        ],
        "from": {
            "email": "hj.harshit007@gmail.com",
            "name": "Obaju"
        },
        "content": [
            {
                "type": "text/html",
                "value": email_template
            }
        ]
    }
    response = sg.client.mail.send.post(request_body=data)


app = Flask(__name__)

conn = MySQLdb.connect(host = "localhost", user = "root", passwd = "root", db="dbms")
c = conn.cursor()


wrong_email = False
already_taken = False
wrong = False

curr_photo = ""
payment_method=""
new_id = 0
@app.route("/")
def hello():
    return render_template("index.html", logged_in=session.get("logged_in", False), name=session.get("name",""))

@app.route("/404")  
def error():
    return render_template("404.html", logged_in=session.get("logged_in", False), name=session.get("name",""))

@app.route("/register")
def reg():
    if session.get("logged_in", False) ==  True:
        return redirect('/404')
    return render_template("register.html",logged_in=session.get("logged_in", False),name=session.get("name",""),already_taken=already_taken,wrong_email=wrong_email)
@app.route("/add_user", methods=['GET','POST'])
def add():
    uemail = request.form["email"]
    upwd = request.form["password"]
    session["name"] = request.form["name"]
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
            c.execute(qu,(total_users+1,session.get("name",""),uemail,upwd))
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
            session['name'] = c.fetchone()[0]
            qu = "select user_id from users where email = %s AND password = %s "
            c.execute(qu, (uemail, upwd))
            
            session["logged_in"] = True
            
            session["uid"] = c.fetchone()[0]
            return redirect("/")
        else:
            global wrong_email,already_taken
            wrong_email = True
            already_taken = False
            return redirect("/register")

@app.route("/myaccount", methods=['GET','POST'])
def myacc():
    if session["uid"] == 1:
        return redirect("/add_items")
    if session.get("logged_in", False) == False:
        return redirect("/404")
    qu = "select * from users where user_id=%s and name=%s"
    c.execute(qu,(session["uid"],session.get("name","")))
    data = c.fetchone()
    return render_template("customer-account.html", data = data, wrong = wrong, logged_in = session.get("logged_in", False), name = session.get("name",""))

@app.route("/logout", methods=['GET','POST'])
def logout():
    session.pop("uid", None)
    session.pop("name", None)
    session["logged_in"] = False
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
    c.execute(qu,(oldp,session["uid"]))
    cnt = int(c.fetchone()[0])
    if cnt > 0:
        qu = "update users set password=%s where user_id=%s and password=%s"
        c.execute(qu,(newp,session["uid"],oldp))
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
    session["name"] = request.form["fname"]
    uemail = request.form["email"]
    uaddress1 = request.form["address1"]
    uaddress2 = request.form["address2"]
    ucity = request.form["city"]
    ustate = request.form["state"]
    ucountry = request.form["country"]
    uzip = request.form["zip"]
    utelephone = request.form["telephone"]

    qu = "update users set name=%s, email=%s, address1=%s, address2=%s, city=%s, state=%s, country=%s, zip=%s, telephone=%s where user_id=%s"
    c.execute(qu,(session.get("name",""),uemail,uaddress1,uaddress2,ucity,ustate,ucountry,uzip,utelephone,session["uid"]))
    conn.commit()
    return redirect("\myaccount")

@app.route("/photos", methods=['GET','POST'])
def photos():
    qu = "select * from photos"
    c.execute(qu)
    photo = c.fetchall()
    return render_template("photos.html",logged_in=session.get("logged_in", False), name=session.get("name",""),photo=photo)

@app.route("/products", methods=['GET','POST'])
def products():
    if session.get("logged_in", False) == False:
        return redirect("/register")
    qu = "select * from photos,uploads where uploads.photo_id = photos.photo_id and uploads.user_id=%s"
    c.execute(qu,[session["uid"]])
    photo = c.fetchall()
    print photo
    return render_template("products.html", logged_in=session.get("logged_in", False), name=session.get("name",""),photo=photo)

@app.route("/add_items", methods=['GET','POST'])
def add_items():
    return render_template("add-items.html",logged_in=session.get("logged_in", False), name=session.get("name",""))

@app.route("/add_photo", methods=['GET','POST'])
def add_photo():
    qu = "insert into photos(name,link,base,from_user) values(%s,%s,%s,%s)"
    c.execute(qu,(request.form["photo_name"], request.form["photo_link"], int(request.form["photo_base"]), 0))
    conn.commit()
    return redirect("/add_items")

@app.route("/add_size", methods=['GET','POST'])
def add_size():
    qu = "insert into size_cost values(%s,%s)"
    c.execute(qu,(request.form["size"], float(request.form["multi"])))
    conn.commit()
    return redirect("/add_items")


app.config['UPLOAD_FOLDER'] = './static/uploads'

@app.route("/upload_photo", methods=['GET','POST'])
def upload():
    if request.method == 'POST':
        photo = request.files['file']
        filename = secure_filename(photo.filename)
        photo.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        qu = "insert into photos(name,link,base,from_user) values(%s,%s,%s,%s)"
        c.execute(qu, (photo.filename, "." + app.config['UPLOAD_FOLDER'] + "/" + filename , 150, 1))
        conn.commit()
        qu = "select photo_id from photos order by photo_id desc limit 1"
        c.execute(qu)
        x = int(c.fetchone()[0])
        qu = "insert into uploads(photo_id,user_id) values(%s,%s)"
        c.execute(qu, (x,session["uid"]))
        conn.commit()
        global curr_photo
        qu = "select * from photos order by photo_id desc limit 1"
        c.execute(qu)
        curr_photo = c.fetchone()
        print curr_photo
        return redirect("/products")

@app.route("/photo_go", methods=['GET','POST'])
def deta():
    global curr_photo
    curr_photo = (request.form["photo_things0"], request.form["photo_things1"], request.form["photo_things2"], request.form["photo_things3"])
    return redirect("/photo_detail/" + str(curr_photo[0]).strip())

@app.route("/photo_detail/<id>", methods=['GET','POST'])
def gogo(id):
    print "here"
    global curr_photo
    qu = "select * from photos where photo_id=%s"
    c.execute(qu,[id])
    curr_photo = c.fetchone()
    print curr_photo
    qu = "select * from size_cost order by multiplier"
    c.execute(qu)
    size_table = c.fetchall()
    qu = "select count(*) from size_cost order by multiplier"
    c.execute(qu)
    size_entries = int(c.fetchone()[0])
    size_dict = {}
    for size in size_table:
        size_dict[size[0]] = size[1]
    print size_dict
    return render_template("detail.html", logged_in=session.get("logged_in", False), name=session.get("name",""), curr_photo=curr_photo, size_table = size_table, size_dict = size_dict)

@app.route("/basket", methods=['GET','POST'])
def basket():
    if session.get("logged_in", False) == False:
        return redirect("/register")
    qu = "select *,C.quantity*C.cost from carts C,photos P where C.photo_id = P.photo_id && C.user_id = %s"
    c.execute(qu,[session["uid"]])
    cart = c.fetchall()
    cost = [int(x[2]) * int(x[4]) for x in cart]
    total_cost = sum(cost)
    return render_template("basket.html", logged_in=session.get("logged_in", False), name=session.get("name",""), cart=cart,cost=cost,total_cost=total_cost)

@app.route("/addbasket", methods=['GET','POST'])
def add_basket():
    if session.get("logged_in", False) == False:
        return redirect("/register")
    s_size = request.form["selected_size"].split('-')
    photo_id = curr_photo[0]
    quantity = request.form["quantity"]
    cost = float(s_size[1]) * curr_photo[3]
    size = s_size[0]
    qu = "insert into carts(user_id,photo_id,quantity,size,cost) values(%s,%s,%s,%s,%s)"
    c.execute(qu,(session["uid"],photo_id,quantity,size,cost))
    conn.commit()
    return redirect("/basket")

@app.route("/delete/<id>", methods=['GET','POST'])
def dele(id):
    qu = "delete from carts where user_id=%s and item_id=%s"
    c.execute(qu,(session["uid"],id))
    conn.commit()
    return redirect("/basket")

@app.route("/delete_upload/<id>", methods=['GET','POST'])
def deel(id):
    qu = "delete from uploads where photo_id=%s"
    c.execute(qu,[id])
    conn.commit()
    return redirect("/products")

@app.route("/checkout1", methods=['GET','POST'])
def check1():
    if session.get("logged_in", False) == False:
        return redirect("/register")
    qu = "select * from users where user_id=%s and name=%s"
    c.execute(qu, (session["uid"], session.get("name","")))
    data = c.fetchone()
    qu = "select *,C.quantity*C.cost from carts C,photos P where C.photo_id = P.photo_id && C.user_id = %s"
    c.execute(qu, [session["uid"]])
    cart = c.fetchall()
    cost = [int(x[2]) * int(x[4]) for x in cart]
    total_cost = sum(cost)
    return render_template("checkout1.html", logged_in=session.get("logged_in", False), name=session.get("name",""), data=data, total_cost=total_cost, ship=total_cost+50)

@app.route("/update_add", methods=['GET','POST'])
def update_add():
    session["name"] = request.form["fname"]
    uemail = request.form["email"]
    uaddress1 = request.form["address1"]
    uaddress2 = request.form["address2"]
    ucity = request.form["city"]
    ustate = request.form["state"]
    ucountry = request.form["country"]
    uzip = request.form["zip"]
    utelephone = request.form["telephone"]

    qu = "update users set name=%s, email=%s, address1=%s, address2=%s, city=%s, state=%s, country=%s, zip=%s, telephone=%s where user_id=%s"
    c.execute(qu, (session.get("name",""), uemail, uaddress1, uaddress2, ucity, ustate, ucountry, uzip, utelephone, session["uid"]))
    conn.commit()

    return redirect("/checkout2")

@app.route("/checkout2", methods=['GET','POST'])
def check2():
    if session.get("logged_in", False) == False:
        return redirect("/register")
    qu = "select *,C.quantity*C.cost from carts C,photos P where C.photo_id = P.photo_id && C.user_id = %s"
    c.execute(qu, [session["uid"]])
    cart = c.fetchall()
    cost = [int(x[2]) * int(x[4]) for x in cart]
    total_cost = sum(cost)
    return render_template("checkout2.html", logged_in=session.get("logged_in", False), name=session.get("name",""), total_cost=total_cost, ship=total_cost+50)

@app.route("/checkout3", methods=['GET','POST'])
def check3():
    if session.get("logged_in", False) == False:
        return redirect("/register")
    qu = "select *,C.quantity*C.cost from carts C,photos P where C.photo_id = P.photo_id && C.user_id = %s"
    c.execute(qu, [session["uid"]])
    cart = c.fetchall()
    cost = [int(x[2]) * int(x[4]) for x in cart]
    total_cost = sum(cost)
    return render_template("checkout3.html", logged_in=session.get("logged_in", False), name=session.get("name",""), total_cost=total_cost,ship=total_cost+50)

@app.route("/checkout4", methods=['GET','POST'])
def check4():
    if session.get("logged_in", False) == False:
        return redirect("/register")
    credit = request.form["payment"]
    global payment_method
    if credit == "payment3":
        payment_method = "cod"
    else:
        payment_method = "credit"

    qu = "select *,C.quantity*C.cost from carts C,photos P where C.photo_id = P.photo_id && C.user_id = %s"
    c.execute(qu, [session["uid"]])
    cart = c.fetchall()
    cost = [int(x[2]) * int(x[4]) for x in cart]
    total_cost = sum(cost)

    return render_template("checkout4.html", logged_in=session.get("logged_in", False), name=session.get("name",""), cart=cart, cost=cost, total_cost=total_cost, ship=total_cost+50)

@app.route("/add_order/<flag>", methods=['GET','POST'])
def add_order(flag):

    qu = "select *,C.quantity*C.cost from carts C,photos P where C.photo_id = P.photo_id && C.user_id = %s"
    c.execute(qu, [session["uid"]])
    cart = c.fetchall()
    cost = [int(x[2]) * int(x[4]) for x in cart]
    total_cost = sum(cost)
    if payment_method == "credit" and int(flag) == 1:
        return redirect("/trans/" + str(total_cost+50))
    qu = "select order_id from orders order by order_id desc limit 1"
    rc = c.execute(qu)
    if rc > 0:
        new_id = int(c.fetchone()[0]) + 1
    else:
        new_id = 1
    print new_id
    for item in cart:
        qu = "insert into orders(order_id,user_id,photo_id,quantity,size,cost) values(%s,%s,%s,%s,%s,%s)"
        c.execute(qu,(new_id,item[0],item[1],item[2],item[3],item[4]))
        conn.commit()

    now = datetime.datetime.now()
    date = str(now.year) + "-" + str(now.month) + "-" + str(now.day)
    print date
    qu = "insert into cust_order values(%s,%s,%s,%s,%s,%s,%s)"
    global new_id
    c.execute(qu,(session["uid"],new_id,total_cost+50,date,payment_method,"Order Pending",0))
    conn.commit()
    qu = "delete from carts where user_id=%s"
    c.execute(qu, [session["uid"]])
    conn.commit()
    return redirect("/orders")

stripe_keys = {
  'secret_key': "sk_test_P4FjgFhENhRiYP9AtCidgfhh",
  'publishable_key': "pk_test_vlpzVMhRsimDYWrAwqANR6wd"
}

stripe.api_key = stripe_keys['secret_key']

@app.route("/trans/<amount>", methods=['GET','POST'])
def trans(amount):
    return render_template('transaction.html', key=stripe_keys['publishable_key'],amount=int(amount)*100)

@app.route('/charge/<amount>', methods=['POST'])
def charge(amount):

    customer = stripe.Customer.create(
        email='customer@example.com',
        source=request.form['stripeToken']
    )

    charge = stripe.Charge.create(
        customer=customer.id,
        amount=amount,
        currency='USD',
        description='Flask Charge'
    )

    return render_template('charge.html', amount=int(amount))

@app.route("/orders", methods=['GET','POST'])
def orders():
    if session.get("logged_in", False) == False:
        return redirect("/register")
    if session.get("uid", False) == 1:
        return redirect("/post")
    qu = "select * from cust_order where user_id=%s"
    c.execute(qu,[session["uid"]])
    orders = c.fetchall()
    return render_template("customer-orders.html", logged_in=session.get("logged_in", False), name=session.get("name",""), orders=orders)

@app.route("/post", methods=['GET','POST'])
def req():
    if session.get("logged_in", False) == False:
        return redirect("/register")
    if session.get("uid", False) != 1:
        return redirect("/register")
    qu = "select * from cust_order order by flag"
    c.execute(qu)
    data = c.fetchall()
    requests = []
    for some in data:
        temp = []
        qu = "select email from users where user_id=%s"
        c.execute(qu, [some[0]])
        uemail = c.fetchone()[0]
        temp.append(some[1])
        temp.append(uemail)
        temp.append(some[5])
        requests.append(temp)
    return render_template("post.html", logged_in=session.get("logged_in", False), name=session.get("name",""),requests=requests)

@app.route("/approve_order/<id>", methods=['GET','POST'])
def approve(id):
    qu = "update cust_order set status='Order Placed', flag=1 where order_id=%s"
    c.execute(qu,[id])
    conn.commit()
    qu = "select user_id from cust_order where order_id=%s"
    c.execute(qu,[id])
    uid = int(c.fetchone()[0])
    qu = "select email from users where user_id=%s"
    c.execute(qu,[uid])
    email = c.fetchone()[0]
    send_mail(str(email),"Your Order Has been Placed", "Order #" + str(id) + " Placed")
    return redirect("/post")


@app.route("/cancel_order/<id>", methods=['GET','POST'])
def cancel(id):
    qu = "update cust_order set status='Order Cancelled', flag=1 where order_id=%s"
    c.execute(qu,[id])
    conn.commit()
    qu = "select user_id from cust_order where order_id=%s"
    c.execute(qu, [id])
    uid = int(c.fetchone()[0])
    qu = "select email from users where user_id=%s"
    c.execute(qu, [uid])
    email = c.fetchone()[0]
    send_mail(str(email), "Your Order Has been Cancelled", "Order #" + str(id) + " Placed")
    return redirect("/post")

@app.route("/view_order/<id>", methods=['GET','POST'])
def viewe(id):
    qu="select * from orders join photos on orders.photo_id = photos.photo_id where order_id=%s and user_id=%s"
    c.execute(qu,(id,session.get("uid")))
    view_data = c.fetchall()
    qu = "select * from cust_order where order_id=%s"
    c.execute(qu, [id])
    new_data = c.fetchone()
    return render_template("customer-order.html", logged_in=session.get("logged_in", False),name=session.get("name",""), view_data = view_data, new_data=new_data)


app.secret_key = 'asd'
if __name__ == "__main__":
    app.run(debug=True, use_reloader=True)

