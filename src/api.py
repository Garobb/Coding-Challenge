from fastapi import FastAPI, Query, encoders, HTTPException
from .model import RecurringOrder, User
from typing import Literal
from decimal import Decimal
from pydantic import BaseModel, ValidationError

import traceback

app = FastAPI(
    title="Investifi Backend Coding Challenge",
)

class RecurringOrderPublic(BaseModel):
    asset_type: str
    frequency: str
    amount: Decimal
    user_id: str

@app.get("/recurring-orders")
def get_recurring_orders(user_id: str = Query(...)):
    """
    TODO
    # Requirements:
    # The GET route should accept a User ID and return only said users recurring orders
    # if no ID is provided, an error should be raised.
    """
    if not user_id:
        raise HTTPException(status_code=400, detail="user_id is required")

    try:
        db_orders = RecurringOrder.query(user_id)
        orders = [RecurringOrderPublic(
            asset_type=order.range_key.split(":")[1],
            frequency=order.range_key.split(":")[0],
            amount=order.currency_amount,
            user_id=order.hash_key,
        ) for order in db_orders]
        return {"message": ([encoders.jsonable_encoder(o) for o in orders])}
    except Exception as ex:
        raise HTTPException(status_code=400, detail=str(ex))


@app.post("/recurring-orders")
def post_recurring_orders(order: RecurringOrderPublic):
    """
    TODO
    Requirements:
    The POST route should create a recurring order for a user
    A recurring order can be for only BTC or ETH
    A recurring order must have a concept of Frequency. Only Daily or Bi-Monthly frequencies is allowed
    A User can only have 1 recurring order for a given Crypto/Frequency i.e. BTC/Daily
    A recurring order must have a USD amount greater than 0
    A recurring order needs to be associated with a specifc user.
    """
    db_users = User.query(order.user_id)
    users = [user for user in db_users]
    if len(users) < 1:
        raise HTTPException(status_code=400, detail="User does not exist")

    try:
        range_key = f'{order.frequency}:{order.asset_type}'
        RecurringOrder(
            hash_key=order.user_id,
            range_key=range_key,
            currency="USD",
            currency_amount=order.amount,
        ).save()
        return {"message": "Recurring order created successfully"}
    except Exception as ex:
        raise HTTPException(status_code=400, detail=str(ex))
