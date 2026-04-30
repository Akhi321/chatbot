from flask import Flask, jsonify, render_template, request
from chatbot import NCM_Bot

app = Flask(__name__)

# Initialize the bot once at startup
print("[INFO] Starting NCM Web Application...")
ncm_bot = NCM_Bot()

@app.route("/")
def home():
    """Render the main chat interface."""
    return render_template("index.html")

@app.route("/api/chat", methods=["POST"])
def chat():
    """Handle incoming chat messages from the frontend."""
    data = request.get_json(silent=True)
    if not data or "message" not in data:
        return jsonify({"response": "Please enter a message."}), 400

    user_message = data["message"]
    try:
        bot_response = ncm_bot.process_query(user_message)
        if isinstance(bot_response, dict):
            return jsonify(
                {
                    "response": str(bot_response.get("response", "")),
                    "charts": bot_response.get("charts", []),
                }
            )
        return jsonify({"response": str(bot_response), "charts": []})
    except Exception as e:
        print(f"[ERROR] Processing message: {e}")
        return jsonify({"response": "Something went wrong while processing your message."}), 500

if __name__ == "__main__":
    app.run(debug=True, port=5000)
