from fastapi import FastAPI, Request
import httpx
import os

app = FastAPI()

VOICEFLOW_API_KEY = os.getenv("VOICEFLOW_API_KEY", "VF.DM.68524c8f58f5533ca5e85556.zwf1WTaSAUBWpdVF")
VOICEFLOW_VERSION_ID = os.getenv("VOICEFLOW_VERSION_ID", "68523cb9f4ab61398423b823")
DOUBLETICK_SEND_URL = "https://public.doubletick.io/whatsapp/message/text"
DOUBLETICK_API_KEY = os.getenv("DOUBLETICK_API_KEY", "key_UuopCTSZhE")

@app.get("/")
async def root():
    return {"message": "DoubleTick to Voiceflow Webhook Service", "status": "running"}

@app.post("/webhook")
async def doubletick_webhook(request: Request):
    try:
        data = await request.json()
        print(f"Received webhook data: {data}")
        
        user_phone = data.get("from")
        message_data = data.get("message", {})
        message_type = message_data.get("type")
        user_message = message_data.get("text")
        
        print(f"User phone: {user_phone}, Message type: {message_type}, Message: {user_message}")
        
        if not user_phone:
            print("Missing phone data")
            return {"status": "error", "message": "Missing phone data"}
        
        # Handle different message types
        if message_type in ["IMAGE", "AUDIO", "VIDEO", "DOCUMENT"]:
            # Handle non-text messages locally without Voiceflow
            polite_reply = "Thank you for reaching out! Could you please describe your requirement or question in text? I'm here to help you with any information you need."
            
            async with httpx.AsyncClient() as client:
                doubletick_payload = {
                    "to": user_phone,
                    "type": "text",
                    "content": {
                        "text": polite_reply
                    }
                }
                
                print(f"Sending direct reply to DoubleTick: {doubletick_payload}")
                
                dt_response = await client.post(
                    DOUBLETICK_SEND_URL,
                    headers={
                        "Authorization": DOUBLETICK_API_KEY,
                        "Content-Type": "application/json"
                    },
                    json=doubletick_payload
                )
                
                print(f"DoubleTick response status: {dt_response.status_code}")
                print(f"DoubleTick response: {dt_response.text}")
                
            return {"status": "ok"}
        
        elif not user_message:
            print("No text message found")
            return {"status": "error", "message": "No processable message content"}

        # Send user's message to Voiceflow (only for text messages)
        async with httpx.AsyncClient() as client:
            print(f"Sending to Voiceflow: {user_message}")
            try:
                vf_response = await client.post(
                    f"https://general-runtime.voiceflow.com/state/user/{user_phone}/interact",
                    headers={
                        "Authorization": VOICEFLOW_API_KEY,
                        "Content-Type": "application/json",
                        "versionID": "68523cb9f4ab61398423b823"
                    },
                    json={
                        "request": {
                            "type": "text",
                            "payload": user_message
                        }
                    },
                    timeout=30.0
                )
                
                print(f"Voiceflow response status: {vf_response.status_code}")
                
                if vf_response.status_code != 200:
                    print(f"Voiceflow error: {vf_response.text}")
                    return {"status": "error", "message": "Voiceflow API error"}
                
                vf_data = vf_response.json()
                print(f"Voiceflow response: {vf_data}")
                
            except httpx.TimeoutException:
                print("Voiceflow API timeout")
                return {"status": "error", "message": "Voiceflow API timeout"}
            except httpx.RequestError as e:
                print(f"Voiceflow API request error: {e}")
                return {"status": "error", "message": f"Voiceflow API request error: {e}"}
            except Exception as e:
                print(f"Voiceflow API unexpected error: {e}")
                return {"status": "error", "message": f"Voiceflow API unexpected error: {e}"}
            
            ai_reply = ""
            for item in vf_data:
                if isinstance(item, dict) and item.get("type") == "text":
                    ai_reply += item["payload"]["message"] + " "
                elif isinstance(item, str):
                    ai_reply += item + " "

            if not ai_reply.strip():
                ai_reply = "Sorry, I didn't understand that. Could you please try again?"
            
            print(f"AI Reply: {ai_reply}")

            # Send the reply back to DoubleTick
            doubletick_payload = {
                "to": user_phone,
                "type": "text",
                "content": {
                    "text": ai_reply.strip()
                }
            }
            
            print(f"Sending to DoubleTick: {doubletick_payload}")
            
            dt_response = await client.post(
                DOUBLETICK_SEND_URL,
                headers={
                    "Authorization": DOUBLETICK_API_KEY,
                    "Content-Type": "application/json"
                },
                json=doubletick_payload
            )
            
            print(f"DoubleTick response status: {dt_response.status_code}")
            print(f"DoubleTick response: {dt_response.text}")
            
        return {"status": "ok"}
        
    except Exception as e:
        print(f"Error in webhook: {str(e)}")
        return {"status": "error", "message": str(e)}
