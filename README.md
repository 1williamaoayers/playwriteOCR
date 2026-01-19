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
# 克隆仓库
git clone https://github.com/1williamaoayers/playwriteOCR.git
cd playwriteOCR

# 一键部署
./deploy.sh
```

### 本地运行

```bash
pip install -r requirements.txt
playwright install chromium
python app.py
```

## 📡 API接口

### 健康检查
```
GET /api/v1/health
```

### 获取数据源列表
```
GET /api/v1/sources
```

### 采集新闻
```
GET /api/v1/news?keyword=小米集团&sources=all&limit=20
```

**参数**:
- `keyword`: 搜索关键词（必填）
- `sources`: 数据源，逗号分隔或`all`（默认all）
- `limit`: 每个源采集数量（默认20）

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
