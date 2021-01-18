from flask import Flask, render_template, redirect, session, url_for, flash, request
from data.db_session import db_auth
#from services.accounts_service import create_user, login_user, get_profile, update_profile
from services.accounts_service import *
import os

app = Flask(__name__) #create application
app.secret_key = os.urandom(24) 

graph = db_auth() #connect to neo4j


@app.route('/')
def index():
    return render_template("home/index.html")


@app.route('/accounts/register', methods=['GET'])
def register_get():
    return render_template("accounts/register.html")


@app.route('/accounts/register', methods=['POST'])
def register_post():
    # Get the form data from register.html
    username = request.form.get('username').strip()
    name = request.form.get('name')
    email = request.form.get('email').lower().strip()
    affiliation = request.form.get('affiliation').strip()
    title = request.form.get('title').strip()
    country = request.form.get('country').strip()
    password = request.form.get('password').strip()
    confirm = request.form.get('confirm').strip()

    # Check for blank fields in the registration form
    if not username or not name or not email or not affiliation or not title  or not country or not password or not confirm:
        flash("Please populate all the registration fields", "error")
        return render_template("accounts/register.html", username=username, name=name, email=email, affiliation=affiliation, title=title, country=country, password=password, confirm=confirm)

    # Check if password and confirm match
    if password != confirm:
        flash("Passwords do not match")
        return render_template("accounts/register.html", username=username, name=name, email=email, affiliation=affiliation, title=title, country=country)

    # Create the user
    user = create_user(username, name, email, affiliation, title, country, password)
    # Verify another user with the same email does not exist
    if not user:
        flash("A user with that email already exists.")
        return render_template("accounts/register.html", username=username, name=name, email=email, affiliation=affiliation, title=title, country=country)

    return redirect(url_for("profile_get"))


@app.route('/accounts/login', methods=['GET'])
def login_get():
    # Check if the user is already logged in.  if yes, redirect to profile page.
    if "usr" in session:
        return redirect(url_for("profile_get"))
    else:
        return render_template("accounts/login.html")


@app.route('/accounts/login', methods=['POST'])
def login_post():
    # Get the form data from login.html
    email = request.form['email']
    password = request.form['password']
    if not email or not password:
        return render_template("accounts/login.html", email=email, password=password)

    # Validate the user
    user = login_user(email, password)
    if not user:
        flash("No account for that email address or the password is incorrect", "error")
        return render_template("accounts/login.html", email=email)

    # Log in user and create a user session, redirect to user profile page.
    usr = request.form["email"]
    session["usr"] = usr
    return redirect(url_for("profile_get"))


@app.route('/accounts/profile', methods=['GET'])
def profile_get():
    # Make sure the user has an active session.  If not, redirect to the login page.
    if "usr" in session:
        usr = session["usr"]
        session["usr"] = usr
        user_profile = get_profile(usr)
        return render_template("accounts/index.html", user_profile=user_profile)
    else:
        return redirect(url_for("login_get"))


@app.route('/accounts/profile', methods=['POST'])
def profile_post():
    # Get the data from index.html
    username = request.form.get('username').strip()
    name = request.form.get('name')
    affiliation = request.form.get('affiliation').strip()
    title = request.form.get('title').strip()
    country = request.form.get('country').strip()
    # Make sure the user has an active session.  If not, redirect to the login page.
    if "usr" in session:
        usr = session["usr"]
        session["usr"] = usr
        user_profile = update_profile(usr, username, name, affiliation, title, country)
        user_profile = get_profile(usr)
        return render_template("accounts/index.html", user_profile=user_profile)
    else:
        return redirect(url_for("login_get"))

@app.route('/accounts/equipments', methods=['GET'])
def equipments_get():
    if "usr" in session:
        usr = session["usr"]
        session["usr"] = usr
        count = count_user_equipment(usr)
        if count == 0:
            flash("Don't have any equipment yet! Please add a equipment first", "error")
            return render_template("accounts/equipments.html", user_equipments = None)
        user_equipments = get_user_equipments(usr)
        return render_template("accounts/equipments.html", user_equipments = user_equipments)
    else:
        return redirect(url_for("login_get"))

