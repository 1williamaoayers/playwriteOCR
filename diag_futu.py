from playwright.sync_api import sync_playwright
import time
import os

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True, args=['--no-sandbox'])
    # browser = p.chromium.launch(headless=False) # Debug mode
    page = browser.new_page(viewport={'width': 1920, 'height': 1080})
    
    print('📄 访问富途...')
    page.goto('https://news.futunn.com/', wait_until='domcontentloaded')
    time.sleep(5)
    
    # Search
    print('⌨️ 搜索...')
    page.locator('.web_search-input-container').first.click(force=True)
    time.sleep(1)
    page.locator('input.web_search-input').type('小米集团', delay=50)
    time.sleep(3)
    
    # Click News Tab
    print('📰 点击资讯标签...')
    page.evaluate('''
        const tabs = document.querySelectorAll('.web_search-tab-li');
        for (const tab of tabs) {
            if (tab.innerText.includes('资讯')) {
                tab.click();
                break;
            }
        }
    ''')
    time.sleep(2)
    
    # Click News Sub-tab
    print('📰 点击新闻子标签...')
    page.evaluate('''
        const elements = Array.from(document.querySelectorAll('div, span, li, a'));
        for (const el of elements) {
            if (el.innerText.trim() === '新闻' && 
                (el.className.includes('tab') || el.className.includes('item') || el.className.includes('title'))) {
                el.click();
                break;
            }
        }
    ''')
    time.sleep(2)
    
    # Scroll a bit
    print('📜 滚动...')
    page.mouse.wheel(0, 1000)
    time.sleep(2)
    
    # Inspect Load More
    print('🔍 检查加载更多按钮...')
    # Try multiple selectors
    selectors = [
        'text=加载更多',
        'button:has-text("Load More")',
        '.web_search-load-more',
        '.load-more'
    ]
    
    found = False
    for sel in selectors:
        lm = page.locator(sel)
        if lm.count() > 0:
            print(f"Selector '{sel}' found {lm.count()} elements")
            visible_count = 0
            for i in range(lm.count()):
                el = lm.nth(i)
                if el.is_visible():
                    print(f"  Element {i} is visible")
                    try:
                        print(f"  HTML: {el.evaluate('el => el.outerHTML')}")
                    except:
                        pass
                    
                    print("  Attempting click...")
                    try:
                        el.click(force=True, timeout=2000)
                        print("  Click success")
                        found = True
                    except Exception as e:
                        print(f"  Click failed: {e}")
            if found:
                break
    
    if not found:
        print("❌ 未找到可见的加载更多按钮")
    
    time.sleep(5)
    
    # Check count
    count = page.locator('.web_search-news-item-title').count()
    print(f"📊 当前新闻标题数量: {count}")
    
    # Save debug info
    page.screenshot(path='futu_debug_diag.png')
    with open('futu_debug_diag.html', 'w', encoding='utf-8') as f:
        f.write(page.content())
        
    browser.close()
