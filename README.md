# Azure Functions MCP Server with Managed ID Authentication

Azure App ServiceからAzure Functions MCP ServerへのManaged ID認証を実装するPoC（Proof of Concept）プロジェクトです。

## アーキテクチャ

```
[App Service (React Frontend)] --Bearer Token(Managed ID)--> [Azure Functions (MCP Server)] --> [Azure OpenAI GPT-5]
                                                                   ↓
                                                              [MCP Binding Extension]
                                                                   ↓
                                                              [MCP Tools]
                                                             - Current Time
                                                             - Weather Info
```

## 構成

### フロントエンド (App Service)
- **技術**: React + TypeScript + Azure Identity SDK
- **場所**: `src/web/`
- **認証**: Azure Managed ID を使用してBearer Tokenを取得

### バックエンド (Azure Functions)
- **技術**: Python + Azure Functions MCP Binding
- **場所**: `src/functions/`
- **MCPツール**:
  - `get_current_time`: 現在時刻取得
  - `get_weather_info`: 天気情報取得（モックデータ）

## 必要な環境

### 開発環境
- Node.js 18.x以上
- Python 3.11以上
- Azure Functions Core Tools v4
- Azure CLI

### Azure環境
- Azure Subscription
- App Service (F1 Free Plan)
- Azure Functions (Consumption Plan)
- Application Insights

## ローカル開発環境構築

### 1. リポジトリクローン

```bash
git clone <your-repo-url>
cd mcp-functions-managedid-auth
```

### 2. Azure Functions (バックエンド) 設定

```bash
cd src/functions

# Python仮想環境作成
python -m venv .venv

# 仮想環境有効化 (Windows)
.venv\Scripts\activate
# 仮想環境有効化 (macOS/Linux)
source .venv/bin/activate

# 依存関係インストール
pip install -r requirements.txt

# Azure Functions Core Tools インストール (未インストールの場合)
npm install -g azure-functions-core-tools@4 --unsafe-perm true
```

### 3. フロントエンド設定

```bash
cd ../web

# 依存関係インストール
npm install
```

## ローカル動作確認

### 1. Azure Functions (バックエンド) 起動

```bash
cd src/functions

# 仮想環境有効化 (必要に応じて)
.venv\Scripts\activate  # Windows
# source .venv/bin/activate  # macOS/Linux

# Azure Functions 起動
func start
```

期待される出力:
```
Azure Functions Core Tools
Core Tools Version:       4.x.x
Function Runtime Version: 4.x.x

Functions:
  get_current_time: mcpToolTrigger
  get_weather_info: mcpToolTrigger
  health: [GET] http://localhost:7071/api/health
  test-auth: [GET,POST] http://localhost:7071/api/test-auth

Host lock lease acquired by instance ID: xxxxx
```

### 2. Azure Functions APIテスト

#### ヘルスチェック
```bash
curl http://localhost:7071/api/health
```

期待される結果:
```json
{
  "status": "healthy",
  "timestamp": "2025-01-19T12:34:56.789Z",
  "service": "MCP Functions Server"
}
```

#### 認証テスト (開発時はトークンなしでもOK)
```bash
curl http://localhost:7071/api/test-auth
```

### 3. MCPツールのテスト

MCPツールは通常MCPクライアント経由でアクセスされますが、開発時は以下の方法でテストできます：

#### MCP Inspector使用 (推奨)

1. MCP Inspector インストール:
```bash
npx @modelcontextprotocol/inspector
```

2. Azure Functions MCP サーバーに接続:
- Server URL: `http://localhost:7071`
- Transport: HTTP

#### cURLによる直接テスト (参考)

**現在時刻取得:**
```bash
curl -X POST http://localhost:7071/api/get_current_time \
  -H "Content-Type: application/json" \
  -d '{
    "arguments": {
      "timezone": "Asia/Tokyo",
      "format": "locale"
    }
  }'
```

