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

import sys
import argparse
import requests
from graphviz import Digraph

parser = argparse.ArgumentParser(description='Create a flowchart of a specific token')
parser.add_argument('-u', '--url', help='Liquid securities url', required=True)
parser.add_argument('-t', '--token', help='Liquid securities authorization token', required=True)
parser.add_argument('-a', '--asset', help='Asset uuid', required=True)
parser.add_argument('-f', '--file', help='Output file', required=True)
args = parser.parse_args()

asset_response = requests.get(args.url+'/api/assets/'+args.asset, \
    headers={'content-type': 'application/json', 'Authorization': 'token '+args.token})
if asset_response.status_code != 200:
    print('ERROR')
    sys.exit(1)
investors_restricted = asset_response.json()['investors_restricted']

ls_response = requests.get(args.url+'/api/assets/'+args.asset+'/activities', \
    headers={'content-type': 'application/json', 'Authorization': 'token '+args.token})

if ls_response.status_code != 200:
    print('ERROR')
    sys.exit(1)

nodes = []
arcs = []
for activity in ls_response.json():
    if activity['type'] == 'issuance':
        node = nodes.append({'shape':'doublecircle', 'name': 'ISSUER'})
    elif activity['type'] == 'reissuance':
        node = nodes.append({'shape': 'doublecircle', 'name': 'ISSUER'})
    elif activity['type'] == 'burn':
        node = nodes.append({'shape': 'doublecircle', 'name': 'BURN'})
    else:
         gaid = activity['GAID']
         if  gaid is None:
            gaid = 'ISSUER'
            #node = nodes.append({'shape': 'doublecircle', 'name': 'ISSUER'})
         else:
            investor = activity['investor']
            if investor is None:
                node = nodes.append({'shape':'box', 'name': gaid})
            else:
                #node = nodes.append({'shape':'diamond', 'name': str(activity['investor']) + ' ' +  gaid})
                node = nodes.append({'shape':'diamond', 'name': gaid})

for activity in ls_response.json():
    if activity['type'] == 'issuance':
        arcs.append({'in': 'ISSUER', 'out': 'ISSUER', 'text': activity['description'] + ' (' + str(activity['amount']) + ' tokens)'})
    elif activity['type'] == 'reissuance':
        arcs.append({'in': 'ISSUER', 'out': 'ISSUER', 'text': activity['description'] + ' (' + str(activity['amount']) + ' tokens)'})
    else:
        inputs = []
        explorer_response = requests.get('https://blockstream.info/liquid/api/tx/'+activity["txid"]).json();
        for vin in explorer_response['vin']:
            for activity_scan in ls_response.json():
                if (activity_scan['txid'] == vin['txid']) and (activity_scan['vout'] == vin['vout']):
                    gaid = activity_scan['GAID']
                    if  gaid is None:
                         gaid = 'ISSUER'
                    inputs.append(gaid)

        for txid in inputs:
            gaid = activity['GAID']
            if  gaid is None:
                 gaid = 'ISSUER'
            arcs.append({'in': txid, 'out':  gaid, 'text': activity['description'] + ' (' + str(activity['amount']) + ' tokens)'})

f = Digraph('Token: '+args.asset, filename=args.file+'.gv')
f.graph_attr.update(dpi="600")
f.attr(rankdir='LR', size='8,5', label='Token: '+args.asset, labelloc='t')
for node in nodes:
    f.attr('node', shape=node['shape'])
    f.node(node['name'])
f.attr('node', shape='box')
for arc in arcs:
    f.edge(arc['in'], arc['out'], label=arc['text'])
f.render(format='png')
