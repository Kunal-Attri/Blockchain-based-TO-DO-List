import socket

from lib.Blockchain import Blockchain
from lib.User import user_main
from lib.Users_DB import authenticate_user, add_user
from lib.Utilities import get_integer, uuid
from flask import Flask, jsonify, request
import requests
from threading import Thread
from time import sleep

# Initiating the blockchain
blockchain = Blockchain()

# Initiating the Node
app = Flask(__name__)
node_thread = None

MAIN_SERVER = 'http://172.25.169.52:5000'
blockchain.register_node(MAIN_SERVER)


# for nodes
@app.route('/chain', methods=['GET'])
def full_chain():
    response = {
        'chain': blockchain.chain,
        'length': len(blockchain.chain),
    }
    return jsonify(response), 200


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
    print(blockchain.nodes)
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
4. Start Server node
5. Add peer nodes
6. Remove peer nodes
7. Exit""")
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
        print(f'Chain: f{blockchain.chain}')
    elif inp == 4:
        port = get_integer("Port (default - 5000): ", defaultVal=5000)
        node_thread = Thread(target=node_server, args=[port])
        node_thread.daemon = True
        node_thread.start()
        ip = "http://"
        ip += f"{extract_ip()}:{port}"
        requests.post(f"{MAIN_SERVER}/nodes/register", json={"nodes": [ip], "new": 'True'})
        sleep(2)
        blockchain.resolve_conflicts()
    elif inp == 5:
        node_address = input("Peer node address('http://ip:port): ")
        added = blockchain.register_node(node_address)
        if added:
            print('Node added...')
            print(f'Peer nodes: {blockchain.nodes}')
    elif inp == 6:
        node_address = input("Peer node address(same as entered previously): ")
        blockchain.unregister_nodes(node_address)
    elif inp == 7:
        exit()
