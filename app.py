#!/usr/bin/env python3
"""
财经爬虫Web控制台
Flask后端 + 前端界面
"""

import os
import sys
import json
import time
import subprocess
import threading
from datetime import datetime
from flask import Flask, render_template_string, jsonify, request

app = Flask(__name__)

# 爬虫配置
SCRAPERS = {
    'toutiao': {'name': '今日头条', 'file': 'scrapers/toutiao_scraper.py', 'time': '~65秒'},
    'cls': {'name': '财联社', 'file': 'scrapers/cls_scraper.py', 'time': '~8秒'},
    'wallstreet': {'name': '华尔街见闻', 'file': 'scrapers/wallstreet_scraper.py', 'time': '~13秒'},
    'futu': {'name': '富途新闻', 'file': 'scrapers/futu_scraper.py', 'time': '~17秒'},
    'futu_report': {'name': '富途研报', 'file': 'scrapers/futu_report_scraper.py', 'time': '~13秒'},
    'gelonghui': {'name': '格隆汇', 'file': 'scrapers/gelonghui_scraper.py', 'time': '~7秒'},
    'eastmoney': {'name': '东方财富', 'file': 'scrapers/eastmoney_scraper.py', 'time': '~10秒'},
}

# 任务状态
tasks = {}

HTML_TEMPLATE = '''
<!DOCTYPE html>
<html lang="zh">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>财经爬虫控制台</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        
        body {
            font-family: 'Segoe UI', system-ui, sans-serif;
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%);
            min-height: 100vh;
            color: #fff;
        }
        
        .container {
            max-width: 1200px;
            margin: 0 auto;
            padding: 40px 20px;
        }
        
        h1 {
            text-align: center;
            font-size: 2.5rem;
            margin-bottom: 40px;
            background: linear-gradient(90deg, #00d4ff, #7b2cbf);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }
        
        .panel {
            background: rgba(255,255,255,0.05);
            border-radius: 16px;
            padding: 30px;
            margin-bottom: 30px;
            backdrop-filter: blur(10px);
            border: 1px solid rgba(255,255,255,0.1);
        }
        
        .panel h2 {
            font-size: 1.2rem;
            margin-bottom: 20px;
            color: #00d4ff;
        }
        
        .input-group {
            display: flex;
            gap: 15px;
            margin-bottom: 20px;
            flex-wrap: wrap;
        }
        
        .input-group input {
            flex: 1;
            min-width: 200px;
            padding: 15px 20px;
            border: none;
            border-radius: 10px;
            background: rgba(255,255,255,0.1);
            color: #fff;
            font-size: 1rem;
        }
        
        .input-group input::placeholder { color: rgba(255,255,255,0.5); }
        .input-group input:focus { outline: 2px solid #00d4ff; }
        
        .count-control {
            display: flex;
            align-items: center;
            gap: 15px;
            background: rgba(255,255,255,0.1);
            padding: 10px 20px;
            border-radius: 10px;
        }
        
        .count-control input[type="range"] {
            width: 150px;
            accent-color: #00d4ff;
        }
        
        .count-control span { font-weight: bold; color: #00d4ff; }
        
        .sources {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(180px, 1fr));
            gap: 15px;
        }
        
        .source-item {
            background: rgba(255,255,255,0.05);
            padding: 15px;
            border-radius: 10px;
            cursor: pointer;
            transition: all 0.3s;
            border: 2px solid transparent;
        }
        
        .source-item:hover { background: rgba(255,255,255,0.1); }
        .source-item.selected { border-color: #00d4ff; background: rgba(0,212,255,0.1); }
        
        .source-item label {
            display: flex;
            align-items: center;
            gap: 10px;
            cursor: pointer;
        }
        
        .source-item input { display: none; }
        
        .source-item .checkbox {
            width: 20px;
            height: 20px;
            border: 2px solid rgba(255,255,255,0.3);
            border-radius: 5px;
            display: flex;
            align-items: center;
            justify-content: center;
        }
        
        .source-item.selected .checkbox {
            background: #00d4ff;
            border-color: #00d4ff;
        }
        
        .source-item.selected .checkbox::after {
            content: '✓';
            color: #1a1a2e;
            font-weight: bold;
        }
        
        .source-time { font-size: 0.8rem; color: rgba(255,255,255,0.5); margin-top: 5px; }
        
        .btn {
            background: linear-gradient(90deg, #00d4ff, #7b2cbf);
            border: none;
            padding: 15px 40px;
            border-radius: 10px;
            color: #fff;
            font-size: 1.1rem;
            font-weight: bold;
            cursor: pointer;
            transition: transform 0.2s, box-shadow 0.2s;
        }
        
        .btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 10px 30px rgba(0,212,255,0.3);
        }
        
        .btn:disabled {
            opacity: 0.5;
            cursor: not-allowed;
            transform: none;
        }
        
        .btn-group {
            display: flex;
            gap: 15px;
            justify-content: center;
            margin-top: 30px;
        }
        
        .results {
            margin-top: 30px;
        }
        
        .result-item {
            background: rgba(255,255,255,0.05);
            border-radius: 10px;
            padding: 20px;
            margin-bottom: 15px;
        }
        
        .result-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 15px;
        }
        
        .result-source {
            font-weight: bold;
            color: #00d4ff;
        }
        
        .result-status {
            padding: 5px 15px;
            border-radius: 20px;
            font-size: 0.9rem;
        }
        
        .status-running { background: #f39c12; color: #000; }
        .status-done { background: #27ae60; }
        .status-error { background: #e74c3c; }
        
        .result-content {
            max-height: 300px;
            overflow-y: auto;
            background: rgba(0,0,0,0.3);
            padding: 15px;
            border-radius: 8px;
            font-family: monospace;
            font-size: 0.9rem;
            white-space: pre-wrap;
        }
        
        .select-all {
            display: flex;
            gap: 15px;
            margin-bottom: 15px;
        }
        
        .select-all button {
            background: rgba(255,255,255,0.1);
            border: none;
            padding: 8px 15px;
            border-radius: 5px;
            color: #fff;
            cursor: pointer;
        }
        
        .select-all button:hover { background: rgba(255,255,255,0.2); }
    </style>
</head>
<body>
    <div class="container">
        <h1>🚀 财经爬虫控制台</h1>
        
        <div class="panel">
            <h2>📝 搜索设置</h2>
            <div class="input-group">
                <input type="text" id="keyword" placeholder="输入关键词，如：小米集团、腾讯、京东..." value="小米集团">
                <div class="count-control">
                    <span>采集量:</span>
                    <input type="range" id="count" min="10" max="100" value="20" oninput="updateCount()">
                    <span id="countValue">20</span>
                </div>
            </div>
        </div>
        
        <div class="panel">
            <h2>📊 数据源选择</h2>
            <div class="select-all">
                <button onclick="selectAll()">全选</button>
                <button onclick="selectNone()">取消全选</button>
            </div>
            <div class="sources" id="sources"></div>
        </div>
        
        <div class="btn-group">
            <button class="btn" id="startBtn" onclick="startScraping()">🔍 开始采集</button>
        </div>
        
        <div class="results" id="results"></div>
    </div>
    
    <script>
        const scrapers = ''' + json.dumps(SCRAPERS) + ''';
        
        function init() {
            const container = document.getElementById('sources');
            for (const [key, info] of Object.entries(scrapers)) {
                const div = document.createElement('div');
                div.className = 'source-item' + (selectedSources.has(key) ? ' selected' : '');
                div.onclick = () => toggleSource(key, div);
                div.innerHTML = `
                    <label>
                        <div class="checkbox"></div>
                        <span>${info.name}</span>
                    </label>
                    <div class="source-time">${info.time}</div>
                `;
                container.appendChild(div);
            }
        }
        
        function toggleSource(key, div) {
            if (selectedSources.has(key)) {
                selectedSources.delete(key);
                div.classList.remove('selected');
            } else {
                selectedSources.add(key);
                div.classList.add('selected');
            }
        }
        
        function selectAll() {
            selectedSources = new Set(Object.keys(scrapers));
            document.querySelectorAll('.source-item').forEach(div => div.classList.add('selected'));
        }
        
        function selectNone() {
            selectedSources.clear();
            document.querySelectorAll('.source-item').forEach(div => div.classList.remove('selected'));
        }
        
        function updateCount() {
            document.getElementById('countValue').textContent = document.getElementById('count').value;
        }
        
        async function startScraping() {
            const keyword = document.getElementById('keyword').value.trim();
            const count = document.getElementById('count').value;
            const sources = Array.from(selectedSources);
            
            if (!keyword) { alert('请输入关键词'); return; }
            if (sources.length === 0) { alert('请选择至少一个数据源'); return; }
            
            document.getElementById('startBtn').disabled = true;
            document.getElementById('results').innerHTML = '';
            
            for (const source of sources) {
                addResultItem(source, 'running', '采集中...');
            }
            
            try {
                const res = await fetch('/api/scrape', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({keyword, count, sources})
                });
                const data = await res.json();
                
                for (const [source, result] of Object.entries(data)) {
                    updateResultItem(source, result.status, result.message);
                }
            } catch (e) {
                alert('请求失败: ' + e.message);
            }
            
            document.getElementById('startBtn').disabled = false;
        }
        
        function addResultItem(source, status, message) {
            const container = document.getElementById('results');
            const div = document.createElement('div');
            div.className = 'result-item';
            div.id = 'result-' + source;
            div.innerHTML = `
                <div class="result-header">
                    <span class="result-source">${scrapers[source].name}</span>
                    <span class="result-status status-${status}">${status === 'running' ? '采集中' : status}</span>
                </div>
                <div class="result-content">${message}</div>
            `;
            container.appendChild(div);
        }
        
        function updateResultItem(source, status, message) {
            const div = document.getElementById('result-' + source);
            if (div) {
                div.querySelector('.result-status').className = 'result-status status-' + status;
                div.querySelector('.result-status').textContent = status === 'done' ? '完成' : (status === 'error' ? '失败' : status);
                div.querySelector('.result-content').textContent = message;
            }
        }
        
        init();
    </script>
</body>
</html>
'''

