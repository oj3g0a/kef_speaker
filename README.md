# KEF LSX II ネットワークスピーカー 外部コントロールAPI仕様

## 概要

本文書は、KEF LSX II ネットワークスピーカーを外部プログラムから制御し、Amazon Musicなどのストリーミングサービスを再生させるためのAPI仕様と手順を解説するものです。

**システムアーキテクチャの要点:**

  * **司令塔 (アプリ)**: ユーザーインターフェースと認証ロジックを担当。
  * **実行役 (スピーカー)**: ローカルAPIを提供し、受け取った命令（再生、音量調整など）を実行する。
  * **仲介役 (Airable Cloud)**: KEFと各音楽配信サービス（Amazon Music等）の間の通信を中継・通訳する。
  * **音源 (Amazon Music Cloud)**: 楽曲データと、再生に必要な一時的な認証情報（トークン）を発行する。

アプリケーションは、スピーカーを「窓口」としてAirable Cloudと通信し、最終的にAmazon Musicのコンテンツを再生します。

-----

## 1\. 認証フロー (OAuth 2.0)

Amazon Musicを再生するには、まず正規のユーザーとして認証し、スピーカー（Airableサービス）がユーザーの代わりにAmazon Musicを操作する許可を得る必要があります。このプロセスはOAuth 2.0に準拠しています。

### 1.1. 準備：ログアウト

認証フローを開始するには、システムがログアウト状態である必要があります。

  - **Endpoint**: `POST http://{SPEAKER_IP}/api/setData`
  - **Body**:
    ```json
    {
        "path": "airable:logout:amazon:https://8448239770.airable.io/amazon/logout",
        "role": "activate",
        "value": {}
    }
    ```

### 1.2. ステップ1：認証開始URLの取得

ログアウト状態でAmazon Musicのトップメニューにアクセスすると、ログインページへのリダイレクト指示が返されます。

**A. トップメニューへアクセス**

```bash
curl "http://{SPEAKER_IP}/api/getRows?path=airable:https%3A%2F%2F8448239770.airable.io%2Famazon&roles=%40all"
```

  * **応答 (抜粋)**: `{"rowsRedirect":"airable:message8","rows":[]}`

**B. リダイレクト先へアクセス**
応答に含まれる`rowsRedirect`のパスを使って、再度`getRows`を実行します。

```bash
curl "http://{SPEAKER_IP}/api/getRows?path=airable%3Amessage8&roles=%40all"
```

  * **応答 (抜粋)**: この応答の中に、認証を開始するための情報が含まれています。
    ```json
    {
        "title": "ログイン",
        "type": "oauth2",
        "value": {
            "type": "oauth2Info",
            "oauth2Info": {
                "browserAuthFlowPath": "airable:oauth?oauthType=browser?url=https://8448239770.airable.io/amazon/oauth\\?code\\=:code:&state\\=[STATE_PARAMETER_STRING]&return\\=:return:",
                "loggedIn": false
            }
        }
    }
    ```

### 1.3. ステップ2：ユーザーによるブラウザ認証

1.  ステップ1で取得した`browserAuthFlowPath`内のURL部分を抜き出します。
    `https://8448239770.airable.io/amazon/oauth?code=:code:&state=[STATE_PARAMETER_STRING]`
2.  このURLをWebブラウザで開き、Amazonアカウントでログイン（2要素認証含む）を完了させます。

### 1.4. ステップ3：認証コードの取得

ログインに成功すると、ブラウザはAirableのサーバーにリダイレクトされ、画面にJSON配列形式で認証コードが表示されます。

  * **リダイレクト先のURL**: `https://8448239770.airable.io/amazon/oauth?code=[取得した認証コード]&scope=...&state=[STATE_PARAMETER_STRING]`
  * **画面に表示される内容**:
    ```json
    ["success", "[取得した認証コード]", "[STATE_PARAMETER_STRING]"]
    ```

