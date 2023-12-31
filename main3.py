from flask import Flask, request, flash, session, url_for, redirect, render_template
from flask_sqlalchemy import SQLAlchemy
import datetime
import paho.mqtt.client as mqtt

import time
from datetime import datetime
import board
import adafruit_dht

import RPi.GPIO as GPIO
GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)
GPIO.setup(2, GPIO.OUT)

dhtDevice = adafruit_dht.DHT22(board.D18)

app = Flask(__name__)

mqttc=mqtt.Client()
mqttc.connect("localhost",1883,60)
mqttc.loop_start()

mqttc1=mqtt.Client()
mqttc1.connect("localhost",1883,60)
mqttc1.loop_start()

mqttc2=mqtt.Client()
mqttc2.connect("localhost",1883,60)
mqttc2.loop_start()

mqttc3=mqtt.Client()
mqttc3.connect("localhost",1883,60)
mqttc3.loop_start()

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///user.sqlite3'
app.config['SECRET_KEY'] = "random string"
db = SQLAlchemy(app)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(100))
    name = db.Column(db.String(1000))
    
class waktu(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    suhu = db.Column(db.Float)
    waktus = db.Column(db.String(1000))

db.create_all()

# Create a dictionary called pins to store the pin number, name, and pin state:
pins = {
   0 : {'name' : 'Lampu Teras', 'board' : 'esp8266', 'topic' : 'esp8266/0', 'state' : 'False'}
   }
pins1 = {
   0 : {'name' : 'Lampu Ruang  Tamu', 'board' : 'esp8266_2', 'topic' : 'esp8266_2/0', 'state' : 'False'}
   }
pins2 = {
   0 : {'name' : 'Lampu Taman', 'board' : 'esp8266_3', 'topic' : 'esp8266_3/0', 'state' : 'False'}
   }
pins3 = {
   0 : {'name' : 'Lampu Kamar', 'board' : 'esp8266_4', 'topic' : 'esp8266_4/0', 'state' : 'False'}
   }

# Put the pin dictionary into the template data dictionary:

templateData = {
   'pins' : pins,
   'pins1' : pins1,
   'pins2' : pins2,
   'pins3' : pins3
   }

@app.route('/')
def login():
    return render_template('login.html')

@app.route('/edit')
def edit():
    return render_template('edit.html')

@app.route('/editProses', methods=['POST'])
def edit_proses():
    email = request.form.get('email')
    password = request.form.get('password')

    user = User.query.filter_by(email=email).first()

    
    if not user:
        flash('Email belum terdaftar')
        return redirect(url_for('register')) 

    num_rows_updated = User.query.filter_by(email=email).update(dict(password=password))
    db.session.commit()

    return redirect(url_for('login'))
    
@app.route('/register')
def register():
    return render_template('register.html')

@app.route('/registerProses', methods=['POST'])
def proses_register():
    email = request.form.get('email')
    name = request.form.get('name')
    password = request.form.get('password')

    user = User.query.filter_by(email=email).first() 

    if user: 
        flash('Email Sudah ada')
        return redirect(url_for('register'))

    new_user = User(email=email, name=name, password=password)

    
    db.session.add(new_user)
    db.session.commit()

    return redirect(url_for('login'))

@app.route('/loginProses', methods=['POST'])
def proses_login():
    email = request.form.get('email')
    password = request.form.get('password')

    user = User.query.filter_by(email=email).first()

    
    if (user.password != password):
        flash('Please check your login details and try again.')
        return redirect(url_for('login')) 
    
    session['username'] = user.name
    return redirect(url_for('index'))

@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('login'))

@app.route("/index")
def index():
   return render_template('index.html')

@app.route("/lampu")
def lampu():
   return render_template('lampu.html', **templateData)

@app.route("/tes")
def tes():
    global waktu
    data = waktu.query.all()
    ids = []
    suhu = []
    waktus = []

    for amounts in data:
        ids.append(amounts.id)
        suhu.append(amounts.suhu)
        waktus.append(amounts.waktus)
        
    import matplotlib.pyplot as plt
    import io
    import base64
    from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
    from matplotlib.figure import Figure
    fig = Figure()
    axis = fig.add_subplot(1, 1, 1)
    axis.set_title("")
    axis.set_xlabel("")
    axis.set_ylabel("")
    axis.grid()
    axis.plot(ids, suhu)

    pngImage = io.BytesIO()
    FigureCanvas(fig).print_png(pngImage)
    
        # Encode PNG image to base64 string
    pngImageB64String = "data:image/png;base64,"
    pngImageB64String += base64.b64encode(pngImage.getvalue()).decode('utf8')
    return render_template('tes.html', image=pngImageB64String)