@app.route('/accounts/equipments', methods=['POST'])
def equipments_post():
    # user equipment parameter
    Site = request.form.get('site').strip()
    Longitude = request.form.get('longitude').strip()
    Latitude = request.form.get('latitude').strip()
    Altitude = request.form.get('altitude').strip()
    tz = request.form.get('time_zone').strip()
    daylight = request.form.get('daylight_saving').strip()
    wv = request.form.get('water_vapor').strip()
    light_pollution = request.form.get('light_pollution').strip()
    
    #equipments parameter
    aperture = request.form.get('aperture').strip()
    Fov = request.form.get('fov').strip()
    pixel_scale = request.form.get('pixel').strip()
    tracking_accuracy = request.form.get('accuracy').strip()
    lim_magnitude = request.form.get('mag').strip()
    elevation_lim = request.form.get('deg').strip()
    mount_type = request.form.get('mount_type').strip()
    camera_type1 = request.form.get('camera_type1').strip()
    camera_type2 = request.form.get('camera_type2').strip()
    JohnsonB = request.form.get('JohnsonB').strip()
    JohnsonV = request.form.get('JohnsonV').strip()
    JohnsonR = request.form.get('JohnsonR').strip()
    SDSSu = request.form.get('SDSSu').strip()
    SDSSg = request.form.get('SDSSg').strip()
    SDSSr = request.form.get('SDSSr').strip()
    SDSSi = request.form.get('SDSSi').strip()
    SDSSz = request.form.get('SDSSz').strip()
    hid = request.form.get('uhaveid').strip() 
    if "usr" in session:
        usr = session["usr"]
        session["usr"] = usr
        if request.form.get('button') == 'update':
            print(hid)
            user_equipments = update_user_equipments(aperture,Fov,pixel_scale,tracking_accuracy,lim_magnitude,elevation_lim,mount_type,camera_type1,
            camera_type2,JohnsonB,JohnsonR,JohnsonV,SDSSu,SDSSg,SDSSr,SDSSi,SDSSz,
            usr,Site,Longitude,Latitude,Altitude,tz,daylight,wv,light_pollution,int(hid))
        if request.form.get('button') == 'add':
            equipments = create_equipments(aperture,Fov,pixel_scale,tracking_accuracy,lim_magnitude,elevation_lim,mount_type,camera_type1,camera_type2,JohnsonB,JohnsonR,JohnsonV,SDSSu,SDSSg,SDSSr,SDSSi,SDSSz)
            print(equipments.EID)
            user_equipments = create_user_equipments(usr,equipments.EID,Site,Longitude,Latitude,Altitude,tz,daylight,wv,light_pollution)
            #print('add')
        if request.form.get('button') == 'delete':
            delete_user_equipment(usr,int(hid))
        user_equipments = get_user_equipments(usr)
        return render_template("accounts/equipments.html", user_equipments = user_equipments)
    else:
        return redirect(url_for("login_get"))

@app.route('/projects/target', methods=['GET'])
def target_get():
    if "usr" in session:
        usr = session["usr"]
        session["usr"] = usr
        target = get_target()
        return render_template("projects/target.html", target = target)
    else:
        return redirect(url_for("login_get"))

@app.route('/projects/target', methods=['POST'])
def target_post():

    if "usr" in session:
        usr = session["usr"]
        session["usr"] = usr
        target = get_target()
        return render_template("projects/target.html", target = target)
    else:
        return redirect(url_for("login_get"))

@app.route('/projects/search', methods=['GET'])
def target_search_get():
    return render_template("projects/search_target.html")

@app.route('/projects/search', methods=['POST'])
def target_search_post():
    text = request.form.get('Search').strip()
    text = '(?i).*'+text+'.*'
    print(text)
    if request.form.get('button') == 'Search':
        target = search_target(text)
    return render_template("projects/search_target.html", target = target)


@app.route('/projects/project', methods=['GET'])
def project_get():

    if "usr" in session:
        usr = session["usr"]
        session["usr"] = usr
        projects = get_project(usr)
        return render_template("projects/project.html", projects = projects)
    else:
        return redirect(url_for("login_get"))