**天気情報取得:**
```bash
curl -X POST http://localhost:7071/api/get_weather_info \
  -H "Content-Type: application/json" \
  -d '{
    "arguments": {
      "location": "Tokyo,Japan",
      "date": "2025-01-19"
    }
  }'
```

### 4. フロントエンド起動

別のターミナルで:

```bash
cd src/web

# 環境変数設定
# .env.local ファイルを作成
echo "REACT_APP_FUNCTION_URL=http://localhost:7071" > .env.local

# 開発サーバー起動
npm start
```

ブラウザで `http://localhost:3000` にアクセス

### 5. 統合テスト

1. フロントエンドのチャットインターフェースで以下を試してください：
   - "What time is it?"
   - "What's the weather like in Tokyo?"
   - "現在の時刻を教えて"
   - "東京の天気はどうですか？"

2. **注意**: ローカル開発時はManaged ID認証は動作しないため、認証エラーが発生する可能性があります。これは正常な動作です。

## 環境変数

### Azure Functions (.env または local.settings.json)

```json
{
  "IsEncrypted": false,
  "Values": {
    "AzureWebJobsStorage": "UseDevelopmentStorage=true",
    "FUNCTIONS_WORKER_RUNTIME": "python",
    "AZURE_OPENAI_ENDPOINT": "https://your-openai.openai.azure.com/",
    "AZURE_OPENAI_DEPLOYMENT_NAME": "gpt-4",
    "AZURE_CLIENT_ID": "your-managed-identity-client-id"
  }
}
```

### フロントエンド (.env.local)

```
REACT_APP_FUNCTION_URL=http://localhost:7071
```

## トラブルシューティング

### よくある問題

#### 1. Python仮想環境の問題
```bash
# 仮想環境を再作成
rm -rf .venv
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

#### 2. Azure Functions Core Toolsの問題
```bash
# 最新版をインストール
npm uninstall -g azure-functions-core-tools
npm install -g azure-functions-core-tools@4 --unsafe-perm true
```

#### 3. ポートの競合
```bash
# 別のポートでFunctions起動
func start --port 7072
```

その後、フロントエンドの環境変数も更新:
```
REACT_APP_FUNCTION_URL=http://localhost:7072
```

#### 4. MCPツールが認識されない
- `@app.generic_trigger` デコレータが正しく設定されているか確認
- `toolName` が重複していないか確認
- Python構文エラーがないか確認

#### 5. 認証エラー (ローカル開発時)
ローカル開発時は以下の対処法があります：

1. **認証をスキップする開発モード実装**:
```python
# 開発環境では認証をスキップ
if os.getenv('AZURE_FUNCTIONS_ENVIRONMENT') == 'Development':
    auth_result = {"authorized": True, "principal": {"sub": "dev-user"}}
else:
    auth_result = await authenticator.authorize(req)
```

2. **モックトークンの使用**:
```bash
# テスト用のBearer token付きリクエスト
curl -H "Authorization: Bearer mock-token" http://localhost:7071/api/test-auth
```

## デプロイ

### Azure Developer CLI使用 (推奨)

```bash
# Azure Developer CLIでデプロイ
azd up
```

### 手動デプロイ

```bash
# Azure Functions デプロイ
cd src/functions
func azure functionapp publish <your-function-app-name>

# App Service デプロイ
cd ../web
npm run build
# Azureポータルでzipデプロイ
```

## 次のステップ

1. **実際の天気API統合**: OpenWeatherMap API等を使用
2. **セキュリティ強化**: CORS設定、IP制限等
3. **監視設定**: Application Insights ダッシュボード
4. **負荷テスト**: Azure Load Testing使用
5. **CI/CD パイプライン**: GitHub Actions設定

## 参考資料

- [Azure Functions MCP Binding Documentation](https://learn.microsoft.com/en-us/azure/azure-functions/functions-create-ai-enabled-apps)
- [Model Context Protocol Specification](https://modelcontextprotocol.io/)
- [Azure Managed Identity Documentation](https://learn.microsoft.com/en-us/azure/active-directory/managed-identities-azure-resources/)

## ライセンス

MIT License