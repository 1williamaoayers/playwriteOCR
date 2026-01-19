#!/usr/bin/env python3
"""
格隆汇爬虫
URL: https://www.gelonghui.com/search?keyword=关键词&type=news
按页面顺序采集（已按时间倒序排列）
"""

import sys
import time
from datetime import datetime
from playwright.sync_api import sync_playwright

def scrape_gelonghui(keyword: str, target_count: int = 20):
    """采集格隆汇新闻 - 按页面顺序（最新在前）"""
    results = []
    
    with sync_playwright() as p:
        print("🚀 启动浏览器...")
        browser = p.chromium.launch(headless=True, args=['--no-sandbox'])
        page = browser.new_page(
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0'
        )
        
        try:
            # 访问搜索页
            url = f"https://www.gelonghui.com/search?keyword={keyword}&type=news"
            print(f"🌍 访问: {url}")
            page.goto(url, wait_until='domcontentloaded', timeout=60000)
            time.sleep(5)
            
            seen = set()
            
            # 按页面顺序采集
            print(f"📊 采集新闻 (目标: {target_count})...")
            
            for scroll_round in range(10):
                items = page.evaluate("""(targetCount) => {
                    var results = [];
                    
                    // 按DOM顺序获取新闻链接
                    var links = document.querySelectorAll('a[href*="/news/"]');
                    
                    links.forEach(function(a) {
                        var text = a.innerText || '';
                        if (text.length > 20 && text.length < 500) {
                            var lines = text.split('\\n');
                            var title = lines[0].trim();
                            
                            // 提取时间
                            var time = '';
                            var match = text.match(/格隆汇(\\d{1,2}月\\d{1,2}日)/);
                            if (match) {
                                time = match[1];
                            } else {
                                match = text.match(/(\\d{1,2}-\\d{1,2}\\s+\\d{1,2}:\\d{1,2})/);
                                if (match) time = match[1];
                            }
                            
                            if (title.length > 5) {
                                results.push({
                                    title: title.substring(0, 150),
                                    time: time,
                                    url: a.href
                                });
                            }
                        }
                    });
                    
                    return results;
                }""", target_count)
                
                for item in items:
                    uid = item['title'][:30]
                    if uid not in seen:
                        seen.add(uid)
                        results.append(item)
                
                print(f"📊 [第{scroll_round+1}轮] 采集: {len(results)} 条")
                
                if len(results) >= target_count:
                    break
                
                # 滚动加载更多
                page.keyboard.press("End")
                page.mouse.wheel(0, 1000)
                time.sleep(2)
            
        except Exception as e:
            print(f"❌ 错误: {e}")
        finally:
            browser.close()
    
    # 返回前N条（保持页面顺序）
    return results[:target_count]

def main():
    if len(sys.argv) < 2:
        print("用法: python gelonghui_scraper.py <关键词> [数量] [--json]")
        print("示例: python gelonghui_scraper.py 小米集团 20")
        sys.exit(1)
    
    # 解析参数
    keyword = sys.argv[1]
    limit = 20
    json_mode = False
    
    for arg in sys.argv[2:]:
        if arg == '--json':
            json_mode = True
        elif arg.isdigit():
            limit = int(arg)
    
    # JSON 模式：静默运行，只输出 JSON
    if json_mode:
        import json as json_lib
        import io, sys as sys_module
        # 抑制 print 输出
        old_stdout = sys_module.stdout
        sys_module.stdout = io.StringIO()
        data = scrape_gelonghui(keyword, limit)
        sys_module.stdout = old_stdout
        print(json_lib.dumps(data, ensure_ascii=False))
        return
    
    # 普通模式
    print(f"{'='*50}")
    print(f"📰 格隆汇爬虫 | {keyword} | 目标: {limit}")
    print(f"{'='*50}")
    
    start = time.time()
    data = scrape_gelonghui(keyword, limit)
    elapsed = time.time() - start
    
    if data:
        filename = f"{keyword}_格隆汇_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(f"# {keyword} 格隆汇资讯\n\n")
            f.write(f"> 采集时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"> 数量: {len(data)}\n")
            f.write(f"> 耗时: {elapsed:.1f}秒\n")
            f.write(f"> 排序: 按时间倒序（最新在前）\n\n---\n\n")
            
            for i, item in enumerate(data, 1):
                f.write(f"## {i}. {item['title']}\n\n")
                if item.get('time'):
                    f.write(f"- **时间**: {item['time']}\n")
                if item.get('url'):
                    f.write(f"- **链接**: {item['url']}\n")
                f.write("\n")
        
        print(f"\n{'='*50}")
        print(f"✅ 完成: {len(data)}条 | {elapsed:.1f}秒")
        print(f"📄 保存: {filename}")
        print(f"{'='*50}")
    else:
        print(f"\n⚠️ 无数据 | {elapsed:.1f}秒")

if __name__ == "__main__":
    main()