# ========== RESTful API 端点 ==========
# 供股票分析项目等外部系统调用

@app.route('/api/v1/health')
def api_health():
    """健康检查"""
    return jsonify({
        'status': 'ok',
        'service': 'playwrite-scraper',
        'version': '1.0.0',
        'scrapers_count': len(SCRAPERS)
    })

# /api/v1/sources 接口已移除，不对外暴露数据源列表

@app.route('/api/v1/news')
def api_news():
    """采集新闻 - JSON API
    
    参数:
        keyword: 关键词 (必须)
        limit: 每个源的采集数量 (默认 20)
    
    示例:
        /api/v1/news?keyword=小米集团&limit=20
    """
    keyword = request.args.get('keyword', '')
    limit = request.args.get('limit', '20', type=int)
    
    if not keyword:
        return jsonify({'success': False, 'error': '缺少 keyword 参数'}), 400
    
    # 强制使用所有数据源，不提供选择
    sources = list(SCRAPERS.keys())
    
    start_time = time.time()
    all_results = []
    errors = []
    
    for source in sources:
        scraper = SCRAPERS[source]
        try:
            # 运行爬虫，使用 --json 模式
            cmd = [sys.executable, scraper['file'], keyword, str(limit), '--json']
            proc = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
            
            if proc.returncode == 0:
                try:
                    items = json.loads(proc.stdout)
                    # 转换为股票项目需要的标准格式
                    for item in items:
                        standardized = {
                            'symbol': keyword,
                            'title': item.get('title', ''),
                            'summary': item.get('summary', ''),
                            'content': item.get('summary', ''),  # 用摘要作为正文
                            'source': scraper['name'],
                            'source_type': 'scraper',
                            'url': item.get('url', ''),
                            'publish_time': item.get('time', ''),
                            'sentiment': 'neutral',
                            'relevance_score': 0.8,
                            'tags': [keyword],
                            'created_at': datetime.now().isoformat()
                        }
                        all_results.append(standardized)
                except json.JSONDecodeError:
                    errors.append(f"{source}: JSON解析失败")
            else:
                errors.append(f"{source}: {proc.stderr[:100]}")
                
        except subprocess.TimeoutExpired:
            errors.append(f"{source}: 采集超时")
        except Exception as e:
            errors.append(f"{source}: {str(e)}")
    
    elapsed = time.time() - start_time
    
    return jsonify({
        'success': True,
        'keyword': keyword,
        'data': all_results,
        'metadata': {
            'total_count': len(all_results),
            'sources_used': sources,
            'duration_seconds': round(elapsed, 2),
            'errors': errors if errors else None
        }
    })

