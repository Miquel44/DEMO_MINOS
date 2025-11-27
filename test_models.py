# test_models.py
import google.generativeai as genai
import os
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv("GOOGLE_API_KEY")

if not api_key:
    print("❌ Error: No se encontró la API KEY en el archivo .env")
else:
    genai.configure(api_key=api_key)
    print(f"✅ API Key cargada correctamente. Consultando modelos...\n")
    
    try:
        for m in genai.list_models():
            if 'generateContent' in m.supported_generation_methods:
                print(f"- {m.name}")
    except Exception as e:
        print(f"❌ Error conectando con Google: {e}")