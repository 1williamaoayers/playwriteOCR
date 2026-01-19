# PlaywriteOCR 财经信息聚合工具

> 🔍 多源财经信息聚合，支持Docker一键部署

> ⚠️ **免责声明**: 本项目仅供个人学习研究使用，请遵守各信息源的服务条款。使用者需自行承担使用风险，作者不对任何滥用行为负责。

## ✨ 特性

- **多数据源**: 支持8个主流财经信息源
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
{"status": "ok", "service": "playwrite-scraper", "version": "1.0.0"}
```

---

### 2. 采集新闻（核心接口）
```bash
GET /api/v1/news?keyword=小米集团&limit=20
```

**参数**:
| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| `keyword` | string | ✅ | - | 搜索关键词 |
| `limit` | int | ❌ | 20 | 采集数量 |

**curl调用示例**（支持任意关键词）:
```bash
# 查询腾讯新闻
curl -G "http://localhost:9527/api/v1/news" --data-urlencode "keyword=腾讯" -d "limit=20"

# 查询京东
curl -G "http://localhost:9527/api/v1/news" --data-urlencode "keyword=京东"

# 查询茅台
curl -G "http://localhost:9527/api/v1/news" --data-urlencode "keyword=贵州茅台" -d "limit=50"
```

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
| 源A | ~7秒 |
| 源B | ~8秒 |
| 源C | ~10秒 |
| 源D | ~13秒 |
| 源E | ~13秒 |
| 源F | ~17秒 |
| 源G | ~24秒 |
| 源H | ~65秒 |

## 🐳 Docker配置

- **端口**: 9527
- **内存限制**: 2GB
- **自动重启**: 除非手动停止
- **日志限制**: 30MB

## 📝 License

MIT

---

**注意**: 请合理使用，尊重各信息源的版权和服务条款。
