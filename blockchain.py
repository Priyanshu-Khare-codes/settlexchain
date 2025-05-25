# utils/blockchain.py

from web3 import Web3
from dotenv import load_dotenv
import json
import os

load_dotenv()

# Connect to BNB Chain Testnet
web3 = Web3(Web3.HTTPProvider("https://data-seed-prebsc-1-s1.binance.org:8545/"))

# Load ABI
with open("contract_abi.json") as f:
    contract_abi = json.load(f)

# Contract address (set your actual deployed contract address here)
CONTRACT_ADDRESS = Web3.to_checksum_address("0x30d97Db299f01D748c2Ba3e486A7051E2FD49436")

# Load Contract
contract = web3.eth.contract(address=CONTRACT_ADDRESS, abi=contract_abi)

# Your backend's wallet private key for signing transactions
PRIVATE_KEY = os.getenv("PRIVATE_KEY")  # put this in a .env or secure vault
BACKEND_ADDRESS = web3.eth.account.from_key(PRIVATE_KEY).address
