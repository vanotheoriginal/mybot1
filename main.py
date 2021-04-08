import json
import sqlite3
from urllib.request import urlopen
import requests
from bs4 import BeautifulSoup
from flask import Flask, request
from flask_sslify import SSLify

app = Flask(__name__)
sslify = SSLify(app)

# URL = 'https://api.telegram.org/bot1610793875:AAHBMRtCaI41gLTTTOCOaXKfpfBfl1FX-DM/setWebHook?url=https://a53d1e82b7af.ngrok.io/'
URL = 'https://api.telegram.org/bot1610793875:AAHBMRtCaI41gLTTTOCOaXKfpfBfl1FX-DM/'
URL2 = 'http://api.exchangeratesapi.io/v1/latest?access_key=189db637f6a36f043e3b8c418e526ab9&format=1'


def write_json(data, filename='answer.json'):
    with open(filename, 'w') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def checkJson():
    url = URL
    r = requests.get(url)
    return r.json()


def sendMessage(chat_id, text='Default text'):
    url = URL + 'sendMessage'
    answer = {'chat_id': chat_id, 'text': text}
    r = requests.post(url, json=answer)
    return r.json()


def get_price(typew='from_API'):

    if typew =='from_API':    # Gets information from API
        url = URL2
        response = requests.get(url).json()
        date = response['date']
        stack = 'Date: ' + date + '\n'
        db_clear()
        for r in response['rates']:
            str = f'{r}: {round(response["rates"][r], 2)}'
            db_insert(r, round(response["rates"][r], 2))
            stack = stack + str + '\n'
        return stack
    else:                   # Gets information from database
        stack = db_select()
        return stack


def db_create():
    db = sqlite3.connect('server.db')
    sql = db.cursor()
    sql.execute("""CREATE TABLE IF NOT EXISTS currency(name TEXT, value REAL)""")
    db.commit()


def db_insert(name, value):
    db = sqlite3.connect('server.db')
    sql = db.cursor()
    sql.execute(f"INSERT INTO currency VALUES (?, ?)", (name, value))
    db.commit()


def db_clear():
    db = sqlite3.connect('server.db')
    sql = db.cursor()
    sql.execute("DELETE FROM currency")
    db.commit()


def db_select():
    stack = ''
    db = sqlite3.connect('server.db')
    sql = db.cursor()

    for value in sql.execute("SELECT * FROM currency"):
        str = f'{value[0]}: {value[1]}'
        stack = stack + str + '\n'
    return stack


def exchange(parse):
    if parse and len(parse) <= 5:
        coef = getCAD()
        value = parse[1].replace('$', '', 1)
        try:
            float(value)
            b = True
        except ValueError:
            b = False
        if b:
            current = float(value) * float(coef)
            return f'${round(float(value), 2)} USD = ${round(current, 2)} CAD'
        else:
            return None


def getCAD():
    html = urlopen('https://finance.yahoo.com/quote/USDCAD=x')
    bsObj = BeautifulSoup(html.read())
    result = bsObj.find("span", class_="Trsdu(0.3s) Fw(b) Fz(36px) Mb(-4px) D(ib)")
    return result.text


def str_check(str):


    if str[2] == 'to' and str[3] == 'CAD':
        value = str[1].replace('$', '', 1)
        try:
            float(value)
            return True
        except ValueError:
            return False
        return True
    elif str[2] == 'USD' and str[3] == 'to' and str[4] == 'CAD':
        try:
            float(str[1])
            return True
        except ValueError:
            return False
        return True
    else:
        return False



@app.route('/', methods=['POST', 'GET'])
def index():
    commands = ['/list', '/exchange', '/help', '/start']

    if request.method == 'POST':
        r = request.get_json()
        if 'message' in r:
            chat_id = r['message']['chat']['id']
            message = r['message']['text']
        else:
            chat_id = r['edited_message']['chat']['id']
            message = r['edited_message']['text']

        db_create()

        parse = message.split(' ')
        if parse[0] in commands:
            if len(parse) > 1:
                if parse[0] == commands[1] and str_check(parse): # /exchange
                    sendMessage(chat_id, text=exchange(parse))
                else:
                    sendMessage(chat_id, text='[-] Error: Wrong syntax at /exchange.')
            else:
                if parse[0] == commands[0]: # /list
                    sendMessage(chat_id, text="[+] Please wait a second...")
                    sendMessage(chat_id, text=get_price())
                elif parse[0] == commands[2]: # /help
                    sendMessage(chat_id, text='Hi, welcome. Command list below:\n/list\n/exchange $<value> to CAD\n/exchange <value> USD to CAD\n/help')
                elif parse[0] == commands[3]: # /start
                    sendMessage(chat_id, text='Hi, welcome. Command list below:\n/list\n/exchange $<value> to CAD\n/exchange <value> USD to CAD\n/help')
                else:
                    sendMessage(chat_id, text='[-] Error: Wrong syntax.')
        else:
            sendMessage(chat_id, text='[-] Error: No such command.')

    return '<h1>Welcome to tele bot</h1>'


if __name__ == '__main__':
    app.run()

