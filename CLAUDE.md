# Azure Functions MCP Server with Managed ID Authentication

## プロジェクト概要
Azure App ServiceからAzure Functions MCP ServerへのManaged ID認証を実装するPoC

## アーキテクチャ
```
[App Service (チャットUI)] --Bearer Token(Managed ID)--> [Azure Functions (MCP Server)] --> [Azure OpenAI GPT-5]
                                                              ↓
                                                         [MCP Binding Extension]
```

## Azure構成
- **App Service**: F1 Free Plan (Frontend: React/Node.js)
- **Azure Functions**: Consumption Plan Y1 (Backend: TypeScript)  
- **Azure OpenAI**: Standard (GPT-5)
- **Application Insights**: 基本プラン

## 認証フロー
1. App Service Managed ID → Access Token取得
2. Functions呼び出し時 Bearer Token付与
3. Functions側でJWT検証・認可

## 開発コマンド
```bash
# ローカル開発
npm run dev              # App Service開発サーバー
func start              # Functions ローカル実行

# デプロイ
azd up                  # 全リソースデプロイ
azd deploy              # アプリケーションのみデプロイ

# テスト
npm test                # ユニットテスト
npm run test:e2e        # E2Eテスト
```

## 重要ファイル
- `azure.yaml`: azd設定
- `infra/`: Bicepテンプレート
- `src/web/`: App Service (Frontend)
- `src/functions/`: Azure Functions (MCP Server)

## RBAC設定
- App Service Managed ID: Functions Appへの最小権限
- Functions App: Azure OpenAIリソースアクセス権

## 技術スタック
- Frontend: 
  - TypeScript
  - React + Azure Identity SDK
- Backend: 
  - Python
  - Azure Functions + MCP Binding Extension
- AI: 
  - Azure OpenAI 
  - モデル：GPT-5
- IaC: Bicep + Azure Developer CLI

## 検証ポイント
✅ Managed ID認証が正常に動作するか
✅ MCP Binding Extensionとの連携
✅ GPT-5との統合
✅ 無料プラン内でのパフォーマンス