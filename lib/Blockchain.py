import hashlib
import json
from time import time, sleep
from urllib.parse import urlparse
import requests
from random import randint, random

from lib.Utilities import uuid, get_hash


class Blockchain:
    def __init__(self):
        self.current_transactions = []
        self.chain = []
        self.nodes = set()
        self.tries = 1
        self.my_ip = ''
        self.update_lock = False

        # default 1st block
        self.new_block(previous_hash='1', proof=100)

    def lock(self):
        if not self.update_lock:
            self.update_lock = True
            return 1
        else:
            return 0

    def unlock(self):
        if self.update_lock:
            self.update_lock = False
            return 1
        else:
            return 0

    def register_node(self, address):
        parsed_url = urlparse(address)
        if parsed_url.netloc:
            self.nodes.add(parsed_url.netloc)
            return True
        elif parsed_url.path:
            self.nodes.add(parsed_url.path)
            return True
        else:
            print('Invalid URL')
            return False

    def unregister_node(self, address):
        parsed_url = urlparse(address)
        if parsed_url.netloc in self.nodes:
            self.nodes.remove(parsed_url.netloc)
            return True
        elif parsed_url.path in self.nodes:
            self.nodes.remove(parsed_url.path)
            return True
        else:
            print('Invalid URL')
            return False

    def valid_chain(self, chain):
        last_block = chain[0]
        current_index = 1

        while current_index < len(chain):
            block = chain[current_index]
            # print(f'{last_block}')
            # print(f'{block}')
            # print("\n-----------\n")
            last_block_hash = self.hash(last_block)
            if block['previous_hash'] != last_block_hash:
                return False

            if not self.valid_proof(last_block['proof'], block['proof'], last_block_hash):
                return False

            last_block = block
            current_index += 1
        return True

    def resolve_conflicts(self):
        neighbours = self.nodes
        new_chain = None

        max_length = len(self.chain)

        for node in neighbours:
            if f'http://{node}' != self.my_ip:
                response = requests.get(f'http://{node}/chain')

                if response.status_code == 200:
                    length = response.json()['length']
                    chain = response.json()['chain']

                    if length >= max_length and self.valid_chain(chain):
                        max_length = length
                        new_chain = chain

        if new_chain:
            self.chain = new_chain
            return True
        return False

    def update_peers(self):
        print('Chain updated broadcast...')
        for node in self.nodes:
            if f'http://{node}' != self.my_ip:
                requests.get(f'http://{node}/chain/update')

    def new_block(self, proof, previous_hash):
        block = {
            'index': len(self.chain) + 1,
            'timestamp': time(),
            'transactions': self.current_transactions,
            'proof': proof,
            'previous_hash': previous_hash or self.hash(self.chain[-1]),
        }
        self.chain.append(block)
        self.update_peers()
        self.resolve_conflicts()
        if self.chain[-1]['transactions'] == self.current_transactions:
            print('Block was added successfully!')
            self.current_transactions = []
            self.tries = 1
        else:
            if self.tries <= 5:
                t = randint(3, 2*len(self.nodes)) ** self.tries
                print(f"Block couldn't be added due to some error! Trying again...after {t} secs")
                sleep(t)
                self.tries += 1
                block = self.commit_block()
            else:
                print("Block addition aborted!!!")
                self.tries = 1
        return block

    def new_transaction(self, user_id, work_info, completed=0, work_id=None):
        if work_id is None:
            work_id = uuid()
        self.current_transactions.append({
            'user_id': user_id,
            'work_id': work_id,
            'work_info': work_info,
            'completed': completed
        })
        return self.last_block['index'] + 1

    @property
    def last_block(self):
        return self.chain[-1]

    @staticmethod
    def hash(block):
        block_string = json.dumps(block, sort_keys=True)
        return get_hash(block_string)

    def proof_of_work(self, last_block):
        last_proof = last_block['proof']
        last_hash = self.hash(last_block)

        proof = 0
        while self.valid_proof(last_proof, proof, last_hash) is False:
            proof += 1
        return proof

    @staticmethod
    def valid_proof(last_proof, proof, last_hash):
        guess = f'{last_proof}{proof}{last_hash}'.encode()
        guess_hash = hashlib.sha256(guess).hexdigest()
        return guess_hash[:4] == "0000"

    def get_work_info(self, work_id):
        for transaction in self.current_transactions:
            if transaction['work_id'] == work_id:
                return transaction.get('work_info', '')
        for block in self.chain:
            for transaction in block.get('transactions', []):
                if transaction['work_id'] == work_id:
                    return transaction.get('work_info', '')
        return None

    def check_completed(self, word_id):
        for transaction in self.current_transactions:
            if transaction['work_id'] == word_id and transaction['completed'] == 1:
                return True
        for block in self.chain:
            for transaction in block.get('transactions', []):
                if transaction['work_id'] == word_id and transaction['completed'] == 1:
                    return True
        return False

    def commit_block(self):
        lock = False
        while not lock and len(self.chain) > 1:
            if 'http://172.25.169.52:5000' != self.my_ip:
                resp = requests.post('http://172.25.169.52:5000/getlock')
                if resp.status_code == 200:
                    lock = True
                else:
                    t = random() * 5
                    print(f"Another block addition in process, Trying again...after {t} secs")
                    sleep(t)
            else:
                if self.lock():
                    lock = True
                else:
                    t = random() * 5
                    print(f"Another block addition in process, Trying again...after {t} secs")
                    sleep(t)

        last_block = self.last_block
        proof = self.proof_of_work(last_block)

        previous_hash = self.hash(last_block)
        block = self.new_block(proof, previous_hash)
        while lock and len(self.chain) > 1:
            if 'http://172.25.169.52:5000' != self.my_ip:
                print(self.my_ip)
                resp = requests.post('http://172.25.169.52:5000/releaselock')
                if resp.status_code == 201:
                    lock = False
            else:
                if self.unlock():
                    lock = False
                else:
                    t = random() * 5
                    print(f"Another block removal in process, Trying again...after {t} secs")
                    sleep(t)
        return block
