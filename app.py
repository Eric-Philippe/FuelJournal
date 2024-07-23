import os
import datetime
from flask import Flask, request, render_template, flash, g
import influxdb_client
from influxdb_client.client.write_api import SYNCHRONOUS
# Load .env file
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.secret_key = 'supersecretkey'


# InfluxDB setup
INFLUXDB_URL = os.getenv("INFLUXDB_URL", "http://influxdb:8086")
INFLUXDB_TOKEN = os.getenv("INFLUXDB_TOKEN")
INFLUXDB_ORG = os.getenv("INFLUXDB_ORG")
INFLUXDB_BUCKET = os.getenv("INFLUXDB_BUCKET")

# Initialize InfluxDB client
influx_client = influxdb_client.InfluxDBClient(url=INFLUXDB_URL, token=INFLUXDB_TOKEN, org=INFLUXDB_ORG)
write_api = influx_client.write_api(write_options=SYNCHRONOUS)

def push_to_influxdb(date, sp95, sp98, dieselPremium, diesel):
    point = influxdb_client.Point("fuel_prices") \
        .tag("date", date) \
        .field("sp95", sp95) \
        .field("sp98", sp98) \
        .field("dieselPremium", dieselPremium) \
        .field("diesel", diesel)
    write_api.write(bucket=INFLUXDB_BUCKET, record=point)
    print("Data pushed to InfluxDB")

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST': 
        date = get_today_date()
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
            push_to_influxdb(date, sp95, sp98, dieselPremium, diesel)
            flash('Record was successfully added.', 'success')
    
    return render_template('index.html')

def get_today_date():
    return datetime.datetime.now().strftime("%Y-%m-%d")

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80, debug=True)