この\*\*`[取得した認証コード]`\*\*が、一度しか使えない一時的なものです。

### 1.5. ステップ4：トークン交換の完了

取得した認証コードを、ステップ1で得られた`appAuthFlowPath`に埋め込み、APIを呼び出すことでログインが完了します。このAPI呼び出しにより、スピーカー・Airableサービス側で永続的なリフレッシュトークンが保存されます。

-----

## 2\. 音楽再生フロー

ログインが完了している状態であれば、以下の手順で任意のプレイリストの曲を再生できます。

### 2.1. ステップ1：再生したい曲の「完全な情報」を取得

1.  **プレイリスト一覧の取得**: `getRows`で目的のプレイリストが含まれるメニューにアクセスします。
2.  **曲リストの取得**: 1の応答からプレイリストの`path`を抜き出し、再度`getRows`で曲のリストを取得します。
3.  **曲の単体情報（完全版）の取得**: 2で取得した曲リストから、再生したい曲の`path`を抜き出し、`getData`でその曲単体の完全な情報を取得します。これが再生命令で必要となる`ApiRoles`オブジェクトです。

### 2.2. ステップ2：再生の実行

1.  **キューのクリア（任意）**: 新しい曲を再生する前に、現在の再生キューをクリアします。

      * **Endpoint**: `POST /api/setData`
      * **Body**: `{"path":"playlists:pl/clear", "role":"activate", "value":{"plid":0}}`

2.  **曲のキュー追加**: 2.1で取得した**完全な曲情報**を**一つのJSON文字列に変換**し、`nsdkRoles`の値としてキューに追加します。

      * **Endpoint**: `POST /api/setData`
      * **Body (構造)**:
        ```json
        {
            "path": "playlists:pl/addexternalitems",
            "role": "activate",
            "value": {
                "plid": 0,
                "items": [{
                    "nsdkRoles": "{\"title\":\"曲名\", \"type\":\"audio\", ...}" // 完全な曲情報をJSON文字列化したもの
                }],
                "mode": "2"
            }
        }
        ```

3.  **再生の開始**: 最後に、再生を命令します。この際、再生する曲の情報(`trackRoles`)と、それが属するコンテナの情報(`mediaRoles`)を合わせて送信します。

      * **Endpoint**: `POST /api/setData`
      * **Body (構造)**:
        ```json
        {
            "path": "player:player/control",
            "role": "activate",
            "value": {
                "control": "play",
                "index": 0,
                "startPaused": false,
                "mediaRoles": { "...": "..." }, // プレイリストのコンテキスト情報
                "trackRoles": { "...": "..." }  // 完全な曲情報のJSONオブジェクト
            }
        }
        ```

-----

## Appendix A: Python実装サンプル

上記フローを実装したPythonスクリプトの最終版です。

