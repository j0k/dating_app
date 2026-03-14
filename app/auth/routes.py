import logging
from datetime import date, datetime

from flask import redirect, render_template, request, url_for
from flask_login import current_user, login_user, logout_user
from flask_wtf import FlaskForm
from wtforms import PasswordField, SelectField, StringField
from wtforms.fields import DateField
from wtforms.validators import DataRequired, Email, EqualTo, Length, Optional

from app.auth import auth_bp
from app.db import get_db, oid
from app.models import User
from app.models.user import get_user_by_email, create_user
from app.models.profile import get_profile_by_user_id

logger = logging.getLogger(__name__)


class LoginForm(FlaskForm):
    email = StringField("Email", validators=[DataRequired(), Email()])
    password = PasswordField("Пароль", validators=[DataRequired()])


class RegisterForm(FlaskForm):
    email = StringField("Email", validators=[DataRequired(), Email()])
    password = PasswordField(
        "Пароль",
        validators=[
            DataRequired(),
            Length(min=6, message="Минимум 6 символов"),
            EqualTo("password_confirm", message="Пароли не совпадают"),
        ],
    )
    password_confirm = PasswordField("Повторите пароль", validators=[DataRequired()])
    name = StringField("Имя", validators=[DataRequired(), Length(max=100)])
    birth_date = DateField("Дата рождения", validators=[Optional()], format="%Y-%m-%d")
    gender = SelectField(
        "Пол",
        choices=[("", "—"), ("male", "Мужской"), ("female", "Женский"), ("other", "Другое")],
        validators=[Optional()],
    )


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("main.feed"))
    form = LoginForm()
    if form.validate_on_submit():
        from flask import current_app
        db = get_db(current_app.config)
        user_doc = get_user_by_email(db, form.email.data)
        if not user_doc:
            form.password.errors.append("Неверный email или пароль")
            return render_template("auth/login.html", form=form)
        user = User(user_doc, get_profile_by_user_id(db, user_doc["_id"]))
        if not user.check_password(form.password.data):
            form.password.errors.append("Неверный email или пароль")
            return render_template("auth/login.html", form=form)
        login_user(user, remember=True)
        logger.info("User logged in: %s", user.email)
        next_url = request.args.get("next") or url_for("main.feed")
        return redirect(next_url)
    return render_template("auth/login.html", form=form)


@auth_bp.route("/logout")
def logout():
    logout_user()
    return redirect(url_for("main.index"))


@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("main.feed"))
    form = RegisterForm()
    ref = request.args.get("ref") or (request.form.get("ref") if request.form else None)
    if form.validate_on_submit():
        from flask import current_app
        db = get_db(current_app.config)
        if get_user_by_email(db, form.email.data):
            form.email.errors.append("Такой email уже зарегистрирован")
            return render_template("auth/register.html", form=form, ref=ref)
        referred_by = None
        if ref:
            referrer = db.users.find_one({"invite_code": ref.strip()})
            if referrer:
                referred_by = referrer["_id"]
        password_hash = __import__("werkzeug.security", fromlist=["generate_password_hash"]).generate_password_hash(form.password.data)
        user_id = create_user(db, form.email.data, password_hash, referred_by=referred_by)
        profile_doc = {
            "user_id": user_id,
            "name": form.name.data[:100],
            "updated_at": datetime.utcnow(),
        }
        if form.birth_date.data:
            # BSON требует datetime, не date
            bd = form.birth_date.data
            profile_doc["birth_date"] = datetime(bd.year, bd.month, bd.day)
        if form.gender.data in ("male", "female", "other"):
            profile_doc["gender"] = form.gender.data
        db.profiles.insert_one(profile_doc)
        user_doc = db.users.find_one({"_id": user_id})
        profile_doc = get_profile_by_user_id(db, user_id)
        user = User(user_doc, profile_doc)
        login_user(user, remember=True)
        logger.info("User registered: %s", user.email)
        return redirect(url_for("main.feed"))
    return render_template("auth/register.html", form=form, ref=ref)
