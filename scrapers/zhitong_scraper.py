#!/usr/bin/env python3
"""
智通财经爬虫
1. 访问首页
2. 输入关键词，点搜索
3. 处理新窗口（带token）
4. 点"快讯"tab，滚动采集
"""

import sys
import time
from datetime import datetime
from playwright.sync_api import sync_playwright

def scrape_zhitong(keyword: str, target_count: int = 20):
    results = []
    seen = set()
    
    with sync_playwright() as p:
        print("🚀 启动浏览器...")
        browser = p.chromium.launch(headless=True, args=['--no-sandbox'])
        context = browser.new_context(viewport={'width': 1920, 'height': 1080})
        page = context.new_page()
        
        try:
            # 1. 访问首页
            print("🌍 访问首页...")
            page.goto('https://www.zhitongcaijing.com/', wait_until='domcontentloaded', timeout=60000)
            time.sleep(3)
            
            # 2. 输入关键词
            print(f"🔍 搜索: {keyword}")
            search_input = page.locator('input.search-input-head').first
            search_input.fill(keyword)
            time.sleep(1)
            
            # 3. 监听新窗口，点击搜索
            with context.expect_page() as new_page_info:
                page.click('text=搜索', force=True)
            
            new_page = new_page_info.value
            print(f"📄 新窗口: {new_page.url[:80]}...")
            time.sleep(3)
            
            # 4. 点击"快讯"tab
            print("👉 点击 '快讯' Tab...")
            new_page.click('text=快讯', force=True, timeout=10000)
            time.sleep(2)
            
            print(f"📊 采集快讯 (目标: {target_count})...")
            
            # 5. 滚动采集
            for scroll_round in range(10):
                items = new_page.evaluate("""() => {
                    var results = [];
                    
                    // 查找快讯条目
                    document.querySelectorAll('a, div, p').forEach(function(el) {
                        var text = el.innerText || '';
                        
                        // 匹配时间格式 2026-01-16 17:40:02
                        var timeMatch = text.match(/(\\d{4}-\\d{2}-\\d{2}\\s+\\d{2}:\\d{2}:\\d{2})/);
                        if (timeMatch && text.length > 30 && text.length < 800) {
                            var lines = text.split('\\n');
                            var title = '';
                            
                            // 找标题（【开头或较长的行）
                            for (var i = 0; i < lines.length; i++) {
                                var line = lines[i].trim();
                                if (line.length > 15 && line.indexOf('2026') < 0) {
                                    title = line;
                                    break;
                                }
                            }
                            
                            if (title) {
                                results.push({
                                    title: title.substring(0, 200),
                                    time: timeMatch[1],
                                    url: el.href || ''
                                });
                            }
                        }
                    });
                    
                    return results;
                }""")
                
                for item in items:
                    uid = item['title'][:30]
                    if uid not in seen:
                        seen.add(uid)
                        results.append(item)
                
                print(f"📊 [第{scroll_round+1}轮] 采集: {len(results)} 条")
                
                if len(results) >= target_count:
                    break
                
                # 滚动加载更多
                new_page.mouse.wheel(0, 800)
                time.sleep(2)
            
        except Exception as e:
            print(f"❌ 错误: {e}")
        finally:
            browser.close()
    
    # 按时间排序
    results.sort(key=lambda x: x.get('time', ''), reverse=True)
    return results[:target_count]

def main():
    if len(sys.argv) < 2:
        print("用法: python zhitong_scraper.py <关键词> [数量] [--json]")
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
    
    # JSON 模式
    if json_mode:
        import json as json_lib
        import io, sys as sys_module
        old_stdout = sys_module.stdout
        sys_module.stdout = io.StringIO()
        data = scrape_zhitong(keyword, limit)
        sys_module.stdout = old_stdout
        print(json_lib.dumps(data, ensure_ascii=False))
        return
    
    # 普通模式
    print(f"{'='*50}")
    print(f"📰 智通财经爬虫 | {keyword} | 目标: {limit}")
    print(f"{'='*50}")
    
    start = time.time()
    data = scrape_zhitong(keyword, limit)
    elapsed = time.time() - start
    
    if data:
        filename = f"{keyword}_智通财经_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(f"# {keyword} 智通财经快讯\n\n")
            f.write(f"> 采集时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"> 数量: {len(data)}\n")
            f.write(f"> 耗时: {elapsed:.1f}秒\n\n---\n\n")
            for i, item in enumerate(data, 1):
                f.write(f"## {i}. {item['title']}\n\n")
                if item.get('time'): f.write(f"- **时间**: {item['time']}\n")
                if item.get('url'): f.write(f"- **链接**: {item['url']}\n")
                f.write("\n")
        
        print(f"\n{'='*50}")
        print(f"✅ 完成: {len(data)}条 | {elapsed:.1f}秒")
        print(f"📄 保存: {filename}")
        print(f"{'='*50}")
    else:
        print(f"\n⚠️ 无数据")

if __name__ == "__main__":
    main()

