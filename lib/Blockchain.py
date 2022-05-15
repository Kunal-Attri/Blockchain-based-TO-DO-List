import hashlib
import json
from time import time
from urllib.parse import urlparse
import requests

from lib.Utilities import uuid, get_hash


class Blockchain:
    def __init__(self):
        self.current_transactions = []
        self.chain = []
        self.nodes = set()

        # default 1st block
        self.new_block(previous_hash='1', proof=100)

    def register_node(self, address):
        parsed_url = urlparse(address)
        if parsed_url.netloc:
            self.nodes.add(parsed_url.netloc)
        elif parsed_url.path:
            self.nodes.add(parsed_url.path)
        else:
            raise ValueError('Invalid URL')

    def valid_chain(self, chain):
        last_block = chain[0]
        current_index = 1

        while current_index < len(chain):
            block = chain[current_index]
            print(f'{last_block}')
            print(f'{block}')
            print("\n-----------\n")
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
            response = requests.get(f'http://{node}/chain')

            if response.status_code == 200:
                length = response.json()['length']
                chain = response.json()['chain']

                if length > max_length and self.valid_chain(chain):
                    max_length = length
                    new_chain = chain

        if new_chain:
            self.chain = new_chain
            return True
        return False

    def new_block(self, proof, previous_hash):
        block = {
            'index': len(self.chain) + 1,
            'timestamp': time(),
            'transactions': self.current_transactions,
            'proof': proof,
            'previous_hash': previous_hash or self.hash(self.chain[-1]),
        }

        self.current_transactions = []
        self.chain.append(block)
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
        last_block = self.last_block
        proof = self.proof_of_work(last_block)

        previous_hash = self.hash(last_block)
        block = self.new_block(proof, previous_hash)
        return block
