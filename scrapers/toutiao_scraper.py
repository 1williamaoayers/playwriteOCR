#!/usr/bin/env python3
"""
今日头条资讯爬虫 - DOM解析版 v6
改用直接解析HTML结构，不使用OCR
"""

import sys
import re
import json
import time
import os
import urllib.parse
from datetime import datetime, timedelta
from playwright.sync_api import sync_playwright


def parse_time(text: str) -> datetime:
    now = datetime.now()
    
    if '分钟前' in text:
        m = re.search(r'(\d+)分钟前', text)
        if m: return now - timedelta(minutes=int(m.group(1)))
    if '小时前' in text:
        m = re.search(r'(\d+)小时前', text)
        if m: return now - timedelta(hours=int(m.group(1)))
    if '天前' in text:
        m = re.search(r'(\d+)天前', text)
        if m: return now - timedelta(days=int(m.group(1)))
    if '昨天' in text: return now - timedelta(days=1)
    if '前天' in text: return now - timedelta(days=2)
    
    m = re.search(r'(\d{4})年(\d{1,2})月(\d{1,2})日', text)
    if m: return datetime(int(m.group(1)), int(m.group(2)), int(m.group(3)))
    
    m = re.search(r'(\d{1,2})月(\d{1,2})日', text)
    if m:
        month, day = int(m.group(1)), int(m.group(2))
        year = now.year
        if month > now.month or (month == now.month and day > now.day):
            year = now.year - 1
        return datetime(year, month, day)
    
    return datetime(2000, 1, 1)


def extract_news_from_dom(page) -> list:
    """从 DOM 结构直接提取新闻"""
    news = []
    
    # 尝试多种可能的新闻卡片选择器
    card_selectors = [
        'div.result-content',          # 搜索结果卡片
        'div[class*="result"]',
        'div[class*="feed-card"]',
        'div[class*="card"]',
        'article',
    ]
    
    for selector in card_selectors:
        try:
            cards = page.locator(selector).all()
            if len(cards) > 2:
                print(f"    使用选择器: {selector} (找到 {len(cards)} 个)")
                
                for card in cards:
                    try:
                        # 提取标题（通常是 a 标签或 h 标签）
                        title = ""
                        title_selectors = ['a', 'h1', 'h2', 'h3', '[class*="title"]']
                        for ts in title_selectors:
                            try:
                                title_elem = card.locator(ts).first
                                if title_elem.count() > 0:
                                    t = title_elem.inner_text().strip()
                                    if len(t) > 20:  # 标题至少20字
                                        title = t
                                        break
                            except:
                                continue
                        
                        if not title or len(title) < 15:
                            continue
                        
                        # 提取链接
                        url = ""
                        try:
                            link = card.locator('a').first
                            if link.count() > 0:
                                url = link.get_attribute('href') or ""
                                if url and not url.startswith('http'):
                                    if url.startswith('//'):
                                        url = 'https:' + url
                                    else:
                                        url = 'https://www.toutiao.com' + url
                        except:
                            pass
                        
                        # 提取来源
                        source = ""
                        try:
                            source_elem = card.locator('[class*="source"], [class*="author"], [class*="name"]').first
                            if source_elem.count() > 0:
                                source = source_elem.inner_text().strip()[:50]
                        except:
                            pass
                        
                        # 提取时间
                        time_text = ""
                        time_obj = datetime(2000, 1, 1)
                        try:
                            # 整个卡片的文本中搜索时间
                            card_text = card.inner_text()
                            time_patterns = [
                                r'\d+分钟前', r'\d+小时前', r'\d+天前',
                                r'昨天', r'前天',
                                r'\d{4}年\d{1,2}月\d{1,2}日',
                                r'\d{1,2}月\d{1,2}日'
                            ]
                            for pattern in time_patterns:
                                match = re.search(pattern, card_text)
                                if match:
                                    time_text = match.group()
                                    time_obj = parse_time(time_text)
                                    break
                        except:
                            pass
                        
                        news.append({
                            'title': title,
                            'url': url,
                            'source': source,
                            'time': time_obj,
                            'time_text': time_text,
                        })
                    except Exception as e:
                        continue
                
                if len(news) > 0:
                    break  # 找到了就不再尝试其他选择器
        except:
            continue
    
    return news


