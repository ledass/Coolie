from flask import Flask, jsonify

app = Flask(__name__)

@app.route("/")
def index():
    return "Bot is running ✅"

@app.route("/health")
def health():
    return jsonify({"status": "ok", "message": "Bot is alive!"}), 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
  
