#  dP oo                   oo       dP               oo
#  88                               88
#  88 dP .d8888b. dP    dP dP .d888b88    dP  dP  dP dP 88d888b. .d8888b.
#  88 88 88'  `88 88    88 88 88'  `88    88  88  88 88 88'  `88 88ooood8
#  88 88 88.  .88 88.  .88 88 88.  .88 dP 88.88b.88' 88 88    88 88.  ...
#  dP dP `8888P88 `88888P' dP `88888P8 88 8888P Y8P  dP dP    dP `88888P'
#              88
#              dP
#
#    MIT License - Valerio Vaccaro 2020
#    Based on open source code

from flask import Flask, request, send_from_directory
from flask_stache import render_template
from flask_qrcode import QRcode
from flask_socketio import SocketIO
from bitcoin_rpc_class import RPCHost
import os
import configparser
import mysql.connector
import json
import requests
import string
import random
import wallycore as wally
from flask import jsonify

import numpy as np
import pandas as pd
from plotnine import *

app = Flask(__name__, static_url_path='/static')
qrcode = QRcode(app)

socketio = SocketIO(app)

config = configparser.RawConfigParser()
config.read('liquid.conf')

rpcHost = config.get('LIQUID', 'host')
rpcPort = config.get('LIQUID', 'port')
rpcUser = config.get('LIQUID', 'username')
rpcPassword = config.get('LIQUID', 'password')
rpcPassphrase = config.get('LIQUID', 'passphrase')
serverURL = 'http://{}:{}@{}:{}'.format(rpcUser, rpcPassword, rpcHost, rpcPort)

myHost = config.get('MYSQL', 'host')
myUser = config.get('MYSQL', 'username')
myPasswd = config.get('MYSQL', 'password')
myDatabase = config.get('MYSQL', 'database')

secToken = config.get('SECURITY', 'token')
secFixedGaid = config.get('SECURITY', 'fixedGaid')
secAuthorizerAddress = config.get('SECURITY', 'authorizerAddress')

betaToken = config.get('BETA', 'token')
betaFixedGaid = config.get('BETA', 'fixedGaid')
betaAuthorizerAddress = config.get('BETA', 'authorizerAddress')

host = RPCHost(serverURL)
if (len(rpcPassphrase) > 0):
    result = host.call('walletpassphrase', rpcPassphrase, 60)


@app.route('/.well-known/<path:filename>')
def wellKnownRoute(filename):
    return send_from_directory('{}/well-known/'.format(app.root_path), filename, conditional=True)


def parse_signed_request(request):
    if not isinstance(request, dict) or \
            set(request.keys()) != {'message', 'signature'} or \
            not isinstance(request['message'], dict) or \
            not isinstance(request['signature'], str):
        return None, 'Unexpected formatting'

    signature = request['signature']
    message_dict = request['message']
    message_str = json.dumps(message_dict, separators=(',', ':'), sort_keys=True).encode('ascii').decode()

    response = host.call('verifymessage', secAuthorizerAddress, signature, message_str)
    if not response:
        return None, 'Invalid signature'

    return message_dict, ''


@app.route('/issuerauthorizer', methods=['POST'])
def issuerauthorizer():
    json_message = request.get_json(force=True)
    message, error = parse_signed_request(json_message)

    ONLY_GAIDS_CAN_SEND = [secFixedGaid]

    mydb = mysql.connector.connect(host=myHost, user=myUser, passwd=myPasswd, database=myDatabase)
    mycursor = mydb.cursor()
    sql = "SELECT GAID FROM liquid_wine_gaids"
    mycursor.execute(sql)
    results = mycursor.fetchall()
    mydb.close()

    for row in results:
        ONLY_GAIDS_CAN_SEND.append(row[0])

    json_result = {
      'result': True,
      'error': '',
    }

    if message is None:
        json_result = {
          'result': False,
          'error': error,
        }

    else:
        i = 0
        total_in = 0
        for row in message['request']['inputs']:
            total_in = total_in + row['amount']
            if row['gaid'] not in ONLY_GAIDS_CAN_SEND:
                json_result = {
                  'result': False,
                  'error': 'Unauthorized GAID (#{} input)'.format(i),
                }
            i = i + 1

        i = 0
        total_out = 0
        for row in message['request']['outputs']:
            total_out = total_out + row['amount']
            if row['gaid'] not in ONLY_GAIDS_CAN_SEND:
                json_result = {
                  'result': False,
                  'error': 'Unauthorized GAID (#{} output)'.format(i),
                }
            i = i + 1

        if not total_in == total_out:
            json_result = {
              'result': False,
              'error': 'Different amounts',
            }

    mydb = mysql.connector.connect(host=myHost, user=myUser, passwd=myPasswd, database=myDatabase)
    mycursor = mydb.cursor()
    sql = "INSERT IGNORE INTO liquid_wine_auth (Message, Result) VALUES (%s, %s)"
    val = (json.dumps(json_message), json.dumps(json_result))
    mycursor.execute(sql, val)
    mydb.commit()
    mydb.close()

    return jsonify(json_result)


