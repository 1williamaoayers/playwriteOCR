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


def scrape_zhitong(keyword: str, target_count: int = 20, proxy: str = ""):
    results = []
    seen = set()

    with sync_playwright() as p:
        print("🚀 启动浏览器...")
        browser = p.chromium.launch(headless=True, args=["--no-sandbox"])

        context = browser.new_context(viewport={"width": 1920, "height": 1080})

        if proxy:
            print(f"🔗 使用代理: {proxy}")
            context = browser.new_context(
                viewport={"width": 1920, "height": 1080}, proxy={"server": proxy}
            )
        else:
            context = browser.new_context(viewport={"width": 1920, "height": 1080})

        page = context.new_page()

        try:
            # 1. 访问首页
            print("🌍 访问首页...")
            page.goto(
                "https://www.zhitongcaijing.com/",
                wait_until="domcontentloaded",
                timeout=60000,
            )
            time.sleep(3)

            # 2. 输入关键词
            print(f"🔍 搜索: {keyword}")
            search_input = page.locator("input.search-input-head").first
            search_input.fill(keyword)
            time.sleep(1)

            # 3. 监听新窗口，点击搜索
            with context.expect_page() as new_page_info:
                page.click("text=搜索", force=True)

            new_page = new_page_info.value
            print(f"📄 新窗口: {new_page.url[:80]}...")
            time.sleep(3)

            # 4. 点击"快讯"tab（用JS执行点击，避免元素定位问题）
            print("👉 点击 '快讯' Tab...")
            clicked = new_page.evaluate("""() => {
                const tabs = document.querySelectorAll('a');
                for (const tab of tabs) {
                    if (tab.innerText.trim() === '快讯' && tab.href.includes('type=immediately')) {
                        tab.click();
                        return tab.href;
                    }
                }
                return null;
            }""")
            print(f"✅ 快讯Tab URL: {clicked}")
            time.sleep(3)

            print(f"📊 采集快讯 (目标: {target_count})...")

            # 5. 滚动采集
            for scroll_round in range(10):
                items = new_page.evaluate("""() => {
                    var results = [];
                    
                    // 查找搜索结果页的快讯条目 - 使用 .search-flashnews-box 选择器
                    document.querySelectorAll('.search-flashnews-box').forEach(function(item) {
                        var timeEl = item.querySelector('.time-box');
                        var contentDiv = item.querySelector('div:first-child');
                        
                        var time = timeEl ? timeEl.innerText.trim() : '';
                        var content = contentDiv ? contentDiv.innerText.trim() : '';
                        
                        // 时间格式可能是 HH:MM:SS 或 YYYY-MM-DD HH:MM:SS
                        // 如果是短格式，补充当前日期
                        var fullTime = time;
                        if (time && !time.includes('-')) {
                            var today = new Date();
                            var dateStr = today.getFullYear() + '-' + 
                                String(today.getMonth() + 1).padStart(2, '0') + '-' + 
                                String(today.getDate()).padStart(2, '0');
                            fullTime = dateStr + ' ' + time;
                        }
                        
                        // 提取标题（【】内的内容）
                        var title = '';
                        var bracketMatch = content.match(/【(.+?)】/);
                        if (bracketMatch) {
                            title = bracketMatch[1];
                        } else if (content.length > 10) {
                            title = content.substring(0, 100);
                        }
                        
                        // 搜索结果页快讯没有URL，使用搜索页URL（提取keyword参数）
                        var baseUrl = window.location.href.split('?')[0];
                        var href = window.location.href;
                        var keywordMatch = href.match(/keyword=([^&]+)/);
                        var keyword = keywordMatch ? decodeURIComponent(keywordMatch[1]) : '';
                        var url = baseUrl + '?keyword=' + encodeURIComponent(keyword) + '&type=immediately';
                        
                        if (title && time) {
                            results.push({
                                title: title.substring(0, 200),
                                time: fullTime,
                                url: url
                            });
                        }
                    });
                    
                    return results;
                }""")

                for item in items:
                    uid = item["title"][:30]
                    if uid not in seen:
                        seen.add(uid)
                        results.append(item)

                print(f"📊 [第{scroll_round + 1}轮] 采集: {len(results)} 条")

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
    results.sort(key=lambda x: x.get("time", ""), reverse=True)
    return results[:target_count]


def main():
    if len(sys.argv) < 2:
        print(
            "用法: python zhitong_scraper.py <关键词> [数量] [--json] [--proxy <代理地址>]"
        )
        sys.exit(1)

    # 解析参数
    keyword = sys.argv[1]
    limit = 20
    json_mode = False
    proxy = ""

    i = 2
    while i < len(sys.argv):
        arg = sys.argv[i]
        if arg == "--json":
            json_mode = True
        elif arg == "--proxy" and i + 1 < len(sys.argv):
            proxy = sys.argv[i + 1]
            i += 2
        elif arg.isdigit():
            limit = int(arg)
            i += 1
        else:
            i += 1

    # JSON 模式
    if json_mode:
        import json as json_lib
        import io, sys as sys_module

        old_stdout = sys_module.stdout
        sys_module.stdout = io.StringIO()
        data = scrape_zhitong(keyword, limit, proxy)
        sys_module.stdout = old_stdout
        print(json_lib.dumps(data, ensure_ascii=False))
        return

    # 普通模式
    print(f"{'=' * 50}")
    print(f"📰 智通财经爬虫 | {keyword} | 目标: {limit}")
    print(f"{'=' * 50}")

    start = time.time()
    data = scrape_zhitong(keyword, limit, proxy)
    elapsed = time.time() - start

    if data:
        filename = f"{keyword}_智通财经_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
        with open(filename, "w", encoding="utf-8") as f:
            f.write(f"# {keyword} 智通财经快讯\n\n")
            f.write(f"> 采集时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"> 数量: {len(data)}\n")
            f.write(f"> 耗时: {elapsed:.1f}秒\n\n---\n\n")
            for i, item in enumerate(data, 1):
                f.write(f"## {i}. {item['title']}\n\n")
                if item.get("time"):
                    f.write(f"- **时间**: {item['time']}\n")
                if item.get("url"):
                    f.write(f"- **链接**: {item['url']}\n")
                f.write("\n")

        print(f"\n{'=' * 50}")
        print(f"✅ 完成: {len(data)}条 | {elapsed:.1f}秒")
        print(f"📄 保存: {filename}")
        print(f"{'=' * 50}")
    else:
        print(f"\n⚠️ 无数据")


if __name__ == "__main__":
    main()
