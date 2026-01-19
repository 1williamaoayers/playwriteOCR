#!/usr/bin/env python3
"""
华尔街见闻资讯爬虫 - DOM解析版 v2
用法：python wallstreet_scraper.py "关键词"
"""

import sys
import re
import time
import os
import urllib.parse
from datetime import datetime
from playwright.sync_api import sync_playwright


def scrape(keyword: str) -> list:
    """爬取华尔街见闻（直接从DOM属性提取时间）"""
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
            url = f'https://wallstreetcn.com/search?q={encoded_keyword}&type=live'
            print(f"📄 打开: {url}")
            page.goto(url, wait_until='domcontentloaded', timeout=60000)
            
            print("⏳ 等待页面加载...")
            time.sleep(5)
            
            print("📰 加载更多内容...")
            
            # 多次点击"加载更多"获取更多内容
            for i in range(5):  # 点击5次
                try:
                    # 滚动到底部
                    page.evaluate('window.scrollTo(0, document.body.scrollHeight)')
                    time.sleep(1)
                    
                    # 点击"加载更多"按钮
                    load_more = page.locator('text=加载更多')
                    if load_more.count() > 0:
                        load_more.click(timeout=3000)
                        time.sleep(2)
                        print(f"  📥 第{i+1}次加载...")
                    else:
                        break
                except:
                    break
            
            # 最终截图
            page.screenshot(path='screenshots/wallstreet_page.png')
            print("📷 截图: wallstreet_page.png")
            
            print("📰 提取新闻...")
            
            # 直接选择 live-item 元素
            items = page.locator('div.live-item').all()
            print(f"  找到 {len(items)} 条快讯")
            
            for item in items:
                try:
                    # 从 time 元素的 datetime 属性直接获取精确时间
                    # 格式：2026-01-16T18:58:31.000+08:00
                    time_elem = item.locator('time.live-item_created')
                    if time_elem.count() == 0:
                        continue
                    
                    datetime_attr = time_elem.get_attribute('datetime')
                    if not datetime_attr:
                        continue
                    
                    # 解析ISO时间
                    # 去掉时区和毫秒
                    dt_str = datetime_attr[:19]  # 2026-01-16T18:58:31
                    time_obj = datetime.strptime(dt_str, '%Y-%m-%dT%H:%M:%S')
                    
                    # 提取标题（【】内的内容）
                    title = ""
                    title_elem = item.locator('div.live-item_title')
                    if title_elem.count() > 0:
                        title = title_elem.inner_text().strip()
                    
                    # 提取正文内容
                    content = ""
                    content_elem = item.locator('div.live-item_html')
                    if content_elem.count() > 0:
                        content = content_elem.inner_text().strip()
                    
                    # 合并标题和正文
                    full_text = title
                    if content:
                        full_text = title + "\n" + content if title else content
                    
                    if len(full_text) < 10:
                        continue
                    
                    news.append({
                        'title': title,
                        'content': content,
                        'full_text': full_text[:500],  # 限制长度
                        'time': time_obj,
                    })
                except Exception as e:
                    continue
            
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
    
    # JSON 模式
    if json_mode:
        import json as json_lib
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
                    'summary': n.get('content', ''),  # 保留完整内容
                    'time': n['time'].strftime('%Y-%m-%d %H:%M') if hasattr(n['time'], 'strftime') else str(n['time']),
                    'url': ''
                })
        output.sort(key=lambda x: x['time'], reverse=True)
        print(json_lib.dumps(output, ensure_ascii=False))
        return
    
    # 普通模式
    print("=" * 60)
    print(f"🎯 华尔街见闻爬虫 | 关键词: {keyword}")
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
    # 输出全部（不再限制20条）
    results = unique
    
    print(f"\n{'=' * 60}")
    print(f"📊 原始: {len(all_news)} | 去重: {len(unique)} | 输出: {len(results)}")
    print("=" * 60)
    
    if results:
        print(f"\n📰 {keyword} 华尔街见闻:\n")
        for i, n in enumerate(results, 1):
            t = n['time'].strftime('%m-%d %H:%M')
            title = n['title'][:65] + '...' if len(n['title']) > 65 else n['title']
            print(f"[{i}] [{t}] {title}")
        
        # 保存 MD
        md = f"{keyword}_华尔街见闻_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
        with open(md, 'w', encoding='utf-8') as f:
            f.write(f"# {keyword} 华尔街见闻\n\n")
            f.write(f"> 采集时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"> 来源: 华尔街见闻快讯\n")
            f.write(f"> 共 {len(results)} 条\n\n---\n\n")
            for i, n in enumerate(results, 1):
                t = n['time'].strftime('%Y-%m-%d %H:%M')
                f.write(f"## {i}. {n['title']}\n\n")
                f.write(f"**时间**: {t}\n\n")
                if n.get('content'):
                    f.write(f"{n['content']}\n\n")
                f.write(f"---\n\n")
        
        print(f"\n💾 已保存: {md}")
    else:
        print("\n⚠️ 未提取到新闻")
    
    print(f"⏱️ 耗时: {elapsed:.1f}s")


if __name__ == "__main__":
    main()

