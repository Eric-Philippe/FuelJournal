import sqlite3
import os
import time
import datetime
from flask import Flask, request, render_template, flash, g

app = Flask(__name__)
app.secret_key = 'supersecretkey'

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATABASE = os.path.join(BASE_DIR, 'database.db')

def get_db():
    if 'db' not in g:
        g.db = sqlite3.connect(DATABASE)
        g.db.row_factory = sqlite3.Row
    return g.db

def close_db(e=None):
    db = g.pop('db', None)
    if db is not None:
        db.close()

@app.before_request
def before_request():
    get_db()

@app.teardown_appcontext
def teardown_db(exception):
    close_db()

req_table = '''
CREATE TABLE IF NOT EXISTS FuelPrices(
    date TEXT PRIMARY KEY NOT NULL,
    sp95 REAL NOT NULL CHECK(sp95 >= 0),
    sp98 REAL NOT NULL CHECK(sp98 >= 0),
    dieselPremium REAL NOT NULL CHECK(dieselPremium >= 0),
    diesel REAL NOT NULL CHECK(diesel >= 0)
);
'''

def create_table():
    with app.app_context(): 
        db = get_db()
        db.execute(req_table)
        db.commit()
        print("Opened database successfully")
        cursor = db.execute('SELECT COUNT(*) FROM FuelPrices')
        print("Amount of rows in the table: ", cursor.fetchone()[0])
        
        time.sleep(1)
        
        # Add 1.50 entries for testing
        try:
            insert_entry(get_date(2024, 7, 20), 1.10, 1.10, 1.10, 1.10)
            insert_entry(get_date(2024, 7, 21), 1.20, 1.20, 1.20, 1.20)
            insert_entry(get_date(2024, 7, 22), 1.30, 1.30, 1.30, 1.30)
            insert_entry(get_date(2024, 7, 23), 1.40, 1.40, 1.40, 1.40)
        except sqlite3.IntegrityError:
            pass

def has_entry(date):
    db = get_db()
    cursor = db.execute('SELECT COUNT(*) FROM FuelPrices WHERE date = ?', (date,))
    amount = cursor.fetchone()[0]
    return amount > 0

def insert_entry(date, sp95, sp98, dieselPremium, diesel):
    db = get_db()
    db.execute('INSERT INTO FuelPrices (date, sp95, sp98, dieselPremium, diesel) VALUES (?, ?, ?, ?, ?)', (date, sp95, sp98, dieselPremium, diesel))
    db.commit()
    print("Record created successfully")

"""
Returns date as : 2023-11-02
"""
def get_today_date():
    return datetime.datetime.now().strftime("%Y-%m-%d")

def get_date(year, month, day):
    return datetime.datetime(year, month, day).strftime("%Y-%m-%d")


@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST': 
        date = get_today_date()
        if has_entry(date):
            flash("Entry already exists for today.", 'error')
        else:
            sp95 = request.form['sp95']
            sp98 = request.form['sp98']
            dieselPremium = request.form['dieselPremium']
            diesel = request.form['diesel']
            
            try:
                sp95 = float(sp95.replace(',', '.'))
                sp98 = float(sp98.replace(',', '.'))
                dieselPremium = float(dieselPremium.replace(',', '.'))
                diesel = float(diesel.replace(',', '.'))
            except ValueError:
                flash("Please enter valid numbers.", 'error')
                return render_template('index.html')
            
            if not sp95 or not sp98 or not dieselPremium or not diesel:
                flash("Please fill in all the fields.", 'error')
            elif float(sp95) < 0 or float(sp98) < 0 or float(dieselPremium) < 0 or float(diesel) < 0:
                flash("Prices cannot be negative.", 'error')
            elif float(sp95) > 3 or float(sp98) > 3 or float(dieselPremium) > 3 or float(diesel) > 3:
                flash("Prices are too high.", 'error')
            else:
                insert_entry(date, sp95, sp98, dieselPremium, diesel)
                flash('Record was successfully added.', 'success')
    
    return render_template('index.html')

if __name__ == '__main__':
    with app.app_context():
        create_table()
    app.run(host='0.0.0.0', port=80, debug=True)
