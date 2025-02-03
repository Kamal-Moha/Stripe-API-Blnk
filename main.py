import os, json
import stripe

from typing import Union

# from fastapi import FastAPI
from fastapi import FastAPI, responses, Request, HTTPException
from pydantic import BaseModel

import uvicorn

import requests

base_url = "http://34.23.238.239:5001"  # blnk GCP instance URL
url = f'{base_url}/transactions'
headers = {'content-type': 'application/json', "X-Blnk-Key": os.environ['x_blnk_key']}

def recordTransaction(url, data):
    try:
        response = requests.post(url, json=data, headers=headers)
        print(f"Response Data: {response.json()}")
    except Exception as e:
        return e

app = FastAPI(
    title='RTA Mobility API',
    description='RTA by Bhadala',
)

# Bhadala Stripe API Key
stripe.api_key = os.environ['stripe_api_key']

@app.get("/")
def read_root():
    return {"message": "Stripe API is running..."}

@app.get("/checkout/")
async def create_checkout_session(price: int):
    checkout_session = stripe.checkout.Session.create(
        line_items=[
            {
                "price_data": {
                    "currency": "usd",
                    "product_data": {
                        "name": "RTA Wallet Topup",
                    },
                    "unit_amount": price * 100,
                },
                "quantity": 1,
            }
        ],
        metadata={
            "user_id": 3,
            "email": "abc@gmail.com",
            "request_id": 1234567890
        },
        mode="payment",
        success_url= "https://bhadala.com/",
        # cancel_url=os.getenv("BASE_URL") + "/cancel/",
        customer_email="test@email.com",
    )
    # return responses.RedirectResponse(checkout_session.url, status_code=303)
    return checkout_session.url

@app.post("/webhook/")
async def stripe_webhook(request: Request):
    payload = await request.body()
    event = None

    try:
        event = stripe.Event.construct_from(json.loads(payload), stripe.api_key)
    except ValueError as e:
        print("Invalid payload")
        raise HTTPException(status_code=400, detail="Invalid payload")
    except stripe.error.SignatureVerificationError as e:
        print("Invalid signature")
        raise HTTPException(status_code=400, detail="Invalid signature")

    print("event received is", event)
    if event["type"] == "checkout.session.completed":
        payment = event["data"]["object"]
        amount = payment["amount_total"]
        currency = payment["currency"]
        user_id = payment["metadata"]["user_id"] # get custom user id from metadata
        user_email = payment["customer_details"]["email"]
        user_name = payment["customer_details"]["name"]
        order_id = payment["id"]
        print(f"{amount} was successfully deposited into the wallet")

        # Topup user wallet in Blnk

        # Wallet TopUp
        topup_wallet_trans = {
            "amount": amount,
            "precision": 1,
            "reference": "Topup Wallet_2",
            "description": "Wallet Topup",
            "currency": "USD",
            "source": "@Stripe",
            "allow_overdraft": True,
            "inflight": False,
            "destination":"bln_24e223a9-24dd-46ae-a225-15a667e1b912",  # destination wallet
            "meta_data": {
                "type": "wallet_topup"
            }
        }

        recordTransaction(url, topup_wallet_trans)


        # save to db
        # send confirmation email in background task
    return {}



if __name__ == "__main__":
  # Run the uvicorn server
  uvicorn.run(app, port=8000)
