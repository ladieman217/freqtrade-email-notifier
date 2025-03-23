# Freqtrade 邮件通知器

一个接收 Freqtrade 交易机器人 webhook 并使用 AWS SES 发送邮件通知的 Python 服务。

## 功能特点

- 接收来自 Freqtrade 交易机器人的 webhook
- 使用 AWS SES 发送格式化的邮件通知
- 同时支持纯文本和 HTML 邮件格式
- 基于 FastAPI 构建，提供高性能和异步处理
- 通过环境变量进行配置
- 自动生成 API 文档 (Swagger UI)
- API 密钥认证，增强安全性
- 使用 Docker 容器化，便于部署

## 系统要求

- Python 3.7+
- AWS 账户并配置 SES 服务
- 在 SES 中验证的发件人邮箱地址

## 使用 Docker 快速开始

使用 Docker 是运行此服务的最简单方式：

```bash
# 克隆仓库
git clone https://github.com/yourusername/freqtrade-email-notifier.git
cd freqtrade-email-notifier

# 创建 .env 文件
cp .env.example .env
# 编辑 .env 文件，设置您的 AWS 凭证和邮件配置

# 使用 Docker Compose 启动服务
docker-compose up -d
```

## 使用虚拟环境安装

### Linux/Mac

1. 克隆此仓库
2. 使用安装脚本创建虚拟环境并安装依赖：
```
chmod +x setup.sh
./setup.sh
```
3. 此脚本将：
   - 在 `.venv` 目录中创建虚拟环境
   - 安装所有必需的依赖
   - 如果不存在，从 `.env.example` 创建 `.env` 文件

4. 编辑 `.env` 文件，设置您的 AWS 凭证和邮件配置
5. 确保您的发件人邮箱在 AWS SES 中已验证

### Windows

1. 克隆此仓库
2. 使用安装脚本创建虚拟环境并安装依赖：
```
setup.bat
```
3. 此脚本将：
   - 在 `.venv` 目录中创建虚拟环境
   - 安装所有必需的依赖
   - 如果不存在，从 `.env.example` 创建 `.env` 文件

4. 编辑 `.env` 文件，设置您的 AWS 凭证和邮件配置
5. 确保您的发件人邮箱在 AWS SES 中已验证

## 配置说明

应用程序使用环境变量进行配置。将 `.env.example` 文件复制为 `.env` 并配置以下内容：

### 邮件配置
- `EMAIL_SENDER`：您在 SES 中验证的发件人邮箱地址
- `EMAIL_RECIPIENT`：接收通知的邮箱地址

### AWS 配置
- `AWS_ACCESS_KEY_ID`：您的 AWS 访问密钥
- `AWS_SECRET_ACCESS_KEY`：您的 AWS 秘密密钥
- `AWS_REGION`：配置 SES 服务的 AWS 区域

### 安全配置
- `API_KEY`：webhook 端点认证的密钥（留空则禁用认证）

### 服务器配置
- `PORT`：服务器端口（默认：5001）

## 运行服务

### 使用 Docker：

```bash
# 启动服务
docker-compose up -d

# 查看日志
docker-compose logs -f

# 停止服务
docker-compose down
```

### 使用运行脚本：

Linux/Mac:
```
chmod +x run.sh
./run.sh
```

Windows:
```
run.bat
```

### 手动启动：

1. 激活虚拟环境（如果尚未激活）：
   - Linux/Mac: `source .venv/bin/activate`
   - Windows: `.venv\Scripts\activate`

2. 启动服务：
```
python app.py
```

对于生产环境部署，您可以使用：

```
uvicorn app:app --host 127.0.0.1 --port 5001
```

## API 文档

FastAPI 自动生成交互式 API 文档。启动服务器后，访问：

- Swagger UI: http://localhost:5001/docs
- ReDoc: http://localhost:5001/redoc

## Freqtrade 配置

在您的 Freqtrade 配置文件中，添加 webhook URL：

```json
"webhook": {
    "enabled": true,
    "url": "http://your-server-address:5001/webhook",
    "format": "json"
}
```

如果您启用了 API 密钥认证，有两个选项：

### 1. URL 查询参数认证（推荐）

```json
"webhook": {
    "enabled": true,
    "url": "http://your-server-address:5001/webhook?token=your_secret_api_key",
    "format": "json"
}
```

### 2. 路径认证

```json
"webhook": {
    "enabled": true,
    "url": "http://your-server-address:5001/webhook/your_secret_api_key",
    "format": "json"
}
```

## 安全注意事项

- 在生产环境中始终使用 HTTPS
- 如果启用认证，请设置强密钥
- 永远不要将您的 `.env` 文件提交到版本控制系统
- 确保您的 AWS 凭证具有最小所需权限
- 配置 SES 发送限制，以避免意外成本

## 测试

### 单元测试

使用以下命令运行单元测试：

```bash
# 直接使用 pytest
pytest tests/ -v

# 或使用测试脚本
./run_tests.sh
```

### 集成测试

您可以使用 curl 测试 webhook 端点：

```
curl -X POST http://localhost:5001/webhook?token=your_secret_api_key \
  -H "Content-Type: application/json" \
  -d '{"type":"entry","exchange":"binance","pair":"BTC/USDT","side":"buy","price":20000,"amount":0.05}'
```

或使用包含的测试脚本：

```bash
# 测试所有 webhook 类型
python test_webhook.py --verbose

# 测试特定 webhook 类型
python test_webhook.py --type entry --verbose
```

## 贡献

欢迎贡献！请随时提交 Pull Request。

1. Fork 仓库
2. 创建您的功能分支 (`git checkout -b feature/amazing-feature`)
3. 提交您的更改 (`git commit -m '添加一些惊人的功能'`)
4. 推送到分支 (`git push origin feature/amazing-feature`)
5. 开启一个 Pull Request

## 许可证

此项目基于 MIT 许可证 - 详见 [LICENSE](LICENSE) 文件。 