def scrape(keyword: str, pages: int = 5) -> list:
    all_news = []
    os.makedirs('screenshots', exist_ok=True)
    
    with sync_playwright() as p:
        print("🚀 启动浏览器...")
        browser = p.chromium.launch(headless=True, args=['--no-sandbox'])
        
        context = browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0',
        )
        page = context.new_page()
        page.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        
        try:
            # 直接使用 URL 编码访问
            encoded_keyword = urllib.parse.quote(keyword)
            url = f'https://so.toutiao.com/search?dvpf=pc&source=pagination&keyword={encoded_keyword}'
            print(f"📄 打开: {url}")
            page.goto(url, wait_until='domcontentloaded', timeout=60000)
            
            print("⏳ 等待页面加载...")
            time.sleep(6)
            
            print("📰 点击资讯...")
            try:
                page.click('text=资讯', timeout=5000)
                time.sleep(3)
                print("✅ 已点击资讯")
            except:
                print("⚠️ 资讯标签点击失败")
            
            for page_num in range(1, pages + 1):
                print(f"\n📖 第 {page_num} 页...")
                time.sleep(2)
                
                # 截图（用于调试）
                try:
                    page.screenshot(path=f'screenshots/dom_page_{page_num}.png')
                    print(f"  📷 截图: dom_page_{page_num}.png")
                except:
                    pass
                
                # DOM 解析提取新闻
                page_news = extract_news_from_dom(page)
                print(f"  📰 提取: {len(page_news)} 条")
                all_news.extend(page_news)
                
                # 保存提取结果（调试用）
                with open(f'screenshots/dom_page_{page_num}.json', 'w', encoding='utf-8') as f:
                    json.dump([{'title': n['title'], 'source': n['source'], 'time': n['time_text']} 
                               for n in page_news], f, ensure_ascii=False, indent=2)
                
                if page_num < pages:
                    print(f"  ➡️ 翻页...")
                    try:
                        page.evaluate('window.scrollTo(0, document.body.scrollHeight)')
                        time.sleep(1)
                        page.click(f'a:text-is("{page_num + 1}")', timeout=5000)
                        time.sleep(3)
                    except:
                        try:
                            page.click('text=下一页', timeout=3000)
                            time.sleep(3)
                        except:
                            print("  ⚠️ 翻页失败")
                            break
            
        except Exception as e:
            print(f"❌ 错误: {e}")
        finally:
            browser.close()
            print("\n🔒 浏览器关闭")
    
    return all_news


def main():
    # 解析参数: keyword [limit] [--json]
    keyword = "小米集团"
    json_mode = False
    
    args = [arg for arg in sys.argv[1:] if arg != '--json']
    json_mode = '--json' in sys.argv
    
    if len(args) >= 1:
        keyword = args[0]
    
    # JSON 模式
    if json_mode:
        import io, sys as sys_module
        old_stdout = sys_module.stdout
        sys_module.stdout = io.StringIO()
        all_news = scrape(keyword)
        sys_module.stdout = old_stdout
        # 转换为 JSON 可序列化格式
        output = []
        seen = set()
        for n in all_news:
            key = n['title'][:40]
            if key not in seen:
                seen.add(key)
                output.append({
                    'title': n['title'],
                    'time': n['time'].strftime('%Y-%m-%d %H:%M') if hasattr(n['time'], 'strftime') and n['time'].year > 2000 else '',
                    'url': n.get('url', '')
                })
        output.sort(key=lambda x: x['time'], reverse=True)
        print(json.dumps(output[:20], ensure_ascii=False))
        return
    
    # 普通模式
    print("=" * 60)
    print(f"🎯 今日头条爬虫 v6 (DOM解析) | 关键词: {keyword}")
    print("=" * 60)
    
    start = time.time()
    all_news = scrape(keyword)
    elapsed = time.time() - start
    
    # 去重
    seen = set()
    unique = []
    for n in all_news:
        key = n['title'][:40]
        if key not in seen:
            seen.add(key)
            unique.append(n)
    
    # 按时间排序
    unique.sort(key=lambda x: x['time'], reverse=True)
    top20 = unique[:20]
    
    print(f"\n{'=' * 60}")
    print(f"📊 原始: {len(all_news)} | 去重: {len(unique)} | 输出: {len(top20)}")
    print("=" * 60)
    
    print(f"\n📰 {keyword} 最新资讯:\n")
    for i, n in enumerate(top20, 1):
        t = n['time'].strftime('%m-%d') if n['time'].year > 2000 else '未知'
        title = n['title'][:65] + '...' if len(n['title']) > 65 else n['title']
        print(f"[{i}] [{t}] {title}")
    
    # 保存 MD
    md = f"{keyword}_资讯_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
    with open(md, 'w', encoding='utf-8') as f:
        f.write(f"# {keyword} 最新资讯\n\n")
        f.write(f"> 采集时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"> 来源: 今日头条（DOM解析，前5页）\n")
        f.write(f"> 共 {len(top20)} 条\n\n---\n\n")
        for i, n in enumerate(top20, 1):
            t = n['time'].strftime('%Y-%m-%d') if n['time'].year > 2000 else '未知'
            f.write(f"## {i}. {n['title']}\n\n")
            f.write(f"- **时间**: {t}\n")
            if n.get('source'):
                f.write(f"- **来源**: {n['source']}\n")
            if n.get('url'):
                f.write(f"- **链接**: [{n['url'][:50]}...]({n['url']})\n")
            f.write(f"\n---\n\n")
    
    print(f"\n💾 已保存: {md}")
    print(f"⏱️ 耗时: {elapsed:.1f}s")


if __name__ == "__main__":
    main()

