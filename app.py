import os
from flask import (
    Flask, flash, render_template,
    redirect, request, session, url_for)
from flask_pymongo import PyMongo
from bson.objectid import ObjectId
from werkzeug.security import generate_password_hash, check_password_hash
if os.path.exists("env.py"):
    import env 


app = Flask(__name__)


app.config["MONGO_DBNAME"] = os.environ.get("MONGO_DBNAME")
app.config["MONGO_URI"] = os.environ.get("MONGO_URI")
app.secret_key = os.environ.get("SECRET_KEY")

mongo = PyMongo(app)


#get sales function
@app.route("/")
@app.route("/get_sales")
def get_sales():
    sales = list(mongo.db.sales.find())
    return render_template("sales.html", sales=sales)


# search option
@app.route("/search", methods=["GET", "POST"])
def search():
    query = request.form.get("query")
    sales = list(mongo.db.sales.find({"$text": {"$search": query}}))
    return render_template("sales.html", sales=sales)


@app.route("/register", methods=["GET", "POST"])   
def register():
    if request.method == "POST":
        #check if username already exists
        existing_user = mongo.db.users.find_one(
            {"username": request.form.get("username").lower()})

        if existing_user:

            flash("Username already used")
            return redirect(url_for("register"))

        register = {
            "username": request.form.get("username").lower(),
            "password": generate_password_hash(request.form.get("password"))
        }
        mongo.db.users.insert_one(register)

        # put new user into session cookie
        session["user"] = request.form.get("username").lower()
        flash("Registration Successful")
        return redirect(url_for("dashboard", username=session["user"]))
    return render_template("register.html") 


#login function
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        # check if username exists in db
        existing_user = mongo.db.users.find_one(
            {"username": request.form.get("username").lower()})

        if existing_user:
            # ensure hashed password matches user input
            if check_password_hash(
                existing_user["password"], request.form.get("password")):
                    session["user"] = request.form.get("username").lower()
                    flash("Welcome, {}".format(
                        request.form.get("username")))
                    return redirect(url_for(
                        "dashboard", username=session["user"]))
            else:
                # invalid password match
                flash("Incorrect Username and/or Password")
                return redirect(url_for("login"))

        else:
            # username doesn't exist
            flash("Incorrect Username and/or Password")
            return redirect(url_for("login"))

    return render_template("login.html")


#dashboard function
@app.route("/dashboard/", methods=["GET", "POST"])
def dashboard():
    dash = mongo.db.dashboard_info.find_one({"username": session["user"]})
    if "user" not in session:
        return redirect(url_for("login"))
    form_errors = []
    # grab the session user's username from db
    username = mongo.db.users.find_one(
        {"username": session["user"]})["username"]

    if session["user"]:	
        return render_template("dashboard.html", dash=dash, username=username)	

    
    return redirect(url_for("login"))    


# logout function
@app.route("/logout")
def logout():
    # remove user from session cookies
    flash("You have been logged out")
    session.pop("user")
    return redirect(url_for("login"))


# create new sale function
@app.route("/new_sales", methods=["GET", "POST"])
def new_sales():
    if "user" not in session:
        return redirect(url_for("login"))
    form_errors = []
    if request.method == "POST":
        purchase_approval = "yes" if request.form.get("purchase_approval") else "no"
        sale = {
            "customer_name": request.form.get("customer_name"),
            "sale_amount": request.form.get("sale_amount"),
            "sale_description": request.form.get("sale_description"),
            "close_date": request.form.get("close_date"),
            "purchase_approval": purchase_approval,
            "created_by": session["user"]
        }
        if len(sale["customer_name"]) < 3 or len(sale["customer_name"]) > 200:
            form_errors.append("Customer name must be between 2 and 200 characters long.")

        # other validation checks like the if statement above
        if len(form_errors) == 0:
            # put the data in the db
            mongo.db.sales.insert_one(sale)
            flash("Congratulations! Sale successfully uploaded!")
            return redirect(url_for("dashboard"))

    return render_template("new_sales.html", form_errors=form_errors) 
       


# edit sale function
@app.route("/edit_sale/<sale_id>", methods = ["GET", "POST"])
def edit_sale(sale_id):
    if "user" not in session:
        return redirect(url_for("login"))
    if "sale.created_by" in session: 
        redirect(url_for("login"))
        flash("User not logged in")
    form_errors = []
    if request.method == "POST":
        purchase_approval = "Yes" if request.form.get("purchase_approval") else "No"
        submit = {
            "customer_name": request.form.get("customer_name"),
            "sale_amount": request.form.get("sale_amount"),
            "sale_description": request.form.get("sale_description"),
            "close_date": request.form.get("close_date"),
            "purchase_approval": purchase_approval,
            "created_by": session["user"]
        }
        mongo.db.sales.replace_one({"_id": ObjectId(sale_id)}, submit)
        flash("Congratulations! Sale successfully edited!")

    sale = mongo.db.sales.find_one({"_id": ObjectId(sale_id)})
    return render_template("edit_sale.html", sale=sale,)


# delete sale function
@app.route("/delete_sale/<sale_id>")
def delete_sale(sale_id):
    if "user" not in session:
        return redirect(url_for("login"))
    if "sale.created_by" in session: 
        redirect(url_for("login"))
        flash("User not logged in")
    form_errors = []
    mongo.db.sales.delete_many({"_id": ObjectId(sale_id)})
    flash("Sale Successfully Deleted")
    return redirect(url_for("get_sales"))


# get users function 
@app.route("/get_users")
def get_users():
    if "user" not in session:
        return redirect(url_for("login"))
    if "admin" in session: 
        redirect(url_for("login"))
        flash("User not logged in")
    form_errors = []
    users = list(mongo.db.users.find().sort("username"))
    return render_template("users.html", users=users)


# creaye new user function 
@app.route("/new_user", methods=["GET", "POST"])
def new_user():
    if "user" not in session:
        return redirect(url_for("login"))
    if "admin" not in session: 
        redirect(url_for("login"))
        flash("User not logged in")
    form_errors = []
    if request.method == "POST":
        existing_user = mongo.db.users.find_one(
            {"username": request.form.get("username").lower()})

        if existing_user:

            flash("Username already used")
            return redirect(url_for("register"))

        register = {
            "username": request.form.get("username").lower(),
            "password": generate_password_hash(request.form.get("password"))
        } 
        mongo.db.users.insert_one(register)
        flash("New User Added")
        return redirect(url_for('get_users'))

    return render_template("new_user.html")


#edit user function
@app.route("/edit_user/<user_id>", methods=["GET", "POST"])
def edit_user(user_id):
    if "admin"  in session:
        return redirect(url_for("login"))
    form_errors = []
    if request.method == "POST":
        submit = {
            "username": request.form.get("username"),
            "password": generate_password_hash(request.form.get("password"))
        }
        mongo.db.users.replace_one({"_id": ObjectId(user_id)}, submit)
        flash("User Successfully Updated!")
        return redirect(url_for("get_users"))

    user = mongo.db.users.find_one({"_id": ObjectId(user_id)})
    return render_template("edit_user.html", user=user)


# delete user function
@app.route("/delete_user/<user_id>")
def delete_user(user_id):
    if "admin"  in session:
        return redirect(url_for("login"))
    form_errors = []
    mongo.db.users.delete_one({"_id": ObjectId(user_id)})
    flash("User Successfully Deleted")
    return redirect(url_for("get_users"))



if __name__ == "__main__":
    app.run(host=os.environ.get("IP"),
            port=int(os.environ.get("PORT")),
            debug=False)

