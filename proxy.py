from flask import Flask, request, jsonify
import requests
import time
from dotenv import load_dotenv
import os

app = Flask(__name__)

# Load environment variables from .env file
load_dotenv()

API_KEY = os.getenv("API_KEY")
DEPLOYMENT_ID = "89206e89-0900-471c-bceb-4ce98d534c7d"
WATSON_URL = f"https://us-south.ml.cloud.ibm.com/ml/v4/deployments/{DEPLOYMENT_ID}/ai_service?version=2021-05-01"

# Token caching (initialize from .env)
TOKEN = os.getenv("ACCESS_TOKEN")
try:
    TOKEN_EXPIRY = float(os.getenv("TOKEN_EXPIRY", "0"))
except ValueError:
    TOKEN_EXPIRY = 0

def get_token():
    global TOKEN, TOKEN_EXPIRY
    if TOKEN and time.time() < TOKEN_EXPIRY - 60:
        return TOKEN  # Token is still valid

    response = requests.post(
        "https://iam.cloud.ibm.com/identity/token",
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        data={
            "apikey": API_KEY,
            "grant_type": "urn:ibm:params:oauth:grant-type:apikey"
        }
    )

    if response.status_code != 200:
        raise Exception("Failed to get IBM Cloud access token", response.text)

    data = response.json()
    TOKEN = data["access_token"]
    TOKEN_EXPIRY = time.time() + data["expires_in"]
    return TOKEN

@app.route("/ask", methods=["POST"])
def ask():
    try:
        token = get_token()
    except Exception as e:
        return jsonify({"error": str(e)}), 500

    payload = request.get_json()
    if not payload or "messages" not in payload:
        return jsonify({
            "error": "Payload must include a 'messages' array with at least one message having role/content."
        }), 400

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    response = requests.post(WATSON_URL, headers=headers, json=payload)

    try:
        return jsonify(response.json()), response.status_code
    except Exception:
        return response.text, response.status_code

if __name__ == "__main__":
    app.run(port=8000)