@app.route('/projects/project', methods=['POST'])
def project_post():

    if "usr" in session:
        usr = session["usr"]
        session["usr"] = usr
        if request.form.get('button') == 'Create':
            return redirect(url_for("project_create_get"))
        elif request.form.get('button') == 'Apply_history':
            print('history')
            return redirect(url_for("project_apply_history_get"))
        elif request.form.get('button') == 'Join':
            PID = request.form.get('PID').strip()
            flag = apply_project_status(usr,int(PID))
            if flag == 1:
                apply_project(usr,int(PID))
            #elif flag == 2:
                # handle already apply
            #elif flag == 3:
                #handle already join project
            #else:
                # handle error
        projects = get_project(usr)
        return render_template("projects/project.html", projects = projects)
    else:
        return redirect(url_for("login_get"))


@app.route('/projects/project_apply_history', methods=['GET'])
def project_apply_history_get():
    if "usr" in session:
        usr = session["usr"]
        session["usr"] = usr
        history = get_apply_history(usr)
        return render_template("projects/project_apply_history.html", history = history)
    else:
        return redirect(url_for("login_get"))

@app.route('/projects/project_create', methods=['GET'])
def project_create_get():
    if "usr" in session:
        usr = session["usr"]
        session["usr"] = usr
        projects = user_manage_projects_get(usr)
        return render_template("projects/project_create.html", projects = projects)
    else:
        return redirect(url_for("login_get"))

@app.route('/projects/project_create', methods=['POST'])
def project_create_post():
    
    title = request.form.get('title').strip()
    project_type = request.form.get('project_type').strip()
    description = request.form.get('description').strip()
    aperture_upper_limit = request.form.get('aperture_upper_limit').strip()
    aperture_lower_limit = request.form.get('aperture_lower_limit').strip()
    FoV_upper_limit = request.form.get('FoV_upper_limit').strip()
    FoV_lower_limit = request.form.get('FoV_lower_limit').strip()
    pixel_scale_upper_limit = request.form.get('pixel_scale_upper_limit').strip()
    pixel_scale_lower_limit = request.form.get('pixel_scale_lower_limit').strip()
    mount_type = request.form.get('mount_type').strip()
    camera_type1 = request.form.get('camera_type1').strip()
    camera_type2 = request.form.get('camera_type2').strip()
    JohnsonB = request.form.get('JohnsonB').strip()
    JohnsonV = request.form.get('JohnsonV').strip()
    JohnsonR = request.form.get('JohnsonR').strip()
    SDSSu = request.form.get('SDSSu').strip()
    SDSSg = request.form.get('SDSSg').strip()
    SDSSr = request.form.get('SDSSr').strip()
    SDSSi = request.form.get('SDSSi').strip()
    SDSSz = request.form.get('SDSSz').strip()
    PID = request.form.get('PID').strip()
    PI = request.form.get('PI').strip()
    umanageid = request.form.get('umanageid').strip()
    if "usr" in session:
        usr = session["usr"]
        session["usr"] = usr
        if request.form.get('button') == 'Create':
            print('create project')
            projects = create_project(usr,title,project_type,description,aperture_upper_limit,aperture_lower_limit,FoV_upper_limit,FoV_lower_limit,pixel_scale_upper_limit,pixel_scale_lower_limit,mount_type,camera_type1,camera_type2,JohnsonB,JohnsonR,JohnsonV,SDSSu,SDSSg,SDSSr,SDSSi,SDSSz)
        if request.form.get('button') == 'Update':
            projects = upadte_project(usr,int(PID),int(umanageid),title,project_type,description,aperture_upper_limit,aperture_lower_limit,FoV_upper_limit,FoV_lower_limit,pixel_scale_upper_limit,pixel_scale_lower_limit,mount_type,camera_type1,camera_type2,JohnsonB,JohnsonR,JohnsonV,SDSSu,SDSSg,SDSSr,SDSSi,SDSSz)
        if request.form.get('button') == 'Delete':
            delete_project(usr,int(PID),int(umanageid))
        projects = user_manage_projects_get(usr)
        return render_template("projects/project_create.html", projects = projects)
    else:
        return redirect(url_for("login_get"))

@app.route('/accounts/logout')
def logout():
    session.pop("usr", None)
    flash("You have successfully been logged out.", "info")
    return redirect(url_for("login_get"))


if __name__ == '__main__':
    app.run(debug=True)
