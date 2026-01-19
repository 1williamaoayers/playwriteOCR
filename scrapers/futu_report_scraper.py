#!/usr/bin/env python3
"""
富途牛牛研报爬虫
采集路径: 搜索 -> 资讯 -> 研报
使用 dispatchEvent 点击避免弹窗关闭
"""

import sys
import time
from datetime import datetime
from playwright.sync_api import sync_playwright

def scrape_futu_report(keyword: str, target_count: int = 50):
    """采集富途研报 - 资讯>研报子栏"""
    results = {}
    
    with sync_playwright() as p:
        print("🚀 启动浏览器...")
        browser = p.chromium.launch(headless=True, args=['--no-sandbox'])
        context = browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0'
        )
        page = context.new_page()
        
        # API拦截器
        def on_response(response):
            try:
                if response.status == 200:
                    url = response.url
                    if 'search' in url or 'report' in url or 'research' in url:
                        try:
                            data = response.json()
                            parse_api(data, results, keyword)
                        except:
                            pass
            except:
                pass

        page.on('response', on_response)
        
        try:
            # 1. 访问首页
            print("🌍 访问: https://news.futunn.com/main/live")
            page.goto('https://news.futunn.com/main/live', wait_until='domcontentloaded', timeout=60000)
            time.sleep(3)
            
            # 2. 输入搜索词
            print(f"🔍 搜索: {keyword}")
            search = page.locator('input.web_search-input').first
            search.click(force=True)
            time.sleep(0.3)
            search.fill(keyword)
            time.sleep(3)
            
            # 3. 使用dispatchEvent点击资讯Tab (关键！)
            print("👉 点击 '资讯' Tab...")
            page.evaluate("""() => {
                var tabs = document.querySelectorAll('.web_search-tab-li');
                for (var i = 0; i < tabs.length; i++) {
                    if (tabs[i].innerText && tabs[i].innerText.indexOf('资讯') >= 0) {
                        var event = new MouseEvent('click', {
                            view: window, bubbles: true, cancelable: true
                        });
                        tabs[i].dispatchEvent(event);
                        return;
                    }
                }
            }""")
            time.sleep(2)
            
            # 4. 使用dispatchEvent点击研报子Tab (关键！选择器是 web_search-sec-tab-li)
            print("👉 点击 '研报' 子Tab...")
            page.evaluate("""() => {
                var tabs = document.querySelectorAll('.web_search-sec-tab-li');
                for (var i = 0; i < tabs.length; i++) {
                    if (tabs[i].innerText && tabs[i].innerText.trim() === '研报') {
                        var event = new MouseEvent('click', {
                            view: window, bubbles: true, cancelable: true
                        });
                        tabs[i].dispatchEvent(event);
                        return;
                    }
                }
            }""")
            time.sleep(2)
            
            # 检查弹窗状态
            popup = page.evaluate("""() => {
                var panel = document.querySelector('.web_search-res-panel');
                return panel ? panel.offsetHeight > 0 : false;
            }""")
            
            if popup:
                print(f"✅ 弹窗打开，开始滚动采集 (目标: {target_count})...")
                no_new = 0
                
                for i in range(100):
                    prev = len(results)
                    
                    # 采集DOM
                    parse_dom(page, results, keyword)
                    
                    curr = len(results)
                    print(f"📊 [第{i+1}轮] 总数: {curr} (+{curr-prev})")
                    
                    if curr >= target_count:
                        print(f"✅ 达到目标")
                        break
                    
                    if curr == prev:
                        no_new += 1
                    else:
                        no_new = 0
                    
                    if no_new >= 10:
                        print("🛑 无更多数据")
                        break
                    
                    # 滚动弹窗内容
                    page.evaluate("""() => {
                        var panel = document.querySelector('.web_search-res-panel');
                        if (panel) panel.scrollTop += 500;
                    }""")
                    time.sleep(1)
            else:
                print("⚠️ 弹窗已关闭")
                
        except KeyboardInterrupt:
            print("\n🛑 用户中断")
        except Exception as e:
            print(f"❌ 错误: {e}")
        finally:
            browser.close()
            
    return list(results.values())

