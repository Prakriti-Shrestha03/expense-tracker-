from flask import Flask, render_template, request, redirect, url_for, session
from sqlalchemy import create_engine, Column, String, Float, ForeignKey, DateTime, Integer
from sqlalchemy.orm import sessionmaker, declarative_base
import datetime
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
import csv
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import math

app = Flask(__name__)
app.secret_key = 'supersecretkey'

Base = declarative_base()

class Users(Base):
    __tablename__ = "users"
    email = Column(String, nullable=False)
    username = Column(String, primary_key=True)
    password = Column(String, nullable=False)

class User_Expenses(Base):
    __tablename__ = 'user_expenses'
    userid = Column(Integer, primary_key=True)
    username = Column(String, ForeignKey("users.username"), nullable=False)
    budget = Column(Float)
    transport = Column(Float)
    education = Column(Float)
    food = Column(Float)
    utility = Column(Float)
    misc = Column(Float)
    bud_transport = Column(Float)
    bud_education = Column(Float)
    bud_food = Column(Float)
    bud_utility = Column(Float)
    bud_misc = Column(Float)
    total_saving = Column(Float)
    datetime = Column(DateTime)
    saving_goal = Column(Float)

engine = create_engine('sqlite:///user.db')
Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)
session_db = Session()

def send_alert(usernames):
    user = session_db.query(Users).filter(Users.username == usernames).first()
    sender_email = ""
    receiver_email = user.email
    password = ""  

    message = MIMEMultipart()
    message["From"] = sender_email
    message["To"] = receiver_email
    message["Subject"] = "Warning!!!!"

    body = "You have spent more than your budget this month."
    message.attach(MIMEText(body, "plain"))

    try:
        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls()
            server.login(sender_email, password)
            server.sendmail(sender_email, receiver_email, message.as_string())
        print("Email sent successfully")
    except Exception as e:
        print(f"Error: {e}")

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        email = request.form['email']
        username = request.form['username']
        password = request.form['password']

        existing_user = session_db.query(Users).filter(Users.username == username).first()
        if existing_user:
            return "Username already taken. Try again."

        user = Users(email=email, username=username, password=password)
        session_db.add(user)
        session_db.commit()

        user_expenses = User_Expenses(
            username=username, 
            budget=0.0, 
            transport=0.0, 
            education=0.0, 
            food=0.0, 
            utility=0.0, 
            misc=0.0, 
            total_saving=0.0, 
            saving_goal=0.0, 
            bud_transport=0.0, 
            bud_education=0.0, 
            bud_food=0.0, 
            bud_utility=0.0, 
            bud_misc=0.0,
            datetime=datetime.datetime.now()
        )
        session_db.add(user_expenses)
        session_db.commit()

        return redirect(url_for('login'))

    return render_template('signup.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        user = session_db.query(Users).filter(Users.username == username, Users.password == password).first()
        if user:
            session['username'] = username  # Store username in session
            return redirect(url_for('user_dashboard'))
        else:
            return "Invalid credentials. Try again."

    return render_template('login.html')

@app.route('/dashboard')
def user_dashboard():
    username = session.get('username')
    if not username:
        return redirect(url_for('login'))  

    last_expense = session_db.query(User_Expenses).filter(User_Expenses.username == username).order_by(User_Expenses.userid.desc()).first()

    if last_expense:
        for field in ['transport', 'education', 'food', 'utility', 'misc',
                    'bud_transport', 'bud_education', 'bud_food', 'bud_utility', 'bud_misc',
                    'total_saving', 'saving_goal']:
            value = getattr(last_expense, field)
            if not is_valid_number(value):
                setattr(last_expense, field, 0.0)
    if (last_expense.bud_transport==0.0 and last_expense.bud_education==0.0 and  last_expense.bud_food==0.0 and last_expense.bud_utility==0.0 and  last_expense.bud_misc==0.0):
        return redirect(url_for('budgeting'))

    if last_expense.transport > last_expense.bud_transport or last_expense.education > last_expense.bud_education or last_expense.food > last_expense.bud_food or last_expense.utility > last_expense.bud_utility or last_expense.misc > last_expense.bud_misc:
        send_alert(username)
    
    if not (last_expense.transport==0.0 and last_expense.education==0.0 and  last_expense.food==0.0 and
              last_expense.utility==0.0 and  last_expense.misc==0.0):
        pie_chart_filename = generate_pie_chart(last_expense)
        bar_chart_filename = generate_bar_chart(last_expense)
    else:
        return redirect(url_for('add_expense'))

    return render_template('user_dashboard.html', 
                           last_expense=last_expense, 
                           pie_chart_filename=pie_chart_filename, 
                           bar_chart_filename=bar_chart_filename)

def is_valid_number(value):
    """Check if a value is a valid number (not NaN, None, or non-numeric)."""
    if value is None:
        return False
    try:
        return not math.isnan(float(value))
    except (ValueError, TypeError):
        return False

def generate_pie_chart(last_expense):
    labels = ["Transport", "Education", "Food", "Utility", "Miscellaneous"]
    values = [last_expense.transport, last_expense.education, last_expense.food, 
              last_expense.utility, last_expense.misc]

    plt.switch_backend('Agg') 
    fig, ax = plt.subplots()
    ax.pie(values, labels=labels, autopct='%1.1f%%', startangle=90)
    ax.axis('equal') 

    pie_chart_filename = 'static/pie_chart.png'
    plt.savefig(pie_chart_filename)
    plt.close() 

    return pie_chart_filename

def generate_bar_chart(last_expense):
    labels = ["Transport", "Education", "Food", "Utility", "Miscellaneous"]
    values = [last_expense.transport, last_expense.education, last_expense.food, 
              last_expense.utility, last_expense.misc]

    plt.switch_backend('Agg') 
    fig, ax = plt.subplots()
    ax.bar(labels, values)
    ax.set_ylabel('Amount')
    ax.set_title('Expense Breakdown')

    bar_chart_filename = 'static/bar_chart.png'
    plt.savefig(bar_chart_filename)
    plt.close()  

    return bar_chart_filename

@app.route('/add_expense', methods=['GET', 'POST'])
def add_expense():
    username = session.get('username')
    if not username:
        return redirect(url_for('login'))

    if request.method == 'POST':
        category = request.form['category']
        amount = float(request.form['amount'])

        categories = ["Transport", "Education", "Food", "Utility", "Miscellaneous"]
        if category not in categories:
            return "Invalid category. Try again."

        last_expense = session_db.query(User_Expenses).filter(User_Expenses.username == username).order_by(User_Expenses.userid.desc()).first()
        if category == "Transport":
            last_expense.transport += amount
        elif category == "Education":
            last_expense.education += amount
        elif category == "Food":
            last_expense.food += amount
        elif category == "Utility":
            last_expense.utility += amount
        elif category == "Misc":
            last_expense.misc += amount

        last_expense.total_saving -= amount
        last_expense.datetime = datetime.datetime.now()
        session_db.add(last_expense)
        session_db.commit()

        return redirect(url_for('user_dashboard'))

    return render_template('add_expense.html')

@app.route('/delete_expense', methods=['GET', 'POST'])
def delete_expense():
    username = session.get('username')
    if not username:
        return redirect(url_for('login'))

    if request.method == 'POST':
        category = request.form['category']
        amount = float(request.form['amount'])

        categories = ["Transport", "Education", "Food", "Utility", "Miscellaneous"]
        if category not in categories:
            return "Invalid category. Try again."

        last_expense = session_db.query(User_Expenses).filter(User_Expenses.username == username).order_by(User_Expenses.userid.desc()).first()
        if category == "transport":
            last_expense.transport -= amount
        elif category == "education":
            last_expense.education -= amount
        elif category == "food":
            last_expense.food -= amount
        elif category == "utility":
            last_expense.utility -= amount
        elif category == "misc":
            last_expense.misc -= amount

        last_expense.total_saving += amount
        last_expense.datetime = datetime.datetime.now()
        session_db.add(last_expense)
        session_db.commit()

        return redirect(url_for('user_dashboard'))

    return render_template('delete_expense.html')

@app.route('/budgeting', methods=['GET', 'POST'])
def budgeting():
    username = session.get('username')
    if not username:
        return redirect(url_for('login'))

    if request.method == 'POST':
        budget_transport = float(request.form['budget_transport'])
        budget_education = float(request.form['budget_education'])
        budget_food = float(request.form['budget_food'])
        budget_utility = float(request.form['budget_utility'])
        budget_misc = float(request.form['budget_misc'])
        saving_goal = float(request.form['saving_goal'])

        total_budget = budget_transport + budget_education + budget_food + budget_utility + budget_misc
        last_expense = session_db.query(User_Expenses).filter(User_Expenses.username == username).order_by(User_Expenses.userid.desc()).first()

        last_expense.bud_transport = budget_transport
        last_expense.bud_education = budget_education
        last_expense.bud_food = budget_food
        last_expense.bud_utility = budget_utility
        last_expense.bud_misc = budget_misc
        last_expense.saving_goal = saving_goal
        last_expense.total_saving = total_budget - saving_goal
        last_expense.budget = total_budget

        session_db.add(last_expense)
        session_db.commit()

        return redirect(url_for('user_dashboard'))

    return render_template('budgeting.html')

@app.route('/download')
def download():
    username = session.get('username')
    if not username:
        return redirect(url_for('login'))

    last_expense = session_db.query(User_Expenses).filter(User_Expenses.username == username).order_by(User_Expenses.userid.desc()).first()
    filename = f"expenses_on_{datetime.datetime.now().strftime('%m_%d_%Y')}.csv"
    filepath = os.path.join('downloads', filename)

    with open(filepath, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(["Username", "Transport", "Education", "Food", "Utility", "Misc", "Budget", "Total Savings", "Saving Goals"])
        writer.writerow([last_expense.username, last_expense.transport, last_expense.education, last_expense.food, last_expense.utility, last_expense.misc, last_expense.budget, last_expense.total_saving, last_expense.saving_goal])

    return render_template('download.html')  

if __name__ == '__main__':
    app.run(debug=True)
