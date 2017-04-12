# app.py
from flask import Flask, render_template, request
from wtforms import Form, TextAreaField, validators
#from model import multiply
import subprocess

app = Flask(__name__)

class HelloForm(Form):
    sayhello = TextAreaField('',[validators.DataRequired()])

@app.route('/')
def index():
    form = HelloForm(request.form)
    return render_template('first_app.html', form=form)

@app.route('/hello', methods=['POST'])
def hello():
    form = HelloForm(request.form)
    if request.method == 'POST' and form.validate():
    	command = 'Rscript'
    	script = 'Rmodel.R'
    	args = ['2', '3']
    	cmd = [command, script] + args
    	x = subprocess.check_output(cmd, universal_newlines = True)
    	name = request.form['sayhello'] + str(x)
    	return render_template('hello.html', name = name)
		#name = request.form['sayhello'] + str(multiply(2,3))
    return render_template('first_app.html', form=form)

if __name__ == '__main__':
    app.run(debug=True)

