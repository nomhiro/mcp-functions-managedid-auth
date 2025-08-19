# VS Code デバッグ設定ガイド

## F5キーでAzure Functionsをデバッグ実行する方法

### 前提条件

1. **VS Code拡張機能インストール**
   - Azure Functions
   - Python
   - Python Debugger

2. **Python仮想環境準備**
   ```bash
   cd src/functions
   python -m venv .venv
   .venv\Scripts\activate  # Windows
   pip install -r requirements.txt
   ```

3. **Azure Functions Core Toolsインストール**
   ```bash
   npm install -g azure-functions-core-tools@4 --unsafe-perm true
   ```

### デバッグ実行手順

#### 方法1: F5キーで直接実行（推奨）

1. VS Codeで `src/functions` フォルダを開く
2. F5キーを押下
3. 「Azure Functions (Python)」を選択
4. デバッガー付きでFunctions起動

#### 方法2: タスクを使用して段階実行

1. **Ctrl+Shift+P** → 「Tasks: Run Task」
2. 「func: host start」を選択してFunctions起動
3. F5キー → 「Attach to Python Functions」を選択

### ブレークポイント設定

```python
# function_app.py内でブレークポイント設定例
@app.generic_trigger(
    arg_name="context",
    type="mcpToolTrigger",
    toolName="get_current_time",
    description="Get the current date and time",
    toolProperties=json.dumps({...})
)
def get_current_time(context) -> str:
    # ここにブレークポイントを設定
    args = getattr(context, 'arguments', {}) or {}
    timezone_str = args.get("timezone", "UTC")  # <- ブレークポイント
    # ...
```

### デバッグ用環境変数

`local.settings.json` で環境変数設定:
```json
{
  "Values": {
    "AZURE_FUNCTIONS_ENVIRONMENT": "Development"
  }
}
```

### テスト用cURLコマンド

**ヘルスチェック:**
```bash
curl http://localhost:7071/api/health
```

**認証テスト:**
```bash
curl http://localhost:7071/api/test-auth
```

**チャットテスト:**
```bash
curl -X POST http://localhost:7071/api/test-chat \
  -H "Content-Type: application/json" \
  -d '{"message": "What time is it?"}'
```

### トラブルシューティング

#### 1. Python仮想環境が認識されない
```bash
# VS Codeで仮想環境を明示的に選択
Ctrl+Shift+P → "Python: Select Interpreter"
→ "./.venv/Scripts/python.exe" を選択
```

#### 2. func.exeが見つからない
```bash
# グローバルにfuncをインストール
npm install -g azure-functions-core-tools@4 --unsafe-perm true

# またはローカルパス確認
where func  # Windows
which func  # Mac/Linux
```

#### 3. ポート競合エラー
- `launch.json` の `port: 5678` を変更（例: 5679）
- `tasks.json` の `--python-debug` ポートも同様に変更

#### 4. モジュールインポートエラー
```bash
# 依存関係再インストール
.venv\Scripts\activate
pip install --upgrade pip
pip install -r requirements.txt
```

### デバッグ実行中の動作確認

1. **VS Code TERMINAL**でFunctionsログ確認
2. **DEBUG CONSOLE**でPython変数確認
3. **ブラウザ**で `http://localhost:3000` (フロントエンド)

### 設定ファイル詳細

#### `.vscode/launch.json`
- F5で実行される設定
- 環境変数、ポート設定

#### `.vscode/tasks.json`
- バックグラウンドタスク定義
- 仮想環境作成、依存関係インストール

#### `.vscode/settings.json`
- VS Code固有設定
- Python interpreter path
- Azure Functions設定

### 本番環境との違い

| 項目 | 開発環境 | 本番環境 |
|------|----------|----------|
| 認証 | スキップ | Managed ID |
| デバッグ | 有効 | 無効 |
| ログレベル | DEBUG | INFO |
| 環境変数 | Development | Production |

これでF5キーでデバッグ実行可能です！