@app.route("/suhu")
def suhu():
    global waktu
    data = waktu.query.all()
    ids = []
    suhu = []
    waktus = []

    for amounts in data:
        ids.append(amounts.id)
        suhu.append(amounts.suhu)
        waktus.append(amounts.waktus)
        
    while True:
     try:
        temp_c = dhtDevice.temperature
        humidity = dhtDevice.humidity
        print("Temp: {:.1f} C / Humidity : {}%". format (temp_c, humidity))
     except RuntimeError as error:
        print(error.args[0])
        time.sleep(2.0)
        continue
     except Exception as error:
        dhtDevice.exit()
        raise error
    
     if temp_c <= 28 :
        GPIO.output(2, False)
     else :
        GPIO.output(2, True)
        
     suhu1 = temp_c
     now = datetime.now()
     waktus = "{:d}:{:02d}".format(now.hour, now.minute)
     new_user = waktu(suhu=suhu1, waktus=waktus)
     db.session.add(new_user)
     db.session.commit()
     
     import matplotlib.pyplot as plt
     import io
     import base64
     from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
     from matplotlib.figure import Figure
     fig = Figure()
     axis = fig.add_subplot(1, 1, 1)
     axis.set_title("Grafik kenaikan suhu")
     axis.set_xlabel("")
     axis.set_ylabel("")
     axis.grid()
     axis.plot(ids, suhu)
     pngImage = io.BytesIO()
     FigureCanvas(fig).print_png(pngImage)
     pngImageB64String = "data:image/png;base64,"
     pngImageB64String += base64.b64encode(pngImage.getvalue()).decode('utf8')
    
     return render_template('suhu.html', image=pngImageB64String, temp_c=temp_c, humidity=humidity, suhu=suhu, waktus=waktus)


@app.route("/<board>/<changePin>/<action>")
def action(board, changePin, action):
   # Convert the pin from the URL into an integer:
   changePin = int(changePin)
   # Get the device name for the pin being changed:
   devicePin = pins[changePin]['name']
   # If the action part of the URL is "on," execute the code indented below:
#ESP 1
   if action == "1" and board == 'esp8266':
      mqttc.publish(pins[changePin]['topic'],"0")
      pins[changePin]['state'] = 'True'
      print("off")

   if action == "0" and board == 'esp8266':
      mqttc.publish(pins[changePin]['topic'],"1")
      pins[changePin]['state'] = 'False'
#ESP 2
   if action == "1" and board == 'esp8266_2':
      mqttc1.publish(pins1[changePin]['topic'],"0")
      pins1[changePin]['state'] = 'True'
      print("off")

   if action == "0" and board == 'esp8266_2':
      mqttc1.publish(pins1[changePin]['topic'],"1")
      pins1[changePin]['state'] = 'False'
#ESP 3
   if action == "1" and board == 'esp8266_3':
      mqttc2.publish(pins2[changePin]['topic'],"0")
      pins2[changePin]['state'] = 'True'
      print("off")

   if action == "0" and board == 'esp8266_3':
      mqttc2.publish(pins2[changePin]['topic'],"1")
      pins2[changePin]['state'] = 'False'
#ESP 4
   if action == "1" and board == 'esp8266_4':
      mqttc3.publish(pins3[changePin]['topic'],"0")
      pins3[changePin]['state'] = 'True'
      print("off")

   if action == "0" and board == 'esp8266_4':
      mqttc3.publish(pins3[changePin]['topic'],"1")
      pins3[changePin]['state'] = 'False'

   # Along with the pin dictionary, put the message into the template data dictionary:
   templateData = {
      'pins' : pins,
      'pins1' : pins1,
      'pins2' : pins2,
      'pins3' : pins3
   }

   return redirect(url_for('lampu'))

if __name__ == "__main__":
   app.run(host='192.168.56.15', port=8181)


