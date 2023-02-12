from flask import Blueprint, flash, render_template, redirect, url_for, request, flash
from flask_login import login_required, current_user
from flask_wtf.csrf import CSRFError
from . import app
from .models import User, Level
from .tools.upload import UploadFileForm, save_hero


views = Blueprint("views", __name__)


@views.route('/')
@views.route("/home")
def home():
    return render_template("home.html", user=current_user)


@views.route('/overview', methods=['GET', 'POST'])
@login_required
def overview():
    form = UploadFileForm()

    if form.validate_on_submit():
        # check if there is no real file uploaded
        if len(form.files.data) < 1 or (len(form.files.data) == 1 and form.files.data[0].filename == ''):
            flash(f"No file selected", category='error')
        else:
            invalid_files = []
            for file in form.files.data:
                if not save_hero(file):
                    invalid_files.append(file.filename)

            if len(invalid_files) > 0:
                invalid_file_names = ', '.join(invalid_files)
                flash(f'These files are not valid: {invalid_file_names}', category='error')
            else:
                flash("Files uploaded successfully", category='success')
        
   
    return render_template('overview.html', user=current_user, form=form)


@views.route('/account')
@login_required
def account():
    return render_template('account.html', user=current_user)


@views.route('/play')
@login_required
def play():
    return render_template("play.html", user=current_user)


@views.route('/admin-panel', methods=['GET', 'POST'])
@login_required
def admin_panel():
    if current_user.access_lvl == Level.ADMIN:
        if request.method == "GET":
            all_users = User.query.all()
        return render_template("admin-panel.html", user=current_user, all_users=all_users)
    else:
        return redirect(url_for("views.home"))


# Server request size to large
@app.errorhandler(413)
def too_large(e):
    flash("Upload size too large", category='error')
    return redirect(url_for("views.overview"))

# wrong url
@app.errorhandler(404)
def server_error(e):
    return "<h1>Page not found</h1>"

#internal server error
@app.errorhandler(500)
def server_error(e):
    return "<h1>Internal server error</h1><p>Please contact me with the steps you just made before this happened</p>"

@app.errorhandler(CSRFError)
def csrf_error(e):
    return f"Sorry, this request could not be executed.\nError: {e}"