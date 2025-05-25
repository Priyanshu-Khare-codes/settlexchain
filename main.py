from fastapi import FastAPI, Path, HTTPException, Header, Depends, File, Form
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from eth_account.messages import encode_defunct
from eth_account import Account
from models import Group, Transaction, ChatRequest
from blockchain import contract, web3, BACKEND_ADDRESS, PRIVATE_KEY
from web3 import Web3
from ai_service import get_ai_response  
import jwt
import uvicorn
import json

app = FastAPI()
SECRET = "supersecret"

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

class AuthRequest(BaseModel):
    address: str
    message: str
    signature: str

# 🔐 Authentication Endpoint
@app.post("/authenticate")
def authenticate(auth: AuthRequest):
    message = encode_defunct(text=auth.message)
    recovered_address = Account.recover_message(message, signature=auth.signature)

    if recovered_address.lower() != auth.address.lower():
        raise HTTPException(status_code=401, detail="Invalid signature")

    token = jwt.encode({"address": auth.address}, SECRET, algorithm="HS256")
    return {"token": token}

# ✅ Dependency to verify token
def verify_token(authorization: str = Header(...)):
    try:
        token = authorization.split(" ")[1]
        decoded = jwt.decode(token, SECRET, algorithms=["HS256"])
        return decoded["address"]
    except:
        raise HTTPException(status_code=403, detail="Invalid or expired token")
    
# ✅ Protected route example
@app.get("/protected")
def protected_route(user_address: str = Depends(verify_token)):
    return {"msg": f"Hello, {user_address}. You're authorized!"}

security = HTTPBearer()

def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    try:
        payload = jwt.decode(credentials.credentials, SECRET, algorithms=["HS256"])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")

def get_data():
    with open("contracts.json", "r") as f:
        data = json.load(f)
        return data
    
@app.get("/contracts/{wallet_id}")
async def get_contracts(
    wallet_id: str = Path(..., description="Wallet ID"),
    user_address: str = Depends(verify_token)  # 👈 secure it
):
    if user_address["address"].lower() != wallet_id.lower():
        raise HTTPException(status_code=403, detail="Unauthorized access")

    data = get_data()
    if wallet_id in data:
        return data[wallet_id]
    else:
        raise HTTPException(status_code=404, detail="Wallet ID not found")
    
def save_data(data):
    with open("contracts.json", "w") as f:
        json.dump(data, f)


@app.post("/contracts/create")
async def create_contract(
    group: Group,
    user_address: str = Depends(verify_token)  
):
    if user_address["address"].lower() != group.wallet_id.lower():
        raise HTTPException(status_code=403, detail="Unauthorized access")
    
    data = get_data()

    for existing_group in data[group.wallet_id]:
        if existing_group['name'] == group.name:
            raise HTTPException(status_code=400, detail="Group name already exists")
        
    data[group.wallet_id].append(group.model_dump(exclude={"wallet_id"}))

    save_data(data)

    return JSONResponse(status_code=201, content={'message':'contract created successfully'})

@app.post("/contracts/add-expense")
async def add_expense(tx: Transaction):
    try:
        # Prepare the transaction
        txn = contract.functions.addExpense(
            tx.name,
            tx.description,
            Web3.to_checksum_address(tx.wallet_id),
            tx.payer,
            Web3.to_wei(tx.total_amount, 'ether'),
            tx.members,
            tx.members_amount
        ).build_transaction({
            'from': BACKEND_ADDRESS,
            'nonce': web3.eth.get_transaction_count(BACKEND_ADDRESS),
            'gas': 500000,
            'gasPrice': web3.to_wei('10', 'gwei')
        })

        # Sign the transaction
        signed_txn = web3.eth.account.sign_transaction(txn, private_key=PRIVATE_KEY)

        # Send the transaction
        # tx_hash = web3.eth.send_raw_transaction(signed_txn.rawTransaction)
        tx_hash = web3.eth.send_raw_transaction(signed_txn.raw_transaction)

        return {"tx_hash": web3.to_hex(tx_hash)}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    

def get_all_expenses(group_name: str):
    expenses = []
    index = 0

    while True:
        try:
            result = contract.functions.getFormattedExpense(group_name, index).call()
            expenses.append({
                "group": result[0],
                "description": result[1],
                "paid_by": result[2],
                "paid_by_name": result[3],
                "total_amount": Web3.from_wei(result[4], 'ether'),
                "members": result[5],  # It's like "Alice:1, Bob:2"
                "timestamp": result[6]
            })
            index += 1
        except Exception:
            break  # No more expenses

    return expenses

@app.get("/contracts/query/{group_name}")
def fetch_all_expenses(
    group_name: str
):
    # You can enhance this with wallet check if needed
    expenses = get_all_expenses(group_name)
    return {"group": group_name, "expenses": expenses}

# @app.post("/contracts/chat/{group_name}")
# async def chatbot_query(
#     group_name: str,
#     user_input: str
# ):
#     expenses = fetch_all_expenses(group_name)
#     # formatted_expenses = json.dumps(expenses)

#     result = get_ai_response(user_input, expenses)
#     return {"result": result}

@app.post("/contracts/chat/{group_name}")
async def chatbot_query(
    group_name: str,
    req: ChatRequest
):
    expenses = fetch_all_expenses(group_name)
    result = get_ai_response(req.user_input, expenses)
    return {"result": result}

@app.get("/")
async def root():
    return {"message": "Welcome to the SettleXChain API!"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")