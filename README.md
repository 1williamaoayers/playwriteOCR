# PlaywriteOCR 财经爬虫

> 🕷️ 8个财经网站爬虫，支持Docker一键部署

## ✨ 特性

- **8个数据源**: 财联社、格隆汇、东方财富、富途新闻、富途研报、智通财经、今日头条、华尔街见闻
- **RESTful API**: 简单易用的JSON接口
- **Docker部署**: 一键部署到VPS，24小时运行
- **健康检查**: 自带健康监控接口

## 🚀 快速开始

### Docker部署（推荐）

```bash
# 方式1：一键拉取镜像运行（最简单）
docker run -d --name playwriteocr -p 9527:9527 ghcr.io/1williamaoayers/playwriteocr:latest

# 方式2：克隆仓库自行构建
git clone https://github.com/1williamaoayers/playwriteOCR.git
cd playwriteOCR && ./deploy.sh
```

### 本地运行

```bash
pip install -r requirements.txt
playwright install chromium
python app.py
```

## 📡 API接口

### 1. 健康检查
```bash
GET /api/v1/health
```
返回示例:
```json
{"status": "ok", "service": "playwrite-scraper", "version": "1.0.0", "scrapers_count": 8}
```

---

### 2. 获取数据源列表
```bash
GET /api/v1/sources
```
返回示例:
```json
{
  "success": true,
  "sources": [
    {"id": "eastmoney", "name": "东方财富", "estimated_time": "~10秒"},
    {"id": "gelonghui", "name": "格隆汇", "estimated_time": "~7秒"}
  ],
  "default": ["eastmoney", "gelonghui", "zhitong"]
}
```

---

### 3. 采集新闻（核心接口）
```bash
GET /api/v1/news?keyword=小米集团&sources=eastmoney,gelonghui&limit=20
```

**参数**:
| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| `keyword` | string | ✅ | - | 搜索关键词 |
| `sources` | string | ❌ | all | 数据源ID，逗号分隔或`all` |
| `limit` | int | ❌ | 20 | 每个源的采集数量 |

**可用数据源ID**: `eastmoney`, `gelonghui`, `cls`, `futu`, `futu_report`, `zhitong`, `wallstreet`, `toutiao`

**返回示例**:
```json
{
  "success": true,
  "keyword": "小米集团",
  "data": [
    {
      "symbol": "小米集团",
      "title": "小米汽车月交付突破3万台",
      "summary": "小米集团发布最新交付数据...",
      "source": "东方财富",
      "url": "https://...",
      "publish_time": "2026-01-19 09:30"
    }
  ],
  "metadata": {
    "total_count": 196,
    "sources_used": ["eastmoney", "gelonghui"],
    "duration_seconds": 18.5,
    "errors": null
  }
}
```

**错误返回**:
```json
{"success": false, "error": "缺少 keyword 参数"}
```

## 📊 数据源性能

| 数据源 | 预计耗时 |
|--------|----------|
| 格隆汇 | ~7秒 |
| 财联社 | ~8秒 |
| 东方财富 | ~10秒 |
| 华尔街见闻 | ~13秒 |
| 富途研报 | ~13秒 |
| 富途新闻 | ~17秒 |
| 智通财经 | ~24秒 |
| 今日头条 | ~65秒 |

## 🐳 Docker配置

- **端口**: 9527
- **内存限制**: 2GB
- **自动重启**: 除非手动停止
- **日志限制**: 30MB

## 📝 License

MIT