# ========== Web 界面 ==========

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route('/api/scrape', methods=['POST'])
def api_scrape():
    data = request.json
    keyword = data.get('keyword', '')
    count = data.get('count', 20)
    sources = data.get('sources', [])
    
    results = {}
    
    for source in sources:
        if source not in SCRAPERS:
            results[source] = {'status': 'error', 'message': '未知数据源'}
            continue
        
        scraper = SCRAPERS[source]
        try:
            # 运行爬虫
            cmd = [sys.executable, scraper['file'], keyword, str(count)]
            proc = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
            
            if proc.returncode == 0:
                # 查找生成的文件
                import glob
                files = glob.glob(f'{keyword}_{scraper["name"]}_*.md')
                files.sort(reverse=True)
                
                if files:
                    with open(files[0], 'r', encoding='utf-8') as f:
                        content = f.read()
                    results[source] = {'status': 'done', 'message': content[:2000] + '\n...(更多内容请查看文件)' if len(content) > 2000 else content}
                else:
                    results[source] = {'status': 'done', 'message': proc.stdout}
            else:
                results[source] = {'status': 'error', 'message': proc.stderr or proc.stdout}
                
        except subprocess.TimeoutExpired:
            results[source] = {'status': 'error', 'message': '采集超时'}
        except Exception as e:
            results[source] = {'status': 'error', 'message': str(e)}
    
    return jsonify(results)

if __name__ == '__main__':
    print("🚀 启动财经爬虫控制台...")
    print("📍 访问: http://localhost:9527")
    app.run(host='0.0.0.0', port=9527, debug=False)
