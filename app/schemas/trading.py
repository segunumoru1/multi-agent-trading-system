from pydantic import BaseModel

class TradingRequest(BaseModel):
    ticker: str
    trade_date: str

class TradingResponse(BaseModel):
    decision: str
    details: dict