from greenaddress import init, Session
import configparser
import mysql.connector
import requests
import json

config = configparser.RawConfigParser()
config.read('liquid.conf')

myHost = config.get('MYSQL', 'host')
myUser = config.get('MYSQL', 'username')
myPasswd = config.get('MYSQL', 'password')
myDatabase = config.get('MYSQL', 'database')

secToken = config.get('SECURITY', 'token')
secFixedGaid = config.get('SECURITY', 'fixedGaid')
secAuthorizerAddress = config.get('SECURITY', 'authorizerAddress')
secAsset = config.get('SECURITY', 'asset')

betaToken = config.get('BETA', 'token')
betaFixedGaid = config.get('BETA', 'fixedGaid')
betaAuthorizerAddress = config.get('BETA', 'authorizerAddress')
betaAsset = config.get('BETA', 'asset')

gdkMnemonic = config.get('GDK', 'mnemonic')
gdkSubaccount = config.get('GDK', 'subaccount')

init({})
s = Session({"name":"liquid", "log_level":"info"})
s.login({}, gdkMnemonic).resolve()
s.change_settings({"unit":"sats"}).resolve()

subaccount = -1
subaccounts = s.get_subaccounts().resolve()
for sub in subaccounts['subaccounts']:
    if sub['name'] == gdkSubaccount:
        if sub['type'] != '2of2_no_recovery':
            print('Wrong subaccount type')
            exit()
        subaccount = sub['pointer']
        break

if subaccount == -1:
    print('Missing subaccount')
    exit()

balance = s.get_balance({'subaccount': subaccount, 'num_confs': 0}).resolve()[secAsset]
print(balance)

mydb = mysql.connector.connect(host=myHost, user=myUser, passwd=myPasswd, database=myDatabase)
mycursor = mydb.cursor()
sql = "UPDATE liquid_wine SET Status = 1 WHERE Status = 0"
mycursor.execute(sql)
mydb.commit()
mydb.close()

mydb = mysql.connector.connect(host=myHost, user=myUser, passwd=myPasswd, database=myDatabase)
mycursor = mydb.cursor()
sql = "SELECT Address, Amount, Asset, GAID FROM liquid_wine WHERE Status = 1"
mycursor.execute(sql)
results = mycursor.fetchall()
mydb.close()

# add my GAID to authorizer
mydb = mysql.connector.connect(host=myHost, user=myUser, passwd=myPasswd, database=myDatabase)
mycursor = mydb.cursor()
sql = 'INSERT IGNORE INTO liquid_wine_gaids (GAID) VALUES ("GA2pcpx9Yw1cDMGiSENKd81TiqD3DN")'
mycursor.execute(sql)
mydb.commit()
mydb.close()

tx_data = []
for row in results:
    tx_obj = {}
    tx_obj['satoshi'] = row[1]
    tx_obj['address'] = row[0]
    tx_obj['asset_tag'] = row[2]
    tx_data.append(tx_obj)
    # add GAID to authorizer
    mydb = mysql.connector.connect(host=myHost, user=myUser, passwd=myPasswd, database=myDatabase)
    mycursor = mydb.cursor()
    sql = 'INSERT IGNORE INTO liquid_wine_gaids (GAID) VALUES ("{}")'.format(row[3])
    mycursor.execute(sql)
    mydb.commit()
    mydb.close()

print(json.dumps(tx_data))

# unlock all locked utxos
utxos = requests.get('https://securities.blockstream.com/api/assets/df36e373-82c9-4412-a993-50c4ae12db6f/utxos', \
    headers={'content-type': 'application/json', 'Authorization': 'token {}'.format(secToken)}).json()

locked_utxos = []
for utxo in utxos:
    if utxo['blacklisted']:
        locked_utxo = {}
        locked_utxo['txid'] = utxo['txid']
        locked_utxo['vout'] = utxo['vout']
        locked_utxos.append(locked_utxo)
print(json.dumps(locked_utxos))

res = requests.post('https://securities.blockstream.com/api/assets/df36e373-82c9-4412-a993-50c4ae12db6f/utxos/whitelist', \
    headers={'content-type': 'application/json', 'Authorization': 'token {}'.format(secToken)}, \
    data=json.dumps(locked_utxos)).json()

txc = s.create_transaction({
    'subaccount': subaccount,
    'addressees': tx_data,
    }).resolve()

txg = s.sign_transaction(txc).resolve()
txs = s.send_transaction(txg).resolve()
print('Transaction sent!')
print('txhash: {}'.format(txs["txhash"]))

mydb = mysql.connector.connect(host=myHost, user=myUser, passwd=myPasswd, database=myDatabase)
mycursor = mydb.cursor()
sql = "UPDATE liquid_wine SET Status = 2, Transaction = '"+txs["txhash"]+"' WHERE Status = 1"
mycursor.execute(sql)
mydb.commit()
mydb.close()

s.disconnect()
