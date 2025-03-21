from flask import Blueprint, request, jsonify
# from web3 import Web3
from web3 import Web3
from eth_account.messages import encode_defunct
from eth_account import Account
import os
import json
from datetime import datetime

payments_bp = Blueprint('payments', __name__)

# Initialize Web3
INFURA_URL = os.getenv('INFURA_URL', 'https://mainnet.infura.io/v3/YOUR_INFURA_KEY')
web3 = Web3(Web3.HTTPProvider(INFURA_URL))

# Relayer wallet
RELAYER_PRIVATE_KEY = os.getenv('RELAYER_PRIVATE_KEY')
relayer_account = Account.from_key(RELAYER_PRIVATE_KEY) if RELAYER_PRIVATE_KEY else None

# Load ABI for ERC20 with permit
with open('app/contracts/ERC20WithPermit.json', 'r') as f:
    contract_json = json.load(f)
    CONTRACT_ABI = contract_json['abi']

@payments_bp.route('/health', methods=['GET'])
def health_check():
    """Endpoint to check if the relayer is online and connected to Ethereum"""
    if web3.is_connected():
        return jsonify({
            'status': 'online',
            'ethereum_connected': True,
            'relayer_address': relayer_account.address if relayer_account else None,
            'current_block': web3.eth.block_number
        })
    return jsonify({
        'status': 'online',
        'ethereum_connected': False
    }), 500

@payments_bp.route('/submit-transaction', methods=['POST'])
def submit_transaction():
    """
    Endpoint to submit a gasless transaction using EIP-2612 permit
    
    Expected payload:
    {
        "token_address": "0x...",
        "sender": "0x...",
        "recipient": "0x...",
        "amount": "1000000000000000000", // Wei amount as string
        "deadline": 1729142399, // Unix timestamp
        "nonce": 1, // EIP-2612 nonce (from contract)
        "signature": {
            "v": 27,
            "r": "0x...",
            "s": "0x..."
        }
    }
    """
    try:
        data = request.get_json()
        
        # Validate request data
        required_fields = ['token_address', 'sender', 'recipient', 'amount', 'deadline', 'nonce', 'signature']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Missing required field: {field}'}), 400
        
        # Get signature components
        v, r, s = data['signature']['v'], data['signature']['r'], data['signature']['s']
        
        # Connect to the token contract
        token_contract = web3.eth.contract(
            address=Web3.to_checksum_address(data['token_address']),
            abi=CONTRACT_ABI
        )
        
        # Convert amount to int if it's a string
        amount = int(data['amount']) if isinstance(data['amount'], str) else data['amount']
        
        # Verify signature and token balance
        sender = Web3.to_checksum_address(data['sender'])
        recipient = Web3.to_checksum_address(data['recipient'])
        
        # Check sender's balance
        balance = token_contract.functions.balanceOf(sender).call()
        if balance < amount:
            return jsonify({'error': f'Insufficient balance. User has {balance}, but {amount} is required'}), 400
        
        # Build and send the transaction
        try:
            # First, call permit to approve spending
            permit_tx = token_contract.functions.permit(
                sender,                      # owner
                relayer_account.address,     # spender
                amount,                      # value
                data['deadline'],            # deadline
                v, r, s                      # signature components
            ).build_transaction({
                'from': relayer_account.address,
                'nonce': web3.eth.get_transaction_count(relayer_account.address),
                'gas': 100000,
                'gasPrice': web3.eth.gas_price
            })
            
            # Sign and send permit transaction
            signed_permit_tx = web3.eth.account.sign_transaction(permit_tx, RELAYER_PRIVATE_KEY)
            permit_tx_hash = web3.eth.send_raw_transaction(signed_permit_tx.rawTransaction)
            permit_receipt = web3.eth.wait_for_transaction_receipt(permit_tx_hash)
            
            if permit_receipt.status != 1:
                return jsonify({'error': 'Permit transaction failed'}), 500
            
            # Then, transfer the tokens
            transfer_tx = token_contract.functions.transferFrom(
                sender,
                recipient,
                amount
            ).build_transaction({
                'from': relayer_account.address,
                'nonce': web3.eth.get_transaction_count(relayer_account.address),
                'gas': 100000,
                'gasPrice': web3.eth.gas_price
            })
            
            # Sign and send transfer transaction
            signed_transfer_tx = web3.eth.account.sign_transaction(transfer_tx, RELAYER_PRIVATE_KEY)
            transfer_tx_hash = web3.eth.send_raw_transaction(signed_transfer_tx.rawTransaction)
            
            return jsonify({
                'status': 'success',
                'permit_tx_hash': permit_tx_hash.hex(),
                'transfer_tx_hash': transfer_tx_hash.hex(),
                'message': 'Transaction submitted to blockchain'
            })
            
        except Exception as e:
            print(f"Transaction error: {str(e)}")
            return jsonify({'error': str(e)}), 500
    
    except Exception as e:
        print(f"Server error: {str(e)}")
        return jsonify({'error': str(e)}), 500

@payments_bp.route('/verify-signature', methods=['POST'])
def verify_signature():
    """Endpoint to verify an EIP-2612 permit signature"""
    try:
        data = request.get_json()
        
        # Validate request
        required_fields = ['token_address', 'sender', 'recipient', 'amount', 'deadline', 'nonce', 'signature']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Missing required field: {field}'}), 400
        
        # Get signature components
        v, r, s = data['signature']['v'], data['signature']['r'], data['signature']['s']
        
        # Connect to the token contract
        token_contract = web3.eth.contract(
            address=Web3.to_checksum_address(data['token_address']),
            abi=CONTRACT_ABI
        )
        
        # Attempt to recover the signer (this varies by token implementation)
        # This is a simplification - actual implementation depends on the token contract
        domain_separator = token_contract.functions.DOMAIN_SEPARATOR().call()
        permit_type_hash = token_contract.functions.PERMIT_TYPEHASH().call()
        
        # We would need the actual contract method to verify the signature
        # This is just a placeholder response
        return jsonify({
            'status': 'simulated',
            'message': 'Signature verification simulated. In production, this would verify the signature against the contract.'
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500 