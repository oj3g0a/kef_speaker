import requests
import time
from typing import Union

# --- 設定 -----------------------------------------------------------------

# スピーカーのIPアドレス
SPEAKER_IP = "192.168.0.XX"

# 探索を開始する起点となるパス
# (例: Amazon Musicのルート)
ROOT_SEARCH_PATH = "airable:https://8448239770.airable.io/amazon"

# --------------------------------------------------------------------------

BASE_URL = f"http://{SPEAKER_IP}/api"

def get_rows(path: str) -> Union[list, None]:
    """getRows APIを呼び出すヘルパー関数"""
    url = f"{BASE_URL}/getRows"
    params = {'path': path, 'roles': '@all', 'from': 0, 'to': 49} # フォルダ内の最初の50件を取得
    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        return response.json().get("rows", [])
    except requests.exceptions.RequestException:
        return None

def explore_all_recursive(path: str, title: str, indent: str = ""):
    """
    指定されたパスから再帰的に全てのフォルダと曲を探索し、表示する
    """
    # 現在地の情報を表示
    print(f"{indent}📂 探索中: {title} ({path})")
    
    # スピーカーへの負荷を軽減
    time.sleep(1)

    rows = get_rows(path)
    if not rows:
        print(f"{indent}  -> この中には項目がありません。")
        return

    # 現在の階層の項目を全て表示
    for item in rows:
        item_type = item.get("type", "N/A").upper()
        item_title = item.get("title", "タイトルなし")
        item_path = item.get("path", "パスなし")
        
        if item_type == "CONTAINER":
            # フォルダの場合はアイコンを変えて表示
            print(f"{indent}  📁 {item_type:<10} | {item_title:<30} | Path: {item_path}")
        else:
            # 曲やアクションの場合はアイコンを変えて表示
            print(f"{indent}  🎵 {item_type:<10} | {item_title:<30} | Path: {item_path}")

    # 次に、この階層にあったフォルダの中を再帰的に探索
    print(f"{indent}--------------------------------------------------")
    for item in rows:
        if item.get("type") == "container" and "path" in item:
            # 無限ループを避けるため、同じパスは再探索しない
            if item["path"] != path:
                # 再帰呼び出し（インデントを深くする）
                explore_all_recursive(item["path"], item.get("title", "不明なフォルダ"), indent + "  ")

def main():
    """メインの実行処理"""
    print(f"--- 📜 スピーカー ({SPEAKER_IP}) の探索を開始します ---")
    print(f"--- 起点: {ROOT_SEARCH_PATH} ---")
    
    # 最初の探索を開始
    explore_all_recursive(ROOT_SEARCH_PATH, "ルート")
    
    print("\n" + "="*50)
    print("✅ 全ての探索が完了しました。")
    print("="*50)

if __name__ == "__main__":
    main()
