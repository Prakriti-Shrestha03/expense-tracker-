from sqlalchemy import create_engine, Column, String, Float, ForeignKey, DateTime,Integer
from sqlalchemy.orm import sessionmaker, declarative_base
import datetime
import smtplib
import csv
import matplotlib.pyplot as plt
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import numpy as np

Base=declarative_base()

class Users(Base):
    __tablename__="users"
    email=Column(String,nullable=False)
    username=Column(String,primary_key=True)
    password=Column(String,nullable=False)

class User_Expenses(Base):
    __tablename__='user_expenses'
    userid=Column(Integer,primary_key=True)
    username=Column(String,ForeignKey("users.username"),nullable=False)
    budget=Column(Float)
    transport=Column(Float)
    education=Column(Float)
    food=Column(Float)
    utility=Column(Float)
    misc=Column(Float)
    bud_transport=Column(Float)
    bud_education=Column(Float)
    bud_food=Column(Float)
    bud_utility=Column(Float)
    bud_misc=Column(Float)
    total_saving=Column(Float)
    datetime=Column(DateTime)
    saving_goal=Column(Float)

engine=create_engine('sqlite:///user.db')
Base.metadata.create_all(engine)
Session=sessionmaker(bind=engine)
session=Session()

def create_user():
    emails=input("Enter an email:")
    usernames=input("Enter a username:")
    existing=session.query(Users).filter(Users.username==usernames).first()
    if existing:
        print("Username Taken.")
        print("Try Again.")
        create_user()
    
    passwords=input("Enter your password:")
    user1=Users(username=usernames,password=passwords,email=emails)
    session.add(user1)
    session.commit()
    user_ex1=User_Expenses(username=usernames,budget=0,transport=0,education=0,food=0,utility=0,misc=0,total_saving=0,datetime=datetime.datetime.now(),saving_goal=0,bud_transport=0,bud_education=0,bud_food=0,bud_utility=0,bud_misc=0)
    session.add(user_ex1)
    session.commit()
    Print("User Created.")
    login_user()

def login_user():
    usernames=input("Enter Username:")
    passwords=input("Enter Password")
    x= session.query(Users).filter(Users.username==usernames).first()
    y=session.query(Users).filter(Users.password==passwords).first()
    if x and y:
        print("Logged In.")
        loged_in(usernames)
    else:
        print("Incorrect Password.")
        login_user()

def before_login():
    x=int(input("""For Login press 1
        For SignUp press 2"""))
    
    if x==1:
        login_user()
    elif x==2:
        create_user()
    else:
        print("Not an option.")

def loged_in(usernames):
    last_expense=session.query(User_Expenses).filter(User_Expenses.username==usernames).order_by(User_Expenses.userid.desc()).first()
    if last_expense.budget==0:
        budgeting(usernames)
    while True:
        if last_expense.transport>last_expense.bud_transport or last_expense.education>last_expense.bud_education or last_expense.food>last_expense.bud_food or last_expense.utility>last_expense.bud_utility or last_expense.misc>last_expense.bud_misc:
            send_alert(usernames)
        y=int(input("""The options you have are:
            1. Create Expense
            2.Delete/Edit Expense
            3. Budgeting
            4.View and Download
            5.Exit"""))
        
        if y==1:
            create_expense(usernames)
        elif y==2:
            delete_expense(usernames)
        elif y==3:
            budgeting(usernames)
        elif y==4:
            view(usernames)
        elif y==5:
            break
        else:
            print("Not an option.")

def budgeting(usernames):

    last_expense=session.query(User_Expenses).filter(User_Expenses.username==usernames).order_by(User_Expenses.userid.desc()).first()
    print("Let's Start Budgeting shall we")
    budget_t=int(input("Enter the budget for transport"))
    last_expense.bud_transport=budget_t
    budget_e=int(input("Enter the budget for education"))
    last_expense.bud_education=budget_e
    budget_f=int(input("Enter the budget for food"))
    last_expense.bud_food=budget_f
    budget_u=int(input("Enter the budget for utility"))
    last_expense.bud_utility=budget_u
    budget_m=int(input("Enter the budget for misc"))
    last_expense.bud_misc=budget_m
    total=budget_t+budget_e+budget_f+budget_u+budget_m
    last_expense.budget=total
    last_expense.total_saving=total
    print(f"Your Total Budget = {total}")
    saving_goals=int(input("Enter the target for savings"))
    last_expense.saving_goal=saving_goals
    session.add(last_expense)
    session.commit()
    print("Budgetting Done.")


