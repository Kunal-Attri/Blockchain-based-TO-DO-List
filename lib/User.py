from lib.Utilities import get_integer
from tabulate import tabulate


class User:
    def __init__(self, user_id, blockchain):
        self.usr_id = user_id
        self.blockchain = blockchain

    def commit(self):
        block = self.blockchain.commit_block()
        print(f"New block forged...")
        print(f"Index: {block['index']}")
        print(f"Transactions: {block['transactions']}")
        print(f"Proof: {block['proof']}")
        print(f"Previous hash: {block['previous_hash']}\n")

    def transaction(self, work_info, work_id=None):
        if work_id is None:
            self.blockchain.new_transaction(self.usr_id, work_info)
        else:
            self.blockchain.new_transaction(self.usr_id, work_info, 1, work_id)
        txn = self.blockchain.current_transactions[-1]
        print('\nWork details:-')
        print(f"User ID: {txn['user_id']}")
        print(f"Work ID: {txn['work_id']}")
        print(f"Work Info: {txn['work_info']}")
        print(f"Completed: {bool(txn['completed'])}")

        if len(self.blockchain.current_transactions) >= 3:
            print("\nBlock full...committing block into chain")
            self.commit()

    def add_work(self):
        work_info = input("Work Info: ")
        if work_info == '':
            print('Provide work info...')
            return
        self.transaction(work_info)

    def mark_completed(self):
        work_id = input('Work ID: ')
        if work_id == '':
            print('Provide valid Work ID')
            return

        work_info = self.blockchain.get_work_info(work_id)
        if work_info is not None:
            if not self.blockchain.check_completed(work_id):
                self.transaction(work_info, work_id)
            else:
                print(f'Work with details:\nWork ID: {work_id}\nWork Info: {work_info}\nalready completed...')
        else:
            print("Invalid Work ID...")

    def show_works(self):
        work_ids = []
        data = []
        for block in self.blockchain.chain:
            for txn in block.get('transactions', []):
                if txn['user_id'] == self.usr_id:
                    w_id = txn['work_id']
                    if w_id not in work_ids:
                        data.append([w_id, txn['work_info'], self.blockchain.check_completed(w_id)])
                        work_ids.append(w_id)
        for txn in self.blockchain.current_transactions:
            if txn['user_id'] == self.usr_id:
                w_id = txn['work_id']
                if w_id not in work_ids:
                    data.append([w_id, txn['work_info'], self.blockchain.check_completed(w_id)])
                    work_ids.append(w_id)
        print()
        if data:
            data = data[::-1]
            print(f'Work details for User ID: {self.usr_id}:-')
            print(tabulate(data, headers=['Work ID', 'Work Info', 'Completed']))
        else:
            print('No works found for this user...')


def user_main(usr_id, blockchain):
    user = User(usr_id, blockchain)
    while True:
        print('''
1. Add a new work
2. Mark a work as completed
3. Show my works' details
4. Logout''')
        inp = get_integer("\nInput: ")
        if inp == 1:
            user.add_work()
        elif inp == 2:
            user.mark_completed()
        elif inp == 3:
            user.show_works()
        elif inp == 4:
            if len(user.blockchain.current_transactions) >= 1:
                user.commit()
            return
        else:
            print('Invalid Input...')
