#!/usr/bin/env python3
"""
财联社资讯爬虫 - 简化版
用法：python cls_scraper.py "关键词"
只采集当前页，不翻页
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
    """解析时间"""
    now = datetime.now()
    
    # "2025-12-31 16:17"
    m = re.search(r'(\d{4})-(\d{2})-(\d{2})\s+(\d{2}):(\d{2})', text)
    if m:
        return datetime(int(m.group(1)), int(m.group(2)), int(m.group(3)),
                        int(m.group(4)), int(m.group(5)))
    
    # "01-16 17:40"
    m = re.search(r'(\d{2})-(\d{2})\s+(\d{2}):(\d{2})', text)
    if m:
        month, day = int(m.group(1)), int(m.group(2))
        year = now.year
        if month > now.month:
            year -= 1
        return datetime(year, month, day, int(m.group(3)), int(m.group(4)))
    
    return datetime(2000, 1, 1)


def scrape(keyword: str) -> list:
    """爬取财联社（只采集当前页）"""
    news = []
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
            url = f'https://www.cls.cn/searchPage?keyword={encoded_keyword}&type=telegram'
            print(f"📄 打开: {url}")
            page.goto(url, wait_until='domcontentloaded', timeout=60000)
            
            print("⏳ 等待页面加载...")
            time.sleep(6)
            
            # 截图
            page.screenshot(path='screenshots/cls_page.png')
            print("📷 截图: cls_page.png")
            
            # 保存HTML用于调试
            html = page.content()
            with open('screenshots/cls_page.html', 'w', encoding='utf-8') as f:
                f.write(html)
            print("📄 HTML: cls_page.html")
            
            # 直接获取页面所有文本，按行解析
            print("📰 提取新闻...")
            
            # 方法1：尝试常见选择器
            selectors_to_try = [
                'div.search-telegram-wrap div',
                'div.search-telegram-item',
                'div.telegraph-item',
                'div[class*="telegraph"]',
                'div[class*="telegram"]',
                'div[class*="search"] div',
                'div.content-wrap div',
                'div.list-item',
                'article',
            ]
            
            for selector in selectors_to_try:
                try:
                    items = page.locator(selector).all()
                    if len(items) > 2:
                        print(f"  尝试选择器: {selector} → {len(items)} 个元素")
                        
                        for item in items:
                            try:
                                text = item.inner_text().strip()
                                if len(text) < 30:
                                    continue
                                
                                # 跳过UI元素
                                if any(skip in text for skip in ['热门话题', 'A股公告', '环球市场', '+关注']):
                                    continue
                                
                                # 解析时间
                                time_obj = parse_time(text)
                                if time_obj.year == 2000:
                                    continue  # 没有时间的跳过
                                
                                # 清理标题
                                title = text
                                # 移除日期时间前缀
                                title = re.sub(r'^\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}\s*[星期一二三四五六日]*\s*', '', title)
                                title = title.strip()
                                
                                if len(title) < 20:
                                    continue
                                
                                news.append({
                                    'title': title[:300],
                                    'time': time_obj,
                                })
                            except:
                                continue
                        
                        if len(news) > 0:
                            print(f"  ✅ 使用选择器: {selector}")
                            break
                except:
                    continue
            
            # 方法2：如果上面没提取到，尝试获取整个页面文本解析
            if len(news) == 0:
                print("  尝试页面文本解析...")
                body_text = page.inner_text('body')
                lines = [l.strip() for l in body_text.split('\n') if l.strip()]
                
                for line in lines:
                    if len(line) < 30 or len(line) > 500:
                        continue
                    
                    time_obj = parse_time(line)
                    if time_obj.year == 2000:
                        continue
                    
                    # 跳过UI
                    if any(skip in line for skip in ['热门话题', 'A股公告', '环球市场', '+关注', '加载更多']):
                        continue
                    
                    # 检查是否包含财联社特征
                    if '财联社' in line or '电' in line:
                        title = re.sub(r'^\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}\s*[星期一二三四五六日]*\s*', '', line)
                        if len(title) > 20:
                            news.append({
                                'title': title[:300],
                                'time': time_obj,
                            })
            
            print(f"📊 共提取: {len(news)} 条")
            
        except Exception as e:
            print(f"❌ 错误: {e}")
        finally:
            browser.close()
            print("🔒 浏览器关闭")
    
    return news


def main():
    # 解析参数: keyword [limit] [--json]
    keyword = "小米集团"
    json_mode = False
    
    args = [arg for arg in sys.argv[1:] if arg != '--json']
    json_mode = '--json' in sys.argv
    
    if len(args) >= 1:
        keyword = args[0]
    # args[1] 是 limit，财联社爬虫不用它
    
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
                    'time': n['time'].strftime('%Y-%m-%d %H:%M') if hasattr(n['time'], 'strftime') else str(n['time']),
                    'url': ''
                })
        output.sort(key=lambda x: x['time'], reverse=True)
        print(json.dumps(output[:20], ensure_ascii=False))
        return
    
    # 普通模式
    print("=" * 60)
    print(f"🎯 财联社爬虫 | 关键词: {keyword}")
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
    
    if top20:
        print(f"\n📰 {keyword} 财联社资讯:\n")
        for i, n in enumerate(top20, 1):
            t = n['time'].strftime('%m-%d %H:%M')
            title = n['title'][:65] + '...' if len(n['title']) > 65 else n['title']
            print(f"[{i}] [{t}] {title}")
        
        # 保存 MD
        md = f"{keyword}_财联社_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
        with open(md, 'w', encoding='utf-8') as f:
            f.write(f"# {keyword} 财联社资讯\n\n")
            f.write(f"> 采集时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"> 来源: 财联社\n")
            f.write(f"> 共 {len(top20)} 条\n\n---\n\n")
            for i, n in enumerate(top20, 1):
                t = n['time'].strftime('%Y-%m-%d %H:%M')
                f.write(f"## {i}. {n['title']}\n\n")
                f.write(f"- **时间**: {t}\n\n---\n\n")
        
        print(f"\n💾 已保存: {md}")
    else:
        print("\n⚠️ 未提取到新闻，请检查 screenshots/cls_page.html")
    
    print(f"⏱️ 耗时: {elapsed:.1f}s")


if __name__ == "__main__":
    main()

