"""
app.py
------
Flask web application for the CodeAlpha FAQ Chatbot (Task 2: Chatbot for FAQs).

Run:
    python app.py
Then open http://127.0.0.1:5000 in your browser.

API:
    POST /api/chat   { "message": "How do I reset my password?" }
    ->  { "answer": "...", "matched": true, "matched_question": "...",
          "category": "...", "confidence": 0.79 }

    GET  /api/categories   -> list of FAQ categories, for reference/debugging
    GET  /api/health       -> simple health check
"""

from flask import Flask, jsonify, render_template, request

from chatbot.matcher import FAQMatcher

app = Flask(__name__)
bot = FAQMatcher()


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/chat", methods=["POST"])
def chat():
    payload = request.get_json(silent=True) or {}
    user_message = payload.get("message", "")

    result = bot.get_response(user_message)

    return jsonify({
        "answer": result.answer,
        "matched": result.matched,
        "matched_question": result.question,
        "category": result.category,
        "confidence": round(result.score, 3),
    })


@app.route("/api/categories", methods=["GET"])
def categories():
    return jsonify({"categories": bot.list_categories()})


@app.route("/api/health", methods=["GET"])
def health():
    return jsonify({"status": "ok", "faq_count": len(bot.faqs)})


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
