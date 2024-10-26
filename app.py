from flask import Flask, render_template, request, url_for, redirect, session, flash, jsonify
from joblib import load
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash
import pandas as pd
import plotly.express as px
import plotly.io as pio

app = Flask(__name__)
app.secret_key = '1234'

# SQLite database file
DATABASE = 'user_registration.db'

def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row  # To return rows as dictionaries
    return conn

# Load the model
model = load('random_forest_model.joblib')
feature_names = model.feature_names_in_.tolist()

@app.route('/')
def home():
    return render_template('login.html')

@app.route('/predict', methods=['POST'])
def predict():
    engine_size = float(request.form['engine_size'])
    vehicle_class = request.form['vehicle_class']

    input_data_dict = {feature: 0 for feature in feature_names}
    input_data_dict['Engine Size(L)'] = engine_size

    vehicle_class_feature = f'Vehicle Class_{vehicle_class}'
    if vehicle_class_feature in feature_names:
        input_data_dict[vehicle_class_feature] = 1
    else:
        return f'Error: Vehicle class "{vehicle_class}" is not valid.'

    input_data = pd.DataFrame([input_data_dict])
    prediction = model.predict(input_data)

    # Save the data to the database
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Assuming you have a table called 'emissions' with the appropriate columns
        cursor.execute('INSERT INTO emissions (user_id, vehicle_class, engine_size, carbon_emission) VALUES (?, ?, ?, ?) ',
                       (session['user_id'], vehicle_class, engine_size, prediction[0]))

        conn.commit()
        cursor.close()
        conn.close()

        return f'The predicted CO2 emissions is: {prediction[0]:.2f} g/km and has been saved to the database.'

    except Exception as e:
        return f'Error while saving data: {e}'

@app.route('/dashboard')
def dashboard():
    # Load the dataset for agriculture, forestry, and other land use emissions
    agriculture_file_path = './datasets/agriculture.csv'
    agriculture_df = pd.read_csv(agriculture_file_path, skiprows=4)

    south_africa_agriculture_data = agriculture_df[agriculture_df['Country Name'] == 'South Africa']
    south_africa_agriculture_data_cleaned = south_africa_agriculture_data.drop(
        columns=['Country Name', 'Country Code', 'Indicator Name', 'Indicator Code', 'Unnamed: 68']
    ).dropna(axis=1).T

    south_africa_agriculture_data_cleaned.columns = ['CO2 Emissions']
    south_africa_agriculture_data_cleaned.index = pd.to_numeric(south_africa_agriculture_data_cleaned.index)

    agriculture_fig = px.line(
        south_africa_agriculture_data_cleaned,
        x=south_africa_agriculture_data_cleaned.index,
        y='CO2 Emissions',
        title='CO2 Emissions from Agriculture, Forestry, and Other Land Use in South Africa (1960-2022)',
        labels={'x': 'Year', 'y': 'CO2 Emissions (MtCO2)'}
    )
    agriculture_fig.update_layout(
        xaxis_title='Year', 
        yaxis_title='CO2 Emissions (MtCO2)', 
        template='plotly_white'
    )
    agriculture_graph_html = pio.to_html(agriculture_fig, full_html=False)

    transportation_file_path = './datasets/transportation.csv'
    transportation_df = pd.read_csv(transportation_file_path, skiprows=4)

    south_africa_transportation_data = transportation_df[transportation_df['Country Name'] == 'South Africa']
    south_africa_transportation_data_cleaned = south_africa_transportation_data.drop(
        columns=['Country Name', 'Country Code', 'Indicator Name', 'Indicator Code', 'Unnamed: 68']
    ).dropna(axis=1).T

    south_africa_transportation_data_cleaned.columns = ['CO2 Emissions']
    south_africa_transportation_data_cleaned.index = pd.to_numeric(south_africa_transportation_data_cleaned.index)

    transportation_fig = px.line(
        south_africa_transportation_data_cleaned,
        x=south_africa_transportation_data_cleaned.index,
        y='CO2 Emissions',
        title='CO2 Emissions from Transportation in South Africa (1960-2022)',
        labels={'x': 'Year', 'y': 'CO2 Emissions (MtCO2)'}
    )
    transportation_fig.update_layout(
        xaxis_title='Year', 
        yaxis_title='CO2 Emissions (MtCO2)', 
        template='plotly_white'
    )
    transportation_graph_html = pio.to_html(transportation_fig, full_html=False)

    return render_template('dashboard.html', agriculture_graph_html=agriculture_graph_html, transportation_graph_html=transportation_graph_html)

@app.route('/save_prediction', methods=['POST'])
def save_prediction():
    data = request.get_json()
    engine_size = data.get('engine_size')
    vehicle_class = data.get('vehicle_class')
    predicted_emission = data.get('predicted_emission')

    # Save the data to your database here
    # Example: save_to_db(engine_size, vehicle_class, predicted_emission)

    return jsonify({"status": "success"}), 201

@app.route('/calculate_total_carbon_emission')
def calculate_total_carbon_emission():
    return render_template('calculator.html')

@app.route('/emission_result')
def emission_result():
    return render_template('emission.html')

@app.route('/predictor_result')
def predictor_result():
    return render_template('predictor.html')

@app.route('/index')
def index():
    return render_template('index.html')

@app.route('/about_us')
def about_us():
    return render_template('about.html')

@app.route('/contact_us')
def contact_us():
    return render_template('contact.html')

@app.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        return redirect(url_for('login'))
    return render_template('forgotPassword.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        try:
            conn = get_db_connection()
            cursor = conn.cursor()

            cursor.execute('SELECT * FROM users WHERE email = ?', (email,))
            user = cursor.fetchone()
            cursor.close()
            conn.close()

            if user:
                if check_password_hash(user['password'], password):  # Use row dictionary
                    session['user_id'] = user['id']  # Use row dictionary
                    flash("Login successful!")
                    return redirect('/dashboard')
                else:
                    flash("Incorrect password.")
            else:
                flash("Email not found.")
        except Exception as e:
            flash(f"Error: {e}")
        
        return redirect('/login')

    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        confirm_password = request.form['confirm_password']

        if password != confirm_password:
            flash("Passwords do not match!")
            return redirect('/register')

        hashed_password = generate_password_hash(password, method='pbkdf2:sha256')

        try:
            conn = get_db_connection()
            cursor = conn.cursor()

            cursor.execute('SELECT * FROM users WHERE email = ?', (email,))
            existing_user = cursor.fetchone()
            if existing_user:
                flash("Email already registered!")
                return redirect('/register')

            cursor.execute('INSERT INTO users (email, password) VALUES (?, ?)', (email, hashed_password))
            conn.commit()
            cursor.close()
            conn.close()

            flash("Registration successful!")
            return redirect('/login')

        except Exception as e:
            flash(f"Error: {e}")
            return redirect('/register')

    return render_template('register.html')

if __name__ == '__main__':
    app.run(debug=True)
