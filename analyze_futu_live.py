import json
import time
from playwright.sync_api import sync_playwright

def analyze_live():
    url = "https://news.futunn.com/main/live"
    print(f"🚀 Analyzing: {url}")
    
    captured_data = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, args=['--no-sandbox'])
        context = browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0'
        )
        page = context.new_page()
        
        # Capture network XHR/Fetch for analysis
        def handle_response(response):
            try:
                # Target the specific API we saw in the logs
                if 'get-flash-list' in response.url and response.status == 200:
                    try:
                        data = response.json()
                        captured_data.append({
                            'url': response.url,
                            'data': data
                        })
                        print(f"✅ CAPTURED TARGET DATA: {response.url}")
                        # Immediately save to avoid data loss on timeout
                        with open("futu_live_flash_data.json", "w", encoding="utf-8") as f:
                            json.dump(captured_data, f, ensure_ascii=False, indent=2)
                    except:
                        pass
            except:
                pass
        
        page.on('response', handle_response)
        
        try:
            print("🌍 Navigating (waiting for domcontentloaded)...")
            # Relaxed timeout and wait condition
            page.goto(url, wait_until='domcontentloaded', timeout=30000)
            
            print("⏳ Waiting for additional data loading...")
            time.sleep(5) # Wait for listeners to fire
            
            # Simple text dump
            visible_text = page.locator('body').inner_text()
            print(f"📄 Page Text Sample: {visible_text[:200]}...")
            
        except Exception as e:
            print(f"⚠️ Navigation warning: {e}")
        finally:
            browser.close()
            print(f"🏁 Finished. Captured {len(captured_data)} datasets.")

if __name__ == "__main__":
    analyze_live()
