#!/usr/bin/env python3
"""
富途牛牛爬虫 - 最终修复版
关键: 使用 dispatchEvent 触发点击，子Tab选择器是 web_search-sec-tab-li
"""

import sys
import time
import signal
from datetime import datetime
from playwright.sync_api import sync_playwright

# 全局浏览器引用，用于信号处理
_browser = None


def signal_handler(signum, frame):
    """收到信号时清理浏览器并退出"""
    print("\n🛑 收到终止信号，正在关闭浏览器...")
    if _browser:
        try:
            _browser.close()
        except:
            pass
    sys.exit(1)


# 注册信号处理器
signal.signal(signal.SIGTERM, signal_handler)
signal.signal(signal.SIGINT, signal_handler)


def kill_existing_browsers():
    """清理可能残留的浏览器进程"""
    import subprocess

    try:
        # 杀掉残留的 chromium 进程
        subprocess.run(
            ["pkill", "-9", "-f", "chromium"], capture_output=True, timeout=5
        )
        subprocess.run(["pkill", "-9", "-f", "chrome"], capture_output=True, timeout=5)
        time.sleep(0.5)
    except:
        pass


def scrape_futu(keyword: str, target_count: int = 50, timeout: int = 120):
    """采集富途资讯 - 资讯>新闻子栏"""
    results = {}
    global _browser

    # 启动前清理残留浏览器
    kill_existing_browsers()

    with sync_playwright() as p:
        print("🚀 启动浏览器...")
        browser = p.chromium.launch(headless=True, args=["--no-sandbox"])
        _browser = browser
        context = browser.new_context(
            viewport={"width": 1920, "height": 1080},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0",
        )
        page = context.new_page()

        # API拦截器
        def on_response(response):
            try:
                if response.status == 200:
                    url = response.url
                    if "search" in url or "news" in url:
                        try:
                            data = response.json()
                            parse_api(data, results, keyword)
                        except:
                            pass
            except:
                pass

        page.on("response", on_response)

        try:
            # 1. 访问首页
            print("🌍 访问: https://news.futunn.com/main/live")
            page.goto(
                "https://news.futunn.com/main/live",
                wait_until="domcontentloaded",
                timeout=60000,
            )
            time.sleep(3)

            # 2. 输入搜索词
            print(f"🔍 搜索: {keyword}")
            search = page.locator("input.web_search-input").first
            search.click(force=True)
            time.sleep(0.3)
            search.fill(keyword)
            time.sleep(3)

            # 3. 使用JS点击资讯Tab (关键: dispatchEvent)
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

            # 4. 点击新闻子Tab (class: web_search-sec-tab-li)
            print("👉 点击 '新闻' 子Tab...")
            page.evaluate("""() => {
                var tabs = document.querySelectorAll('.web_search-sec-tab-li');
                for (var i = 0; i < tabs.length; i++) {
                    if (tabs[i].innerText && tabs[i].innerText.trim() === '新闻') {
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
                    print(f"📊 [第{i + 1}轮] 总数: {curr} (+{curr - prev})")

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
    if "data" in data:
        d = data["data"]
        if isinstance(d, dict):
            items.extend(d.get("news", []))
            items.extend(d.get("list", []))
            items.extend(d.get("items", []))
        elif isinstance(d, list):
            items = d

    for item in items:
        if not isinstance(item, dict):
            continue
        title = (item.get("title") or "").replace("<em>", "").replace("</em>", "")
        if keyword not in title and "小米" not in title and "01810" not in title:
            continue
        if len(title) < 10:
            continue

        uid = title[:30]
        if uid in results:
            continue

        ts = item.get("time") or item.get("publishTime") or 0
        try:
            if isinstance(ts, (int, float)) and ts > 1000000000:
                time_str = datetime.fromtimestamp(int(ts)).strftime("%Y-%m-%d %H:%M")
            else:
                time_str = str(ts) if ts else ""
        except:
            time_str = ""

        results[uid] = {
            "title": title,
            "url": item.get("url", ""),
            "time": time_str,
            "source": "API",
        }


def parse_dom(page, results, keyword):
    """解析DOM数据"""
    try:
        items = page.evaluate(
            """(kw) => {
            var res = [];
            var links = document.querySelectorAll('a');
            for (var i = 0; i < links.length; i++) {
                var a = links[i];
                var text = a.innerText || '';
                var href = a.href || '';
                if ((text.indexOf('小米') >= 0 || text.indexOf(kw) >= 0 || text.indexOf('01810') >= 0) && 
                    text.length > 10 && 
                    (href.indexOf('/post/') >= 0 || href.indexOf('/flash/') >= 0 || href.indexOf('/notice/') >= 0)) {
                    res.push({
                        title: text.split('\\n')[0].substring(0, 150),
                        url: href
                    });
                }
            }
            return res;
        }""",
            keyword,
        )

        for item in items:
            title = item.get("title", "")
            if len(title) < 10:
                continue
            uid = title[:30]
            if uid in results:
                continue
            results[uid] = {
                "title": title,
                "url": item.get("url", ""),
                "time": datetime.now().strftime("%Y-%m-%d %H:%M"),
                "source": "DOM",
            }
    except:
        pass


def main():
    if len(sys.argv) < 2:
        print("用法: python futu_scraper.py <关键词> [数量] [--json]")
        print("示例: python futu_scraper.py 小米集团 50")
        sys.exit(1)

    # 解析参数
    keyword = sys.argv[1]
    limit = 20
    json_mode = False

    for arg in sys.argv[2:]:
        if arg == "--json":
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
        data = scrape_futu(keyword, limit)
        sys_module.stdout = old_stdout
        print(json_lib.dumps(data, ensure_ascii=False))
        return

    # 普通模式
    print(f"{'=' * 50}")
    print(f"🎯 富途爬虫 | {keyword} | 目标: {limit}")
    print(f"{'=' * 50}")

    start = time.time()
    data = scrape_futu(keyword, limit)
    elapsed = time.time() - start

    if data:
        try:
            data.sort(key=lambda x: x.get("time", ""), reverse=True)
        except:
            pass

        filename = f"{keyword}_富途_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
        with open(filename, "w", encoding="utf-8") as f:
            f.write(f"# {keyword} 富途资讯\n\n")
            f.write(f"> 采集时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"> 来源: 资讯 > 新闻\n")
            f.write(f"> 数量: {len(data)}\n")
            f.write(f"> 耗时: {elapsed:.1f}秒\n\n---\n\n")

            for i, item in enumerate(data, 1):
                f.write(f"## {i}. {item['title']}\n\n")
                f.write(f"- 时间: {item.get('time', 'N/A')}\n")
                f.write(f"- 来源: {item.get('source', 'N/A')}\n")
                if item.get("url"):
                    f.write(f"- 链接: {item['url']}\n")
                f.write("\n")

        print(f"\n{'=' * 50}")
        print(f"✅ 完成: {len(data)}条 | {elapsed:.1f}秒")
        print(f"📄 保存: {filename}")
        print(f"{'=' * 50}")
    else:
        print(f"\n⚠️ 无数据 | {elapsed:.1f}秒")


if __name__ == "__main__":
    main()
