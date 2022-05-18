import socket
from tabulate import tabulate
from flask import Flask, jsonify, request
import requests
from threading import Thread
from time import sleep

from lib.Blockchain import Blockchain
from lib.User import user_main
from lib.Users_DB import authenticate_user, add_user
from lib.Utilities import get_integer, uuid


# Initiating the blockchain
blockchain = Blockchain()

# Initiating the Node
app = Flask(__name__)
node_thread = None

MAIN_SERVER = 'http://172.25.169.52:5000'
MY_IP = 'http://'
blockchain.register_node(MAIN_SERVER)



# for nodes
@app.route('/chain', methods=['GET'])
def full_chain():
    response = {
        'chain': blockchain.chain,
        'length': len(blockchain.chain),
    }
    return jsonify(response), 200


@app.route('/getlock', methods=['POST'])
def get_lock():
    update = blockchain.lock()
    if update:
        response = {
            'lock': 'True'
        }
        return jsonify(response), 200
    else:
        response = {
            'lock': 'False'
        }
        return jsonify(response), 400


@app.route('/releaselock', methods=['POST'])
def release_lock():
    update = blockchain.unlock()
    if update:
        response = {
            'released': 'True'
        }
        return jsonify(response), 201
    else:
        response = {
            'released': 'False'
        }
        return jsonify(response), 401


@app.route('/chain/update', methods=['GET'])
def update_chain():
    updated = blockchain.resolve_conflicts()
    if updated:
        print('Node synced successfully!')
    response = {
        'updated': True,
    }
    return jsonify(response), 200


@app.route('/nodes/register', methods=['POST'])
def register_nodes():
    values = request.get_json()
    nodes = values.get('nodes')
    if nodes is None:
        return "Error: Please supply a valid list of nodes", 400
    for node in nodes:
        blockchain.register_node(node)

    response = {
        'message': 'New nodes have been added',
        'total_nodes': list(blockchain.nodes),
    }
    a = list(blockchain.nodes).copy()
    a = ["http://" + i for i in a]
    if socket.gethostbyname(socket.gethostname()) == "172.25.169.52" and values.get('new') == 'True':
        for node in blockchain.nodes:
            requests.post(f"http://{node}/nodes/register", json={"nodes": a})
    return jsonify(response), 201


@app.route('/nodes/unregister', methods=['POST'])
def unregister_nodes():
    values = request.get_json()
    nodes = values.get('nodes')
    if nodes is None:
        return "Error: Please supply a valid list of nodes", 400
    for node in nodes:
        blockchain.unregister_node(node)

    response = {
        'message': 'New nodes have been removed',
        'total_nodes': list(blockchain.nodes),
    }
    if socket.gethostbyname(socket.gethostname()) == "172.25.169.52" and values.get('new') == 'True':
        for node in blockchain.nodes:
            if f'http://{node}' != MAIN_SERVER:
                requests.post(f"http://{node}/nodes/unregister", json={"nodes": nodes})
    return jsonify(response), 201


def node_server(my_port):
    app.run(host='0.0.0.0', port=my_port)


def extract_ip():
    st = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        st.connect(('10.255.255.255', 1))
        IP = st.getsockname()[0]
    except Exception:
        IP = '127.0.0.1'
    finally:
        st.close()
    return IP


while True:
    print("""
Actions: 
1. Login
2. New User
3. Show full chain
4. Show all nodes
5. Start Server node
6. Exit""")
    inp = get_integer("\nInput: ")
    if inp == 1:
        usr_id = input("User ID: ")
        if authenticate_user(usr_id):
            user_main(usr_id, blockchain)
        else:
            print("User ID not valid...")
    elif inp == 2:
        usr_id = uuid()
        add_user(usr_id)
        print(f"Your user id is: {usr_id}")
        print("You must save it now to login!")
    elif inp == 3:
        print(f'Length of chain: {len(blockchain.chain)} blocks')
        print(f'Chain: {tabulate(blockchain.chain)}')
    elif inp == 4:
        print(f'No of nodes: {len(blockchain.nodes)} nodes')
        print(f'Nodes: f{blockchain.nodes}')
    elif inp == 5:
        if len(MY_IP) <= 10:
            port = get_integer("Port (default - 5000): ", defaultVal=5000)
            node_thread = Thread(target=node_server, args=[port])
            node_thread.daemon = True
            node_thread.start()
            MY_IP += f"{extract_ip()}:{port}"
            blockchain.my_ip = MY_IP
            if MAIN_SERVER != MY_IP:
                requests.post(f"{MAIN_SERVER}/nodes/register", json={"nodes": [MY_IP], "new": 'True'})
                sleep(2)
                blockchain.resolve_conflicts()
        else:
            print('Server already running...')
    elif inp == 6:
        if len(MY_IP) > 10 and MY_IP != MAIN_SERVER:
            requests.post(f"{MAIN_SERVER}/nodes/unregister", json={"nodes": [MY_IP], "new": 'True'})
            sleep(2)
        exit()
