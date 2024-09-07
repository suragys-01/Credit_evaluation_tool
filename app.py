from flask import Flask, request, render_template, redirect, url_for, flash
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from pymongo import MongoClient
from flask_bcrypt import Bcrypt
import pickle
import numpy as np 
import os

import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
app = Flask(__name__)
app.secret_key = 'your_secret_key'


# Configure Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Initialize Bcrypt for password hashing
bcrypt = Bcrypt(app)

# MongoDB client setup
client = MongoClient("mongodb+srv://pkpavan2003:lzPrZel3OLaBi5bN@loanapprovalprediction.zstouto.mongodb.net/")
db = client['loan_approval_prediction']
users_collection = db['users']

# User class for Flask-Login
class User(UserMixin):
    def __init__(self, id, email):
        self.id = id
        self.email = email

@login_manager.user_loader
def load_user(user_id):
    user_data = users_collection.find_one({"username": user_id})
    if user_data:
        return User(user_id, user_data.get('email'))
    return None



# Verify the existence and readability of the model file
model_path = 'model.pkl'
if not os.path.exists(model_path):
    raise FileNotFoundError(f"The model file '{model_path}' does not exist.")
if not os.access(model_path, os.R_OK):
    raise PermissionError(f"The model file '{model_path}' is not readable.")

# Load the model
with open(model_path, 'rb') as model_file:
    model = pickle.load(model_file)

with open('model2.pkl', 'rb') as model_file2:
    model2 = pickle.load(model_file2)

with open('model3.pkl', 'rb') as model_file3:
    model3 = pickle.load(model_file3)

with open('model4.pkl', 'rb') as model_file4:
    model4 = pickle.load(model_file4)


# Function to send email
def send_email(to_email, prediction_text):
    sender_email = "sohambalekundri862@gmail.com"  # replace with your email
    sender_password = "stpauls2120"      # replace with your password
    
    msg = MIMEMultipart()
    msg['From'] = sender_email
    msg['To'] = to_email
    msg['Subject'] = "Loan Prediction Status"

    body = f"Your loan approval status is {prediction_text}."
    msg.attach(MIMEText(body, 'plain'))

    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)  # Using Gmail's SMTP server
        server.starttls()
        server.login(sender_email, sender_password)
        text = msg.as_string()
        server.sendmail(sender_email, to_email, text)
        server.quit()
    except Exception as e:
        print(f"Error sending email: {e}")

@app.route('/')
def home():
    return render_template("index.html")

@app.route('/about')
def about():
    return render_template("about.html")

@app.route('/contact')
def contact():
    return render_template("contact.html")

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = users_collection.find_one({"username": username})
        if user and bcrypt.check_password_hash(user['password'], password):
            user_obj = User(username, user['email'])
            login_user(user_obj)
            flash('Login successful!', 'success')
            flash(f'Welcome {username}!', 'success')
            return redirect(url_for('predict'))
        else:
            flash('Invalid credentials. Please try again.', 'danger')
    return render_template('login.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        confirm_password = request.form['confirm_password']
        
        if password != confirm_password:
            flash('Passwords do not match. Please try again.', 'danger')
            return redirect(url_for('signup'))
        
        if users_collection.find_one({"username": username}):
            flash('Username already exists. Please try another one.', 'danger')
            return redirect(url_for('signup'))
        
        if users_collection.find_one({"email": email}):
            flash('Email already exists. Please try another one.', 'danger')
            return redirect(url_for('signup'))
        
        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
        users_collection.insert_one({"username": username, "email": email, "password": hashed_password})
        flash('Signup successful! Please log in.', 'success')
        return redirect(url_for('login'))
    
    return render_template('signup.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('login'))

@app.route('/predict', methods=['GET', 'POST'])
def predict():
    if request.method == 'POST':
        try:
            # Extract form data
            gender = request.form['gender']
            married = request.form['married']
            dependents = request.form['dependents']
            education = request.form['education']
            employed = request.form['employed']
            credit = float(request.form['credit'])
            area = request.form['area']
            ApplicantIncome = float(request.form['ApplicantIncome'])
            CoapplicantIncome = float(request.form['CoapplicantIncome'])
            LoanAmount = float(request.form['LoanAmount'])
            Loan_Amount_Term = float(request.form['Loan_Amount_Term'])

            # Feature transformation
            male = 1 if gender == "Male" else 0
            married_yes = 1 if married == "Yes" else 0
            dependents_1, dependents_2, dependents_3 = 0, 0, 0
            if dependents == '1':
                dependents_1 = 1
            elif dependents == '2':
                dependents_2 = 1
            elif dependents == '3+':
                dependents_3 = 1
            not_graduate = 1 if education == "Not Graduate" else 0
            employed_yes = 1 if employed == "Yes" else 0
            semiurban, urban = 0, 0
            if area == "Semiurban":
                semiurban = 1
            elif area == "Urban":
                urban = 1
            total_income = ApplicantIncome + CoapplicantIncome

            # Prepare input features for prediction
            input_features = [LoanAmount, Loan_Amount_Term, credit, total_income, male, married_yes, 
                              dependents_1, dependents_2, dependents_3, not_graduate, employed_yes, semiurban, urban]
            
            # Convert input features to numpy array and reshape for prediction
            input_features = np.array(input_features).reshape(1, -1)
            
            # Prediction of hard voting classifier
            prediction = model.predict(input_features)
            prediction_text = prediction

            # Prediction of log_reg
            prediction2 = model2.predict(input_features)
            prediction_text2 = prediction2

            # Prediction of svc
            prediction3 = model3.predict(input_features)
            prediction_text3 = prediction3
            
            # Prediction of dt
            prediction4 = model4.predict(input_features)
            prediction_text4 = prediction4


            return render_template("prediction.html", 
                       prediction_text=f"Loan Approval Estimation from HV model is: {prediction_text} \n"
                                       f"Loan Approval Estimation from LR model is: {prediction_text2}  \n"
                                       f"Loan Approval Estimation from SVC model is: {prediction_text3}\n"
                                       f"Loan Approval Estimation from DT model is: {prediction_text4}\n"
                                       )

        except ValueError:
            return "Please enter valid numeric values for income and loan amount fields."
        except Exception as e:
            return f"An error occurred: {e}"

    return render_template("prediction.html")

if __name__ == "__main__":
    app.run(debug=True)
