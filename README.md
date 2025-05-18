# Discord通知ボット

Discordサーバーで定期的な通知を設定・管理するためのボットです。日時を指定して、自動的にメッセージを送信することができます。

## 機能

- **複数の通知タイプ**:
  - 毎日の通知
  - 毎週特定の曜日の通知
  - 毎月特定の日の通知
  - 毎月特定の週と曜日の通知（例：毎月第2月曜日）
  - 一度だけの通知

- **カスタマイズ可能な通知**:
  - タイトルとメッセージ内容のカスタマイズ
  - ロールメンション機能
  - 画像の添付

- **通知管理**:
  - 設定済み通知の一覧表示
  - 通知の削除
  - 通知チャンネルの変更

- **Web UI**:
  - ブラウザからの通知管理
  - サーバー固有のURLによるセキュアなアクセス
  - 通知の追加、編集、削除

## インストール方法

1. リポジトリをクローンする:
```
git clone https://github.com/yourusername/discord-at-code-reminder.git
cd discord-at-code-reminder
```

2. 必要なパッケージをインストールする:
```
pip install -r requirements.txt
```

3. `.env`ファイルを作成し、Discordボットトークンを設定する:
```
TOKEN=your_discord_bot_token_here
```

4. ボットを起動する:
```
python discord-bot.py
```

## 必要なライブラリ

- discord.py
- python-dotenv
- SQLAlchemy
- pytz

## 使い方

### 初期設定

ボットをサーバーに招待した後、最初に初期設定コマンドを実行してください:

```
/setup
```

### 通知の設定

#### 毎日の通知

```
/day-time time:06:00:00 title:朝の挨拶 message:おはようございます！
```

#### 毎週の通知

```
/week-time week:月 time:09:00:00 title:週次ミーティング message:週次ミーティングの時間です
```

#### 毎月の通知

特定の日に通知:
```
/month-time day:1 time:12:00:00 title:月初め message:新しい月の始まりです
```

特定の週と曜日に通知（例：毎月第2月曜日）:
```
/month-time day:2 week:月 time:15:00:00 title:定例会議 message:月次定例会議の時間です
```

#### 一度だけの通知

```
/one-time day:12/25 time:00:00:00 title:クリスマス message:メリークリスマス！
```

### 通知の管理

#### 設定済み通知の一覧表示

```
/get-settings
```

特定の通知の詳細を表示:
```
/get-settings setting_id:1
```

#### 通知の削除

```
/del-settings setting_id:1
```

#### 通知チャンネルの変更

```
/channel-settings setting_id:1 channel:#新しいチャンネル
```

## データベース構造

このボットはSQLAlchemyを使用してSQLiteデータベースに通知設定を保存します。各サーバー（ギルド）ごとに独自のテーブルが作成されます。

テーブル構造:
- `id`: 通知のID（主キー）
- `channel_id`: 通知を送信するチャンネルID
- `option`: 通知タイプ（day, week, month, oneday）
- `day`: 日付設定
- `week`: 曜日設定
- `call_time`: 通知時間
- `mention_ids`: メンションするロールID
- `title`: 通知タイトル
- `main_text`: 通知メッセージ
- `img`: 画像URL

## Web UI の設定と使用方法

### Web UI のセットアップ

1. Discord Developer Portal で OAuth2 設定を行う:
   - [Discord Developer Portal](https://discord.com/developers/applications) にアクセスします
   - アプリケーションを選択（または新規作成）します
   - 「OAuth2」→「General」タブで以下を設定します:
     - Redirects: `http://localhost:5000/callback` を追加
     - Client ID と Client Secret をメモします

2. `.env` ファイルに Web UI の設定を追加:
   ```
   # Web UI設定
   DISCORD_CLIENT_ID="Developer Portalで取得したClient ID"
   DISCORD_CLIENT_SECRET="Developer Portalで取得したClient Secret"
   DISCORD_REDIRECT_URI="http://localhost:5000/callback"
   WEB_SERVER_URL="http://localhost:5000"
   FLASK_SECRET_KEY="ランダムな文字列"
   ```
   FLASK_SECRET_KEY には任意のランダムな文字列を設定してください。

3. Web サーバーを起動:
   ```
   python web_server.py
   ```

4. Discord ボットを起動:
   ```
   python discord-bot.py
   ```

### Web UI の使用方法

1. Discord サーバーで `/web-ui` コマンドを実行して、Web UI の URL を取得します。
   - URL は DM で送信されます（DM が無効な場合はチャンネルに表示されます）
   - この URL はサーバー固有で、他のサーバーのユーザーはアクセスできません

2. ブラウザで URL にアクセスして、通知を管理します:
   - 通知の一覧表示
   - 新しい通知の追加
   - 既存の通知の編集
   - 通知の削除

3. Web UI では以下の操作が可能です:
   - 毎日、毎週、毎月、一回限りの通知の設定
   - 通知のタイトルとメッセージの編集
   - 通知を送信するチャンネルの変更
   - メンションするロールの設定
   - 画像 URL の設定

## トラブルシューティング

### 通知が送信されない場合

1. ボットが正しく起動しているか確認してください
2. ボットが通知を送信するチャンネルに対する権限を持っているか確認してください
3. 通知設定が正しいか `/get-settings` コマンドで確認してください
4. 時間設定が正しいフォーマット（HH:MM:SS）で設定されているか確認してください

### Web UI にアクセスできない場合

1. `.env` ファイルの設定が正しいか確認してください
2. Discord Developer Portal の OAuth2 設定が正しいか確認してください
3. Web サーバーが起動しているか確認してください
4. `/web-ui` コマンドで取得した URL が正しいか確認してください

### エラーメッセージ「セットアップコマンドを実行してください」

サーバーで `/setup` コマンドを実行して初期設定を完了してください。

### その他のエラー

エラーが発生した場合は、コンソールログを確認して問題を特定してください。一般的なエラーは以下の通りです:

- データベース接続エラー: データベースファイルへのアクセス権限を確認してください
- 不正な日付/時間フォーマット: 正しいフォーマットで日付と時間を入力してください
- OAuth エラー: Discord Developer Portal の設定を確認してください

## ライセンス

このプロジェクトはMITライセンスの下で公開されています。詳細については[LICENSE](LICENSE)ファイルを参照してください。
