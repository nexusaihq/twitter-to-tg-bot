import os
import requests
import time

# ===== CONFIGURATION (loaded from Render Environment Variables) =====
TWITTER_USERNAME = os.getenv('TWITTER_USERNAME')
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
TELEGRAM_CHANNEL = os.getenv('TELEGRAM_CHANNEL')
BEARER_TOKEN = os.getenv('TWITTER_BEARER_TOKEN')
CHECK_INTERVAL = 180  # 3 minutes between checks

# ===== API SETUP =====
HEADERS = {"Authorization": f"Bearer {BEARER_TOKEN}"}
TWITTER_API_URL = f"https://api.twitter.com/2/users/by/username/{TWITTER_USERNAME}/tweets"

# ===== TELEGRAM SENDER FUNCTION =====
def send_to_telegram(text):
    """Sends a formatted message to the specified Telegram channel."""
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHANNEL,
        "text": text,
        "parse_mode": "HTML",
        "disable_web_page_preview": True
    }
    try:
        response = requests.post(url, json=payload)
        response.raise_for_status()  # Raise an exception for bad status codes
        print(f"Successfully sent message to {TELEGRAM_CHANNEL}")
    except requests.exceptions.RequestException as e:
        print(f"Error sending to Telegram: {e}")

# ===== MAIN BOT LOGIC =====
def main():
    """Main loop to check for new tweets and forward them."""
    print("Bot started. Initial check for last tweet...")
    last_tweet_id = None

    # Initial run to get the very last tweet ID without posting
    try:
        initial_params = {"max_results": 5}
        response = requests.get(TWITTER_API_URL, headers=HEADERS, params=initial_params)
        response.raise_for_status()
        initial_tweets = response.json().get('data', [])
        if initial_tweets:
            last_tweet_id = initial_tweets[0]['id']
            print(f"Starting point found. Last tweet ID: {last_tweet_id}")
    except requests.exceptions.RequestException as e:
        print(f"Could not perform initial fetch: {e}. Retrying.")
        time.sleep(60) # Wait a minute before starting the main loop if initial fetch fails

    while True:
        try:
            params = {"max_results": 5, "tweet.fields": "created_at"}
            if last_tweet_id:
                params["since_id"] = last_tweet_id

            response = requests.get(TWITTER_API_URL, headers=HEADERS, params=params)
            response.raise_for_status()
            tweets = response.json().get('data', [])

            if tweets:
                print(f"Found {len(tweets)} new tweet(s).")
                # The API returns newest first. We reverse to post oldest first.
                for tweet in reversed(tweets):
                    tweet_id = tweet['id']
                    tweet_text = tweet['text']
                    tweet_url = f"https://twitter.com/{TWITTER_USERNAME}/status/{tweet_id}"

                    message = (
                        f"<b>New Tweet from @{TWITTER_USERNAME}</b>\n\n"
                        f"{tweet_text}\n\n"
                        f"<a href='{tweet_url}'>View on X</a>"
                    )

                    send_to_telegram(message)

                # Update the last tweet ID to the newest one from this batch
                last_tweet_id = tweets[0]['id']
            else:
                print("No new tweets found. Waiting...")

        except Exception as e:
            print(f"An error occurred: {e}")

        time.sleep(CHECK_INTERVAL)

if __name__ == "__main__":
    main()
