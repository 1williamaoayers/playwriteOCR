#!/usr/bin/env python3
"""
东方财富爬虫
URL: https://so.eastmoney.com/news/s?keyword=关键词&type=content
直接打开就是 资讯>正文，翻页点底栏页码
"""

import sys
import time
from datetime import datetime
from playwright.sync_api import sync_playwright

def scrape_eastmoney(keyword: str, target_count: int = 20):
    results = []
    seen = set()
    
    with sync_playwright() as p:
        print("🚀 启动浏览器...")
        browser = p.chromium.launch(headless=True, args=['--no-sandbox'])
        page = browser.new_page(viewport={'width': 1920, 'height': 1080})
        
        try:
            # 直接访问，不需要点Tab
            url = f"https://so.eastmoney.com/news/s?keyword={keyword}&type=content"
            print(f"🌍 访问: {url}")
            page.goto(url, wait_until='domcontentloaded', timeout=60000)
            time.sleep(3)
            
            page_num = 1
            while len(results) < target_count:
                print(f"📖 第 {page_num} 页...")
                
                # 采集 .news_item
                items = page.evaluate("""() => {
                    var results = [];
                    document.querySelectorAll('.news_item').forEach(function(item) {
                        var text = item.innerText || '';
                        var lines = text.split('\\n');
                        var title = lines[0].trim();
                        
                        // 摘要（第二行通常是时间+摘要）
                        var summary = '';
                        if (lines.length > 1) {
                            // 跳过时间，取摘要内容
                            var content = lines.slice(1).join(' ').trim();
                            // 去掉时间和链接
                            content = content.replace(/\\d{4}-\\d{2}-\\d{2}\\s+\\d{2}:\\d{2}:\\d{2}\\s*-?/g, '');
                            content = content.replace(/http[^\\s]+/g, '');
                            summary = content.trim().substring(0, 200);
                        }
                        
                        // 时间
                        var time = '';
                        var m = text.match(/(\\d{4}-\\d{2}-\\d{2}\\s+\\d{2}:\\d{2}:\\d{2})/);
                        if (m) time = m[1];
                        
                        // 链接
                        var urlEl = item.querySelector('.news_item_url');
                        var url = urlEl ? urlEl.innerText.trim() : '';
                        
                        if (title.length > 5) results.push({
                            title: title, 
                            summary: summary,
                            time: time, 
                            url: url
                        });
                    });
                    return results;
                }""")
                
                for item in items:
                    if item['title'][:30] not in seen:
                        seen.add(item['title'][:30])
                        results.append(item)
                
                print(f"   本页: {len(items)} 条, 总计: {len(results)} 条")
                
                if len(results) >= target_count:
                    break
                
                # 点击下一页页码
                page_num += 1
                try:
                    page.click(f'a:text-is("{page_num}")', timeout=3000)
                    time.sleep(2)
                except:
                    print("   翻页结束")
                    break
            
        except Exception as e:
            print(f"❌ 错误: {e}")
        finally:
            browser.close()
    
    # 保持页面顺序（默认按相关性排序）
    return results[:target_count]

def main():
    if len(sys.argv) < 2:
        print("用法: python eastmoney_scraper.py <关键词> [数量] [--json]")
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
        # 抑制 scrape 函数内的 print 输出
        old_stdout = sys_module.stdout
        sys_module.stdout = io.StringIO()
        data = scrape_eastmoney(keyword, limit)
        sys_module.stdout = old_stdout
        print(json_lib.dumps(data, ensure_ascii=False))
        return
    
    # 普通模式：输出进度和保存文件
    print(f"{'='*50}")
    print(f"📈 东方财富爬虫 | {keyword} | 目标: {limit}")
    print(f"{'='*50}")
    
    start = time.time()
    data = scrape_eastmoney(keyword, limit)
    elapsed = time.time() - start
    
    if data:
        filename = f"{keyword}_东方财富_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(f"# {keyword} 东方财富资讯\n\n")
            f.write(f"> 采集时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"> 数量: {len(data)}\n")
            f.write(f"> 耗时: {elapsed:.1f}秒\n\n---\n\n")
            for i, item in enumerate(data, 1):
                f.write(f"## {i}. {item['title']}\n\n")
                if item.get('time'): f.write(f"- **时间**: {item['time']}\n")
                if item.get('summary'): f.write(f"- **摘要**: {item['summary']}\n")
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

