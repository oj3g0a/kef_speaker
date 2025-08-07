import requests
import json
import sys

# --- 設定項目 ---
# スピーカーのIPアドレスをここに設定してください
SPEAKER_IP = "192.168.0.XXXX"
# 再生したいプレイリストのパスを設定してください
PLAYLIST_PATH = "airable:https://8448239770.airable.io/amazon/playlist/XXXXXXXXX"

# --- スクリプト本体 ---

BASE_URL = f"http://{SPEAKER_IP}"

def print_api_call(method, path, request_data, response_data):
    """APIコールの情報を分かりやすく表示するヘルパー関数"""
    print(f"\n>> {method} {path}")
    if method == "GET":
        print(f"   Request Params: {json.dumps(request_data, indent=2, ensure_ascii=False)}")
    else: # POST
        print(f"   Request Body: {json.dumps(request_data, indent=2, ensure_ascii=False)}")
    
    response_str = json.dumps(response_data, indent=2, ensure_ascii=False) if response_data else "（空の応答）"
    print(f"   Response Body: {response_str}")

def get_rows(path, start=0, count=30):
    """【ステップ1の一部】GET /api/getRows を呼び出し、一覧（要約情報）を取得"""
    api_path = "/api/getRows"
    params = {"path": path, "roles": "@all", "from": start, "to": start + count - 1}
    response = requests.get(f"{BASE_URL}{api_path}", params=params, timeout=10)
    response.raise_for_status()
    data = response.json()
    print_api_call("GET", api_path, params, data)
    return data.get("rows", [])

def get_data(path):
    """【ステップ2の一部】GET /api/getData を呼び出し、詳細（完全な情報）を取得"""
    api_path = "/api/getData"
    params = {"path": path, "roles": "@all"}
    response = requests.get(f"{BASE_URL}{api_path}", params=params, timeout=10)
    response.raise_for_status()
    data = response.json()
    print_api_call("GET", api_path, params, data)
    return data

def set_data(payload):
    """【ステップ3/4の一部】POST /api/setData を呼び出す汎用関数"""
    api_path = "/api/setData"
    response = requests.post(f"{BASE_URL}{api_path}", json=payload, timeout=10)
    response.raise_for_status()
    response_data = None
    if response.text:
        try:
            response_data = response.json()
        except json.JSONDecodeError:
            response_data = response.text # JSONでない場合も考慮
    print_api_call("POST", api_path, payload, response_data)
    return response_data

def add_to_queue(track_summary_info):
    """【ステップ3】setData でキューに曲を追加"""
    # API仕様通り、要約情報をJSON「文字列」に変換
    nsdk_roles_str = json.dumps(track_summary_info, separators=(',', ':'))
    payload = {
        "path": "playlists:pl/addexternalitems",
        "role": "activate",
        "value": { "items": [{"nsdkRoles": nsdk_roles_str}] }
    }
    set_data(payload)

def play_track(track_complete_info):
    """【ステップ4】setData で再生を命令"""
    payload = {
        "path": "player:player/control",
        "role": "activate",
        "value": {
            "control": "play",
            "index": 0,
            "trackRoles": track_complete_info,
            "mediaRoles": {
                "type": "container",
                "path": "playlists:pq/getitems",
                "mediaData": {"metaData": {"playLogicPath": "playlists:playlogic"}},
                "title": "PlayQueue tracks"
            },
            "shuffle": False,
            "repeatMode": "Off"
        }
    }
    set_data(payload)

def main():
    """メインの再生処理フロー"""
    try:
        # --- ステップ1: プレイリストから曲の「要約情報」を取得 ---
        print("▶️ ステップ1: プレイリスト内の曲一覧（要約情報）を取得します...")
        playlist_rows = get_rows(PLAYLIST_PATH)
        if not playlist_rows:
            print("❌ エラー: プレイリストから曲を取得できませんでした。パスが正しいか確認してください。")
            return

        # --- ステップ2: 再生可能な曲を探し、「完全な情報」を取得 ---
        print("\n▶️ ステップ2: 再生可能な最初の曲を探し、その詳細（完全な情報）を取得します...")
        first_track_summary = None
        first_track_complete_info = None

        for track_summary in playlist_rows:
            track_path = track_summary.get("path")
            if not track_path:
                continue

            print(f"\n  - トラック '{track_summary.get('title', 'N/A')}' を検証中...")
            data_response = get_data(track_path)
            
            # APIの応答がリストか辞書か分からないため両対応
            track_complete = data_response[0] if isinstance(data_response, list) and data_response else data_response

            if isinstance(track_complete, dict) and track_complete.get("mediaData", {}).get("resources"):
                print(f"  ✅ 再生可能なトラックを発見: {track_complete.get('title')}")
                first_track_summary = track_summary
                first_track_complete_info = track_complete
                break # 最初の再生可能な曲が見つかったらループを抜ける
            else:
                print("  ⚠️ このトラックは再生に必要な情報を持たないため、スキップします。")

        if not first_track_summary or not first_track_complete_info:
            print("\n❌ エラー: プレイリスト内に再生可能な曲が見つかりませんでした。")
            return

        # --- ステップ3: 再生キューに曲を追加 ---
        print("\n▶️ ステップ3: 再生キューに曲を追加します...")
        add_to_queue(first_track_summary)

        # --- ステップ4: 再生を命令 ---
        print("\n▶️ ステップ4: スピーカーに再生を開始するよう命令します...")
        play_track(first_track_complete_info)

        print("\n🎉 スピーカーに再生リクエストを送信しました！")

    except requests.exceptions.ConnectionError:
        print(f"\n❌ ネットワークエラー: スピーカー({SPEAKER_IP})に接続できませんでした。")
        print("   - IPアドレスが正しいか確認してください。")
        print("   - スピーカーの電源が入っていて、ネットワークに接続されているか確認してください。")
    except requests.exceptions.HTTPError as e:
        print(f"\n❌ APIエラー: スピーカーがリクエストの処理に失敗しました (HTTP {e.response.status_code})。")
        print(f"   応答: {e.response.text}")
    except Exception as e:
        print(f"\n❌ 予期せぬエラーが発生しました: {e}")

if __name__ == "__main__":
    main()
