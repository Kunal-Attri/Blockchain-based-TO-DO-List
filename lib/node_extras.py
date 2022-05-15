@app.route('/mine', methods=['GET'])
def mine():
    block = blockchain.commit_block()
    response = {
        'message': "New Block Forged",
        'index': block['index'],
        'transactions': block['transactions'],
        'proof': block['proof'],
        'previous_hash': block['previous_hash'],
    }
    return jsonify(response), 200


@app.route('/transactions/new', methods=['POST'])
def new_transaction():
    values = request.get_json()

    required = ['user_id']
    if not all(k in values for k in required):
        return 'Missing values - user_id', 400

    user_id = values['user_id']

    # checking optional criterias and creating new transaction
    completed = values.get('completed', 0)
    if completed == 1:
        if 'work_id' in values:
            work_id = values['work_id']
            work_info = blockchain.get_work_info(work_id)
            if work_info is not None:
                index = blockchain.new_transaction(user_id, work_info, completed, work_id)
            else:
                return 'Invalid values - work_id', 400
        else:
            return 'Missing values - work_id', 400
    else:
        if 'work_info' in values:
            work_info = values['work_info']
            index = blockchain.new_transaction(user_id, work_info)
        else:
            return 'Missing values - work_info', 400

    response = {'message': f'Transaction will be added to Block {index}'}
    return jsonify(response), 201


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
    return jsonify(response), 201


@app.route('/nodes/resolve', methods=['GET'])
def consensus():
    replaced = blockchain.resolve_conflicts()

    if replaced:
        response = {
            'message': 'Our chain was replaced',
            'new_chain': blockchain.chain
        }
    else:
        response = {
            'message': 'Our chain is authoritative',
            'chain': blockchain.chain
        }
    return jsonify(response), 200