def parse_api(data, results, keyword):
    """解析API数据"""
    if not isinstance(data, dict):
        return
    
    items = []
    if 'data' in data:
        d = data['data']
        if isinstance(d, dict):
            items.extend(d.get('report', []))
            items.extend(d.get('research', []))
            items.extend(d.get('list', []))
            items.extend(d.get('items', []))
        elif isinstance(d, list):
            items = d
    
    for item in items:
        if not isinstance(item, dict):
            continue
        title = (item.get('title') or '').replace('<em>', '').replace('</em>', '')
        if keyword not in title and '小米' not in title and '01810' not in title:
            continue
        if len(title) < 10:
            continue
        
        uid = title[:30]
        if uid in results:
            continue
        
        ts = item.get('time') or item.get('publishTime') or 0
        try:
            if isinstance(ts, (int, float)) and ts > 1000000000:
                time_str = datetime.fromtimestamp(int(ts)).strftime('%Y-%m-%d %H:%M')
            else:
                time_str = str(ts) if ts else ''
        except:
            time_str = ''
        
        # 提取研报特有信息
        org = item.get('orgName') or item.get('organization') or ''
        rating = item.get('rating') or item.get('ratingName') or ''
        
        results[uid] = {
            'title': title,
            'url': item.get('url', ''),
            'time': time_str,
            'org': org,
            'rating': rating,
            'source': 'API'
        }

def parse_dom(page, results, keyword):
    """解析DOM数据"""
    try:
        items = page.evaluate("""(kw) => {
            var res = [];
            var links = document.querySelectorAll('a');
            for (var i = 0; i < links.length; i++) {
                var a = links[i];
                var text = a.innerText || '';
                var href = a.href || '';
                // 研报链接通常包含 /report/ 或 /research/
                if ((text.indexOf('小米') >= 0 || text.indexOf(kw) >= 0 || text.indexOf('01810') >= 0) && 
                    text.length > 10 && 
                    (href.indexOf('/report/') >= 0 || href.indexOf('/research/') >= 0 || 
                     href.indexOf('/post/') >= 0 || href.indexOf('/notice/') >= 0)) {
                    res.push({
                        title: text.split('\\n')[0].substring(0, 200),
                        url: href
                    });
                }
            }
            return res;
        }""", keyword)
        
        for item in items:
            title = item.get('title', '')
            if len(title) < 10:
                continue
            uid = title[:30]
            if uid in results:
                continue
            results[uid] = {
                'title': title,
                'url': item.get('url', ''),
                'time': datetime.now().strftime('%Y-%m-%d %H:%M'),
                'org': '',
                'rating': '',
                'source': 'DOM'
            }
    except:
        pass

def main():
    if len(sys.argv) < 2:
        print("用法: python futu_report_scraper.py <关键词> [数量] [--json]")
        print("示例: python futu_report_scraper.py 小米集团 30")
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
    
    if keyword == "01810":
        keyword = "小米集团"
    
    # JSON 模式
    if json_mode:
        import json as json_lib
        import io, sys as sys_module
        old_stdout = sys_module.stdout
        sys_module.stdout = io.StringIO()
        data = scrape_futu_report(keyword, limit)
        sys_module.stdout = old_stdout
        print(json_lib.dumps(data, ensure_ascii=False))
        return
    
    # 普通模式
    print(f"{'='*50}")
    print(f"📈 富途研报爬虫 | {keyword} | 目标: {limit}")
    print(f"{'='*50}")
    
    start = time.time()
    data = scrape_futu_report(keyword, limit)
    elapsed = time.time() - start
    
    if data:
        try:
            data.sort(key=lambda x: x.get('time', ''), reverse=True)
        except:
            pass
        
        filename = f"{keyword}_富途研报_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(f"# {keyword} 富途研报\n\n")
            f.write(f"> 采集时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"> 来源: 资讯 > 研报\n")
            f.write(f"> 数量: {len(data)}\n")
            f.write(f"> 耗时: {elapsed:.1f}秒\n\n---\n\n")
            
            for i, item in enumerate(data, 1):
                f.write(f"## {i}. {item['title']}\n\n")
                f.write(f"- **时间**: {item.get('time', 'N/A')}\n")
                if item.get('org'):
                    f.write(f"- **机构**: {item['org']}\n")
                if item.get('rating'):
                    f.write(f"- **评级**: {item['rating']}\n")
                f.write(f"- **来源**: {item.get('source', 'N/A')}\n")
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

