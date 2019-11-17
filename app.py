from flask import Flask, request, Response, render_template
import requests
import itertools
from flask_wtf.csrf import CSRFProtect
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, SelectField
from wtforms.validators import Regexp, Length
import re

class WordForm(FlaskForm):
    avail_letters = StringField("Letters", validators= [
        Regexp(r'^[a-z]*$', message="Pattern must contain letters only")
    ])
    word_length = SelectField(u'Word Length', choices=[("","---"),('3','3'),('4','4'),('5','5'),('6','6'),('7','7'),('8','8'),('9','9'),('10','10')])
    word_pattern = StringField("Pattern", validators= [
        Regexp(r'^[a-z\.]*$', message="must contain only letters and dots")
    ])
    submit = SubmitField("Go")
    def validate(self):
        result = True
        if not super().validate():
            return False
        if len(self.avail_letters.data) < 1:
            if len(self.word_pattern.data) < 1:
                error = list(self.word_pattern.errors)
                error.append('A pattern is required if no letters are selected.')
                self.word_pattern.errors = tuple(error)
                result = False
        if len(self.word_length.data) != 0 and len(self.word_pattern.data) != 0:
            if len(self.word_pattern.data) != int(self.word_length.data):
                error = list(self.word_pattern.errors)
                error.append('The pattern length must match the word length selected.')
                self.word_pattern.errors = tuple(error)
                result = False
        return result


csrf = CSRFProtect()
app = Flask(__name__)
app.config["SECRET_KEY"] = "row the boat"
csrf.init_app(app)
wordset = set()

@app.route('/index')
def index():
    form = WordForm()
    return render_template("index.html", form=form)

def check_patterns(word, pattern):
        i = 0
        if pattern == "":
            return True
        while i < len(word):
            if pattern[i] != '.':
                if word[i] != pattern[i]:
                    return False
            i = i+1
        return True

@app.route('/words', methods=['POST','GET'])
def letters_2_words():

    form = WordForm()
    if form.validate_on_submit():
        letters = form.avail_letters.data
        if form.word_length.data != "":   
            length = int(form.word_length.data)
        else:
            length = 0
        pattern = form.word_pattern.data
    else:
        return render_template("index.html", form=form)

    with open('sowpods.txt') as f:
        good_words = set(x.strip().lower() for x in f.readlines())

    word_set = set()
    if len(letters) > 0:
        for l in range(3,len(letters)+1):
            for word in itertools.permutations(letters,l):
                w = "".join(word)
                if length > 0:
                    if w in good_words and len(w) == length and check_patterns(w, pattern):
                        word_set.add(w)
                else:
                    if w in good_words and check_patterns(w, pattern): 
                        word_set.add(w)

    global wordset
    wordset = sorted(sorted(word_set),key = len)

    return render_template('wordlist.html',
        wordlist=sorted(sorted(word_set),key=len))




@app.route('/proxy')
def proxy():
    result = requests.get(request.args['url'])
    resp = Response(result.text)
    resp.headers['Content-Type'] = 'application/json'
    return resp

@app.route('/definition/<word>')
def getDefinition(word):
    KEY = "bb174e73-8c43-435d-b626-8698c6bf8fc2"
    link = "https://www.dictionaryapi.com/api/v3/references/collegiate/json/" + word +"?key=" + KEY
    response = requests.get(link)
    if response.status_code == 200:
        print("The request for the word was a success: " + word)
    else:
        print("the request for the word was a failure: " + word)
    return render_template('wordlist.html',
        wordlist=sorted(sorted(wordset),key=len))


if __name__ == '__main__':
    app.run()