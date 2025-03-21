# KiwiPay - Gasless ERC20 Payment System

KiwiPay is a subsidized payment system that allows users to send ERC20 tokens without paying for gas fees. The system uses the EIP-2612 permit standard along with a relayer to perform the transactions on behalf of the user.

## How It Works

1. **User Signs a Permit Message**: Instead of sending an `approve` transaction, the user signs a permit message using their wallet (e.g., MetaMask). This signature authorizes the relayer to spend a specific amount of tokens.

2. **Signature is Sent to Relayer**: The signed message is sent to our backend.

3. **Relayer Verifies and Executes**: Our relayer verifies the signature and executes two transactions:
   - First, it calls the `permit()` function to set the allowance.
   - Then, it calls `transferFrom()` to transfer the tokens from the user to the recipient.

4. **Gas Fees are Covered**: The relayer pays for the gas fees, making the transaction gasless for the user.

## Technical Architecture

### Backend (Flask)

- **Flask API**: Handles incoming signature requests and relays transactions to the blockchain.
- **Web3.py**: Interacts with Ethereum blockchain.
- **eth_account**: Handles signature verification.

### Smart Contracts

- **ERC20 with Permit**: Standard ERC20 token with EIP-2612 permit functionality.

### Frontend

- **Web Interface**: Allows users to connect their wallet and sign permit messages.
- **Web3.js/ethers.js**: Handles wallet connection and signing.

## Prerequisites

- Python 3.7+
- Flask
- Web3.py
- MetaMask or compatible wallet
- Infura account or other Ethereum node provider

## Installation

1. Clone the repository:
```
git clone https://github.com/yourusername/kiwipay.git
cd kiwipay
```

2. Install required packages:
```
pip install -r requirements.txt
```

3. Create a `.env` file based on `.env.example` and fill in your configuration:
```
cp .env.example .env
# Edit .env with your values
```

4. Run the application:
```
python run.py
```

## API Endpoints

### `POST /api/submit-transaction`

Submit a signed permit and execute a token transfer.

**Request Body**:
```json
{
  "token_address": "0x...",
  "sender": "0x...",
  "recipient": "0x...",
  "amount": "1000000000000000000",
  "deadline": 1729142399,
  "nonce": 1,
  "signature": {
    "v": 27,
    "r": "0x...",
    "s": "0x..."
  }
}
```

**Response**:
```json
{
  "status": "success",
  "permit_tx_hash": "0x...",
  "transfer_tx_hash": "0x...",
  "message": "Transaction submitted to blockchain"
}
```

## Notes for Deployment

### Security Considerations
- Protect the relayer's private key
- Implement rate limiting
- Add additional signature verification
- Consider implementing a business model to recoup gas costs

### Supported Tokens
Only ERC20 tokens that implement the EIP-2612 permit standard can be used with this system. Common examples include:
- DAI
- USDC
 