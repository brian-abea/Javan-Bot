from fastapi import FastAPI, Request, HTTPException
import httpx
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

app = FastAPI()

# --- Configuration from .env ---
RASA_CORE_WEBHOOK_ENDPOINT = os.getenv("RASA_CORE_WEBHOOK_ENDPOINT", "http://localhost:5005/webhooks/rest/webhook")
INFOBIP_API_KEY = os.getenv("INFOBIP_API_KEY")
WHATSAPP_SENDER = os.getenv("WHATSAPP_SENDER")
INFOBIP_SEND_API = os.getenv("INFOBIP_SEND_API")

# Verify essential environment variables
if not all([RASA_CORE_WEBHOOK_ENDPOINT, INFOBIP_API_KEY, WHATSAPP_SENDER, INFOBIP_SEND_API]):
    raise ValueError("Missing one or more required environment variables (RASA_CORE_WEBHOOK_ENDPOINT, INFOBIP_API_KEY, WHATSAPP_SENDER, INFOBIP_SEND_API)")


@app.post("/infobip-webhook")
async def infobip_to_rasa(request: Request):
    """
    This receives inbound messages from Infobip, forwards them to Rasa,
    and then sends Rasa's responses back to Infobip.
    """
    try:
        payload = await request.json()
        print(f"Received raw Infobip payload: {payload}")

        messages = []
        if "results" in payload: 
            messages = payload["results"]

        elif "whatsappInboundMessage" in payload: # Dedicated WhatsApp webhook (newer format)
            # The block is for a different payload structure, handles other scenarios
            inbound_msg = payload["whatsappInboundMessage"]
            messages.append({
                "from": inbound_msg.get("from"),
                "text": {"body": inbound_msg.get("text", {}).get("body", "")},
                "messageId": inbound_msg.get("id"),
                "to": inbound_msg.get("to")
            })
        else:
            print(f"Warning: Unexpected Infobip payload structure: {payload}")
            return {"status": "unsupported_payload_format"}

        # Initialize HTTPX client for async requests
        async with httpx.AsyncClient() as client:
            for msg in messages:
                sender_whatsapp_number = msg.get("sender") 
                user_message_text = ""
                if "content" in msg and isinstance(msg["content"], list) and msg["content"]:
                    if "text" in msg["content"][0]:
                        user_message_text = msg["content"][0]["text"]

                if not user_message_text:
                    print(f"Warning: No text body found in message from {sender_whatsapp_number}. Skipping Rasa forwarding.")
                    continue # Skips to next message if no text found

                print(f"Received message from {sender_whatsapp_number}: {user_message_text}")

                #   Forward to Rasa
                rasa_payload = {
                    "sender": sender_whatsapp_number.lstrip('+') if sender_whatsapp_number else "unknown_sender",
                    "message": user_message_text
                }
                print(f"Sending to Rasa: {rasa_payload} to {RASA_CORE_WEBHOOK_ENDPOINT}")
                try:
                    rasa_response = await client.post(RASA_CORE_WEBHOOK_ENDPOINT, json=rasa_payload, timeout=30.0)
                    rasa_response.raise_for_status() # Raise an exception for HTTP errors
                    bot_replies = rasa_response.json()
                    print(f"Received from Rasa: {bot_replies}")

                    # Send Rasa's responses back to Infobip
                    for reply in bot_replies:
                        if "text" in reply:
                            infobip_outbound_payload = {
                                "from": WHATSAPP_SENDER,
                                "to": sender_whatsapp_number, # Send back to the original sender
                                "content": {
                                    "text": reply["text"]
                                }
                            }
                            # Include API Key in headers for Infobip outbound API
                            headers = {
                                "Authorization": f"App {INFOBIP_API_KEY}",
                                "Content-Type": "application/json",
                                "Accept": "application/json"
                            }
                            print(f"Sending to Infobip: {infobip_outbound_payload} to {INFOBIP_SEND_API}")
                            infobip_send_response = await client.post(
                                INFOBIP_SEND_API,
                                json=infobip_outbound_payload,
                                headers=headers,
                                timeout=30.0
                            )
                            infobip_send_response.raise_for_status()
                            print(f"Infobip Send Response: {infobip_send_response.json()}")
                        # Handle other types of Rasa responses (e.g., images, buttons) if needed
                except httpx.RequestError as e:
                    print(f"Error communicating with Rasa: {e}")
                    # To handle a fallback message to the user via Infobip here
                    # e.g., "Sorry, I'm having trouble connecting right now."
                except httpx.HTTPStatusError as e:
                    print(f"Error response from Rasa: {e.response.status_code} - {e.response.text}")
                    # To handle specific Rasa errors
                except Exception as e:
                    print(f"Unexpected error processing Rasa response: {e}")

    except Exception as e:
        print(f"Error processing Infobip webhook payload: {e}")
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {e}")

    return {"status": "processed_and_replied"}