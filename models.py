from pydantic import BaseModel, Field
from typing import Annotated, List

class Group(BaseModel):
    wallet_id: Annotated[str, Field(..., description="Wallet ID")]
    name: Annotated[str, Field(..., description="Group Name")]
    members: Annotated[List[str], Field(..., description="Members")]

class Transaction(BaseModel):
    name: Annotated[str, Field(..., description="Group Name")]
    description: Annotated[str, Field(..., description="Transaction Description")]
    wallet_id: Annotated[str, Field(..., description="Wallet ID")]
    payer: Annotated[str, Field(..., description="Player Name")]
    total_amount: Annotated[float, Field(..., description="Total Amount")]
    members: Annotated[List[str], Field(..., description="Members Names")]
    members_amount: Annotated[List[int], Field(..., description="Members Amounts")]
    timestamp: Annotated[str, Field(..., description="Transaction Timestamp")]

class ChatRequest(BaseModel):
    user_input: str