def download(usernames):
    date=datetime.datetime.now()
    with open(f"expenses_on_{date.strftime('%m_%d_%Y')}.csv",mode="w") as file:
        last_expense=session.query(User_Expenses).filter(User_Expenses.username==usernames).order_by(User_Expenses.userid.desc()).first()
        writer=csv.writer(file)
        writer.writerow(["Username","Transport","Education","Food","Utilty","Miscellenous","Budget","Budget for Transport","Budget for Education","Budget for Food","Budget for Utility","Budget for Miscellenous","Total Savings","Saving Goals"])
        writer.writerow([ last_expense.username,last_expense.transport,last_expense.education,last_expense.food,last_expense.utility,last_expense.misc,last_expense.budget,last_expense.bud_transport,last_expense.bud_education,last_expense.bud_food,last_expense.bud_utility,last_expense.bud_misc,last_expense.total_saving,last_expense.saving_goal])
        print("CSV downloaded.")

def graph(usernames):
    #pie chart
    last_expense=session.query(User_Expenses).filter(User_Expenses.username==usernames).order_by(User_Expenses.userid.desc()).first()
    x=np.array(["Transport","Education","Food","Utility","Miscellenous"])
    y=np.array([last_expense.transport,last_expense.education,last_expense.food,last_expense.utility,last_expense.misc])
    plt.pie(y)
    plt.show()
    #bar graph
    plt.bar(x,y)
    plt.show()


def view(usernames):
    last_expense=session.query(User_Expenses).filter(User_Expenses.username==usernames).order_by(User_Expenses.userid.desc()).first()
    print(f"""Username={last_expense.username}

             Total Spendicure:
             Transport={last_expense.transport}
             Education={last_expense.education}
             Food={last_expense.food}
             Utility={last_expense.utility}
             Misc={last_expense.misc}

            Budget and Savings:
            Budget={last_expense.budget}
            Budget for Transport={last_expense.bud_transport}
            Budget for Education={last_expense.bud_education}
            Budget for Food={last_expense.bud_food}
            Budget for Utility={last_expense.bud_utility}
            Budget for Miscellenous={last_expense.misc}
            Total Savings={last_expense.total_saving}
            Saving Goals={last_expense.saving_goal}

    """)
    graph(usernames)
    x=input("Do you want to download CSV of this report")
    if x.lower()=="yes":
        download(usernames)
    

def send_alert(usernames):

    user=session.query(Users).filter(Users.username==usernames).first()
    sender_email=""
    receiver_email=user.email
    password=""

    message=MIMEMultipart()
    message["From"]=sender_email
    message["To"]=receiver_email
    message["Subject"]="Warning!!!!"

    body="You have spent more than your budget this month."
    message.attach(MIMEText(body,"plain"))

    try:
        with smtplib.SMTP("smtp.gmail.com",587) as server:
            server.starttls()
            server.login(sender_email, password)
            server.sendmail(sender_email, receiver_email, message.as_string())
        print("Email sent successfully")
    except Exception as e:
        print(f"Error: {e}")

categories=["transport","education","food","utility","misc"]
def create_expense(usernames):
    category=input("Enter the category for the expense")
    if category.lower() not in categories:
        print("Incorrect Category.")
        create_expense()
    amount=float(input("Enter the amount"))
    last_expense=session.query(User_Expenses).filter(User_Expenses.username==usernames).order_by(User_Expenses.userid.desc()).first()


    if category.lower()=="transport":
        last_expense.transport+=amount
    elif category.lower()=="education":
        last_expense.education+=amount
    elif category.lower()=="food":
        last_expense.food+=amount
    elif category.lower()=="utility":
        last_expense.utility+=amount
    elif category.lower()=="misc":
        last_expense.misc+=amount
    
    last_expense.total_saving-=amount
    last_expense.datetime=datetime.datetime.now()
    session.add(last_expense)
    session.commit()
    print("Expenses Added.")


def delete_expense(usernames):
    category=input("Enter the category for the expense")
    if category.lower() not in categories:
        print("Incorrect Category.")
        create_expense()
    amount=float(input("Enter the amount"))
    last_expense=session.query(User_Expenses).filter(User_Expenses.username==usernames).order_by(User_Expenses.userid.desc()).first()


    if category.lower()=="transport":
        last_expense.transport-=amount
    elif category.lower()=="education":
        last_expense.education-=amount
    elif category.lower()=="food":
        last_expense.food-=amount
    elif category.lower()=="utility":
        last_expense.utility-=amount
    elif category.lower()=="misc":
        last_expense.misc-=amount
    
    last_expense.total_saving+=amount
    last_expense.datetime=datetime.datetime.now()
    session.add(last_expense)
    session.commit()
    print("Expense Deleted.")

before_login()





