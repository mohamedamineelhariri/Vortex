import requests
import json
import yaml

def load_url():
    try:
        with open("config.yaml", "r") as f:
            config = yaml.safe_load(f)
            return config.get("n8n_webhook_url")
    except Exception as e:
        print(f"Error loading config: {e}")
        return None

def test_webhook():
    url = load_url()
    if not url:
        print("No URL found in config.yaml")
        return

    print(f"Testing Webhook URL: {url}")
    
    payload = {
        "filename": "debug_test_file.txt",
        "extension": ".txt",
        "created_at": "2023-01-01",
        "text_excerpt": "This is a debug request to check JSON response."
    }

    try:
        response = requests.post(url, json=payload, timeout=10)
        print(f"\nResponse Status Code: {response.status_code}")
        print("-" * 30)
        print("Raw Response Body:")
        print("-" * 30)
        print(response.text)
        print("-" * 30)
        
        try:
            data = response.json()
            print("\n✅ Valid JSON received:")
            print(json.dumps(data, indent=2))
        except json.decoder.JSONDecodeError:
            print("\n❌ ERROR: Response is NOT valid JSON.")
            
    except Exception as e:
        print(f"\n❌ Request failed: {e}")

if __name__ == "__main__":
    test_webhook()