@app.route('/')
def home():
    tokens = []
    token = requests.get('https://securities.blockstream.com/api/assets/df36e373-82c9-4412-a993-50c4ae12db6f', \
        headers={'content-type': 'application/json', 'Authorization': 'token {}'.format(secToken)}).json()
    tokens.append(token)
    data = {
        'tokens': tokens,
    }
    return render_template('home', **data)


@app.route('/authorizer')
def authorizer():
    command = request.args.get('command')
    gaid = request.args.get('gaid')

    validate = {'error': ''}

    if command is not None:
        if command=='add' and gaid is not None:
            validate = requests.get('https://securities.blockstream.com/api/gaids/{}/validate'.format(gaid), \
                headers={'content-type': 'application/json', 'Authorization': 'token {}'.format(secToken)}).json()

            if validate['is_valid']:
                mydb = mysql.connector.connect(host=myHost, user=myUser, passwd=myPasswd, database=myDatabase)
                mycursor = mydb.cursor()
                sql = 'INSERT IGNORE INTO liquid_wine_gaids (GAID) VALUES ("{}")'.format(gaid)
                val = (gaid)
                mycursor.execute(sql, val)
                mydb.commit()
                mydb.close()

        if command=='delete' and gaid is not None:
            mydb = mysql.connector.connect(host=myHost, user=myUser, passwd=myPasswd, database=myDatabase)
            mycursor = mydb.cursor()
            sql = 'DELETE FROM liquid_wine_gaids WHERE GAID="{}"'.format(gaid)
            mycursor.execute(sql)
            mydb.commit()
            mydb.close()

    mydb = mysql.connector.connect(host=myHost, user=myUser, passwd=myPasswd, database=myDatabase)
    mycursor = mydb.cursor()
    sql = "SELECT Timestamp, Message, Result FROM liquid_wine_auth"
    mycursor.execute(sql)
    results = mycursor.fetchall()
    mydb.close()

    auths = [{'timestamp': row[0], 'request': row[1], 'result': row[2]} for row in results]

    mydb = mysql.connector.connect(host=myHost, user=myUser, passwd=myPasswd, database=myDatabase)
    mycursor = mydb.cursor()
    sql = "SELECT Timestamp, GAID FROM liquid_wine_gaids"
    mycursor.execute(sql)
    results = mycursor.fetchall()
    mydb.close()

    gaids = [{'timestamp': row[0], 'gaid': row[1]} for row in results]

    data = {
        'gaids': gaids,
        'auths': auths,
        'gaid_validate': validate['error'],
    }
    return render_template('authorizer', **data)


