import os
from dotenv import load_dotenv
from google import genai

load_dotenv()
client=genai.Client(
    api_key=os.getenv('GEMINI_API_KEY')  
)

def ask_gemini(prompt:str):
    response=client.models.generate_content(
        model="gemini-3.6-flash",
        contents=prompt
    )
    return response.text

def ask_gemini_with_history(messages):
    contents=[]
    for message in messages:
        contents.append({
            "role":message.role,
            "parts":[
                {
                    "text":message.content
                }
            ]
        })
    try:
        response=client.models.generate_content(
        model="gemini-3.6-flash",
        contents=contents
        )

        return response.text
    except Exception as e:
        print(f"Gemini error:{e}")
        raise RuntimeError("Gemini Service is temporarily unavailable")

    



