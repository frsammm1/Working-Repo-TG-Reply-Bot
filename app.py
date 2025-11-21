from flask import Flask
import logging

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@app.route('/')
def home():
    logger.info("🏠 Home endpoint accessed")
    return "✅ Bot Running!", 200

@app.route('/health')
def health():
    logger.info("💊 Health check")
    return "OK", 200

@app.route('/ping')
def ping():
    logger.info("🏓 Ping received")
    return "PONG", 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