@app.route('/utxos')
def utxos():
    command = request.args.get('command')
    txid = request.args.get('txid')
    vout = request.args.get('vout')

    if command is not None:
        if command=='lock' and txid is not None and vout is not None:
            res = requests.post('https://securities.blockstream.com/api/assets/df36e373-82c9-4412-a993-50c4ae12db6f/utxos/blacklist', \
                headers={'content-type': 'application/json', 'Authorization': 'token {}'.format(secToken)}, \
                data=json.dumps([{'txid': txid, 'vout': int(vout)}])).json()

        if command=='unlock' and txid is not None and vout is not None:
            res = requests.post('https://securities.blockstream.com/api/assets/df36e373-82c9-4412-a993-50c4ae12db6f/utxos/whitelist', \
                headers={'content-type': 'application/json', 'Authorization': 'token {}'.format(secToken)}, \
                data=json.dumps([{'txid': txid, 'vout': int(vout)}])).json()

    utxos = requests.get('https://securities.blockstream.com/api/assets/df36e373-82c9-4412-a993-50c4ae12db6f/utxos', \
        headers={'content-type': 'application/json', 'Authorization': 'token {}'.format(secToken)}).json()

    data = {
        'utxos': utxos,
    }
    return render_template('utxos', **data)


@app.route('/stats')
def stats():
    os.system('python flowchart.py -u "https://securities.blockstream.com" -t "{}" -a "df36e373-82c9-4412-a993-50c4ae12db6f" -f "flowchart"'.format(secToken))
    os.system('mv flowchart.gv.png static/flowchart.png')
    os.system('rm flowchart.gv')

    activities = requests.get('https://securities.blockstream.com/api/assets/df36e373-82c9-4412-a993-50c4ae12db6f/activities', \
        headers={'content-type': 'application/json', 'Authorization': 'token {}'.format(secToken)}).json()

    random_list = [random.choice(string.ascii_letters + string.digits) for n in range(32)]
    random_str = "".join(random_list)

    data = {
        'random': random_str,
        'activities': activities,
    }
    return render_template('stats', **data)


@app.route('/balance')
def balance():
    confirmed_balance = requests.get('https://securities.blockstream.com/api/assets/df36e373-82c9-4412-a993-50c4ae12db6f/balance', \
        headers={'content-type': 'application/json', 'Authorization': 'token {}'.format(secToken)}).json()['confirmed_balance']

    # convert to pandas dataframe
    data = np.array([(e['GAID'], e['owner'], e['amount']) for e in confirmed_balance])
    df = pd.DataFrame({'gaid': data[:, 0], 'owner': data[:, 1], 'amount': data[:, 2]})
    df.replace(to_replace=[None], value=np.nan, inplace=True)

    # plot distribution
    plt1 = ggplot(df, aes(x='gaid', y='amount', fill='gaid')) + \
        geom_col() +   \
        coord_flip() + \
        scale_fill_brewer(type='div', palette="Spectral") + \
        labs(title ='Balance', x = 'GAID', y = 'Tokens')

    ggsave(filename="static/gaid_balance.png", plot=plt1, device='png', dpi=300)

    random_list = [random.choice(string.ascii_letters + string.digits) for n in range(32)]
    random_str = "".join(random_list)

    data = {
        'random': random_str,
        'confirmed_balance': confirmed_balance,
    }
    return render_template('balance', **data)

@app.route('/status')
def status():
    print(betaToken)
    beta_info = requests.get('https://securities-beta.blockstream.com/api/info', \
        headers={'content-type': 'application/json', 'Authorization': 'token {}'.format(betaToken)}).json()
    beta_changelog = requests.get('https://securities-beta.blockstream.com/api/changelog', \
        headers={'content-type': 'application/json', 'Authorization': 'token {}'.format(betaToken)}).json()
    prod_info = requests.get('https://securities.blockstream.com/api/info', \
        headers={'content-type': 'application/json', 'Authorization': 'token {}'.format(secToken)}).json()
    prod_changelog = requests.get('https://securities.blockstream.com/api/changelog', \
        headers={'content-type': 'application/json', 'Authorization': 'token {}'.format(secToken)}).json()

    data = {
        'beta_info': json.dumps(beta_info, indent=4),
        'beta_changelog': json.dumps(beta_changelog, indent=4),
        'prod_info': json.dumps(prod_info, indent=4),
        'prod_changelog': json.dumps(prod_changelog, indent=4),
    }
    return render_template('status', **data)

@app.route('/about')
def about():
    data = {
    }
    return render_template('about', **data)


if __name__ == '__main__':
    app.import_name = '.'
    socketio.run(app, host='0.0.0.0', port=5005)
