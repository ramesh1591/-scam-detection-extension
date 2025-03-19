from flask import Flask, request, jsonify
from transformers import AutoTokenizer, AutoModelForSequenceClassification, pipeline
from playwright.sync_api import sync_playwright
import logging
import traceback

# Initialize Flask app
app = Flask(__name__)

# Force UTF-8 encoding for JSON responses
@app.after_request
def apply_utf8(response):
    response.headers["Content-Type"] = "application/json; charset=utf-8"
    return response

# Fine-tuned model configuration
FINE_TUNED_MODEL_PATH = "./finetuned_model"

# Configure logging
logging.basicConfig(level=logging.INFO)

# Load fine-tuned model and tokenizer
try:
    tokenizer = AutoTokenizer.from_pretrained(FINE_TUNED_MODEL_PATH)
    model = AutoModelForSequenceClassification.from_pretrained(FINE_TUNED_MODEL_PATH)
    logging.info(f"✅ Fine-tuned model loaded successfully from {FINE_TUNED_MODEL_PATH}.")
except Exception as e:
    logging.error(f"❌ Failed to load fine-tuned model from {FINE_TUNED_MODEL_PATH}: {str(e)}")
    raise e

# Initialize pipeline for detection using the fine-tuned model
scam_detector = pipeline("text-classification", model=model, tokenizer=tokenizer)

# List of suspicious words commonly found in scams
SUSPICIOUS_KEYWORDS = [
        "win", "lottery", "prize", "jackpot", "poker", "casino", "betting", "real money",
    "double your money", "no risk", "lucky winner", "investment", "bitcoin", "crypto",
    "forex", "binary options", "pyramid scheme", "get rich quick", "quick money",
    "instant cash", "guaranteed returns", "no risk investment", "earn from home",
    "financial freedom", "wire transfer", "bank alert", "cash out", "limited-time offer",
    "free", "congratulations", "click here", "claim now", "exclusive", "redeem now",
    "special offer", "limited time", "hot girls", "watch live", "sex cam", "free porn",
    "your account", "verify your identity", "reset password", "urgent security alert",
    "login issue", "account locked", "unauthorized access", "your details required",
    "click to verify", "your computer is infected", "update your software",
    "contact support", "call now", "fix now", "microsoft support", "fix your device",
    "system alert", "security warning", "instant loan", "no credit check loan",
    "personal loan approval", "low interest loan", "debt relief", "government grants",
    "free insurance", "cheap insurance", "free robux", "game hack", "cheat code",
    "mod apk", "unlimited coins", "limited edition reward", "too good to be true",
    "don't miss out", "one-time offer", "act fast", "last chance", "hurry up",
    "money back guarantee", "best deal ever", "easy approval", "win big now","Dating"
]

@app.route('/api/detect', methods=['POST'])
def detect_scam():
    """
    API endpoint to classify a webpage as a scam or legitimate.
    """
    try:
        if not request.is_json:
            return jsonify({"error": "Content-Type must be application/json"}), 400

        data = request.get_json()
        url = data.get("url")

        if not url:
            return jsonify({"error": "Missing 'url' parameter"}), 400

        # Validate the URL
        if not url.startswith(("http://", "https://")):
            return jsonify({"error": "Invalid URL format. URL must start with 'http://' or 'https://'"}), 400

        # Check if the domain is trusted
        trusted_domains = [".edu", ".gov", ".ac.in"]
        is_trusted = any(url.endswith(domain) for domain in trusted_domains)

        # Scrape webpage content using Playwright
        webpage_content = scrape_webpage_content(url)
        if not webpage_content:
            return jsonify({"error": "Failed to retrieve webpage content."}), 400

        # Count occurrences of suspicious words
        content_lower = webpage_content.lower()
        suspicious_count = sum(1 for word in SUSPICIOUS_KEYWORDS if word in content_lower)

        # Auto-mark trusted domains as legitimate if no suspicious words found
        if is_trusted and suspicious_count == 0:
            return jsonify({
                "url": url,
                "result": "Legitimate",
                "confidence": 1.0,
                "message": "✅ Trusted domain detected. No scam indicators found."
            })

        # Reduce scam weight for trusted domains to lower false positives
        scam_weight = 2.0  # Default weight
        if is_trusted:
            scam_weight = 0.5  # Reduce scam influence on trusted domains

        # Process text for scam detection
        max_length = 512  # Max tokens for BERT
        stride = 256  # Overlap chunks to retain scam phrases
        tokens = tokenizer(webpage_content, truncation=False)["input_ids"]
        chunks = [tokens[i:i + max_length] for i in range(0, len(tokens), stride)]
        results = []

        for chunk in chunks:
            chunk_text = tokenizer.decode(chunk, skip_special_tokens=True)

            # Predict using the pipeline
            try:
                result = scam_detector(chunk_text)[0]
                results.append(result)
            except Exception as e:
                logging.error(f"❌ Error processing chunk: {e}")

        # Aggregate results
        scam_count = sum(1 for r in results if r["label"] == "LABEL_1")
        legitimate_count = sum(1 for r in results if r["label"] == "LABEL_0")
        confidence = sum(r["score"] for r in results) / len(results) if results else 0

        # Adjust scam detection threshold
        detection_threshold = 2  # Increase threshold from 1 to 2 to reduce false positives
        label = "Scam" if scam_count * scam_weight + suspicious_count > detection_threshold else "Legitimate"

        # Log cases where a trusted domain is classified as a scam
        if is_trusted and label == "Scam":
            logging.warning(f"⚠️ False Positive? Trusted site {url} marked as Scam. Suspicious words found: {suspicious_count}")

        # Use emoji in response for better readability
        emoji = "🚨" if label == "Scam" else "✅"

        return jsonify({
            "url": url,
            "result": label,
            "confidence": round(confidence, 4),
            "suspicious_word_count": suspicious_count,
            "message": f"{emoji} The webpage is detected as {label} based on its content."
        })

    except Exception as e:
        logging.error("❌ Error in /api/detect: %s", traceback.format_exc())
        return jsonify({"error": f"❌ An unexpected error occurred: {str(e)}"}), 500

def scrape_webpage_content(url):
    """
    Uses Playwright to extract webpage content, including JavaScript-rendered text.
    """
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)  # Run in headless mode
            page = browser.new_page()
            page.goto(url, timeout=30000)  # Increased timeout to 30 sec
            
            # Extract only visible text (removes hidden/malicious scripts)
            text = page.inner_text("body")
            
            browser.close()
        
        return text[:100000]  # Increased to 100,000 characters
    except Exception as e:
        logging.error(f"❌ Error fetching webpage content: {str(e)}")
        return None

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