```python
import requests
import json
import time
import urllib.parse

# --- 設定項目 ---
SPEAKER_IP = "192.168.0.XXX" # あなたのスピーカーのIPアドレス
BASE_URL = f"http://{SPEAKER_IP}/api"
# 起点となるメニューのPath (例: 「人気ランキング」)
# このPathは、再生したいプレイリストに応じてキャプチャし、変更する必要があります。
MENU_PATH = "airable:https%3A%2F%2F8448239770.airable.io%2Famazon%2Fdocument%2FWyJodHRwczpcL1wvbXVzaWMtYXBpLmFtYXpvbi5jb21cL2NhdGFsb2dcL3BvcHVsYXJcLyNjYXRhbG9nX3BvcHVsYXJfZGVzYyJd"

def set_data(payload: dict):
    """スピーカーにPOSTリクエスト(setData)を送信する関数"""
    try:
        response = requests.post(f"{BASE_URL}/setData", json=payload, timeout=10)
        response.raise_for_status()
        print(f"  -> setData成功: {response.text}")
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"  -> setDataエラー: {e}")
        return None

# --- メイン処理 ---
if __name__ == "__main__":
    
    # --- ステップ1: 「人気の楽曲」プレイリストのPathを取得 ---
    print("--- ステップ1: 「人気の楽曲」プレイリストのPathを取得します ---")
    songs_playlist_path = None
    try:
        get_menu_url = f"{BASE_URL}/getRows?path={MENU_PATH}&roles=%40all&from=0&to=20"
        response = requests.get(get_menu_url, timeout=10)
        response.raise_for_status()
        menu_data = response.json()
        
        for item in menu_data.get("rows", []):
            if item.get("title") == "人気の楽曲":
                songs_playlist_path = item.get("path")
                break
        
        if not songs_playlist_path:
            raise ValueError("メニュー内に「人気の楽曲」プレイリストが見つかりませんでした。")
        
        print(f" -> 「人気の楽曲」のPathを発見しました。")

    except (requests.exceptions.RequestException, ValueError) as e:
        print(f"プレイリストPathの取得に失敗しました: {e}")
        exit()

    # --- ステップ2: プレイリストを開き、最初の曲のPathを取得 ---
    print("\n--- ステップ2: 最初の曲のPathを取得します ---")
    first_track_path = None
    try:
        encoded_playlist_path = urllib.parse.quote(songs_playlist_path, safe='/:')
        get_tracks_url = f"{BASE_URL}/getRows?path={encoded_playlist_path}&roles=%40all&from=0&to=5"
        response = requests.get(get_tracks_url, timeout=10)
        response.raise_for_status()
        track_data = response.json()
        tracks = track_data.get("rows", [])

        if not tracks or "path" not in tracks[0]:
            raise ValueError("プレイリストに曲が見つからないか、曲のPathがありません。")
            
        first_track_path = tracks[0].get("path")
        print(f" -> 曲「{tracks[0].get('title')}」のPathを取得しました。")

    except (requests.exceptions.RequestException, ValueError) as e:
        print(f"曲リストの取得に失敗しました: {e}")
        exit()

    # --- ステップ3: 曲のPathを使い、完全な再生情報をgetDataで取得 ---
    print("\n--- ステップ3: 曲の完全な再生情報を取得します ---")
    full_track_info = None
    try:
        encoded_track_path = urllib.parse.quote(first_track_path, safe='/:')
        get_track_info_url = f"{BASE_URL}/getData?path={encoded_track_path}&roles=%40all"
        response = requests.get(get_track_info_url, timeout=10)
        response.raise_for_status()
        full_track_info = response.json()[0] 
        print(f" -> 完全な再生情報を取得しました。")

    except (requests.exceptions.RequestException, IndexError, KeyError) as e:
        print(f"曲の完全な情報の取得に失敗しました: {e}")
        exit()

    # --- ステップ4: キューのクリアと追加 ---
    print("\n--- ステップ4: キューをクリアし、曲を追加します ---")
    set_data({"path": "playlists:pl/clear", "role": "activate", "value": {"plid": 0}})
    time.sleep(1)
    
    nsdk_roles_string = json.dumps(full_track_info)
    add_payload = {
        "path": "playlists:pl/addexternalitems", "role": "activate",
        "value": {"plid": 0, "items": [{"nsdkRoles": nsdk_roles_string}], "mode": "2"}
    }
    set_data(add_payload)
    time.sleep(3)

    # --- ステップ5: 再生を開始 ---
    print("\n--- ステップ5: 再生を開始します ---")
    media_roles = {
        "title": "PlayQueue tracks", "type": "container", "containerType": "none",
        "path": "playlists:pq/getitems",
        "mediaData": {"metaData": {"playLogicPath": "playlists:playlogic"}}
    }
    
    play_payload = {
        "path": "player:player/control", "role": "activate",
        "value": {
            "control": "play", "index": 0, "startPaused": False,
            "mediaRoles": media_roles,
            "trackRoles": full_track_info 
        }
    }
    set_data(play_payload)

    print("\n--- 完了 ---")
```
