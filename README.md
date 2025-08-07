# KEF LSX II ネットワークスピーカー 外部コントロールAPI仕様

## 概要

本文書は、KEF LSX II ネットワークスピーカーを外部プログラムから制御するためのHTTP/JSON API仕様を解説するものです。

*注: スピーカーにはハードウェアを直接制御する低レベルなバイナリTCP API（ポート50001）も存在しますが、本文書で解説するHTTP APIがその全機能をカバーしており、より柔軟な制御が可能であるため、低レベルAPIに関する説明は割愛します。*

### APIエンドポイントリファレンス

| APIエンドポイント | HTTPメソッド | 役割 |
| :--- | :--- | :--- |
| `GET /api/getRows` | `GET` | メニューや曲の**一覧**を取得します。 |
| `GET /api/getData` | `GET` | 単一項目の**詳細情報**や**現在の設定値**を取得します。 |
| `POST /api/setData` | `POST` | 再生や**設定変更**などのアクションを命令します。 |
| `POST /api/event/modifyQueue` | `POST` | サーバーからの**イベント通知を購読**するために使用します。 |
| `GET /api/event/pollQueue` | `GET` | 購読したイベントの**更新情報を受信**します。 |

-----

## Part 1: 機能別API解説

### 1.1 音楽再生とプレイリスト操作

#### **フロー概要**

1.  **閲覧**: `getRows`を再帰的に呼び出し、再生したい曲の情報（`trackRoles`）を見つけます。
2.  **準備**: `setData`で`playlists:pl/clear`を呼び出して現在の再生キューをクリアし、`playlists:pl/addexternalitems`で再生したい曲をキューに追加します。
3.  **再生**: `setData`で`player:player/control`を呼び出し、再生を開始します。

#### **`player:player/control` による再生開始**

再生コマンドには、再生する曲の情報に加え、シャッフルとリピートのオプションを指定できます。

  - **`path`**: `player:player/control`
  - **`role`**: `activate`
  - **`value`の構造**:
    ```json
    {
        "control": "play",
        "index": 0,
        "trackRoles": {
            "type": "audio",
            "path": "airable:https://.../track/[Track_ID]",
            "title": "曲名",
            "subTitle": "アーティスト名",
            "mediaData": {
                "artwork": "http://.../artwork.jpg",
                "duration": 240
            },
            "...": "..."
        },
        "mediaRoles": {
            "type": "container",
            "path": "playlists:pq/getitems",
            "mediaData": {
                "metaData": {
                    "playLogicPath": "playlists:playlogic"
                }
            },
            "title": "PlayQueue tracks"
        },
        "shuffle": false,
        "repeatMode": "Off"
    }
    ```

#### **`settings:/mediaPlayer/playMode` による再生中モード変更**

再生を中断することなく、いつでも再生モードを変更できます。

  - **`path`**: `settings:/mediaPlayer/playMode`
  - **`role`**: `value`
  - **`value`**: 以下のいずれかの値を持つJSONオブジェクトを`setData`で送信します。

| `playerPlayMode`の値 | 説明 |
| :--- | :--- |
| `"normal"` | 通常再生 |
| `"shuffle"` | シャッフル |
| `"repeatOne"` | 1曲リピート |
| `"repeatAll"` | 全曲リピート |
| `"shuffleRepeatAll"`| シャッフル ＋ 全曲リピート |

**リクエストボディ例 (`setData`)**:

```json
{
  "path": "settings:/mediaPlayer/playMode",
  "role": "value",
  "value": {
    "type": "playerPlayMode",
    "playerPlayMode": "shuffleRepeatAll"
  }
}
```

### 1.2 スピーカーの一般設定

`getData`で現在の値を取得し、`setData`で値を変更できます。

**取得**: `GET /api/getData?path={path}&roles=value`
**設定**: `POST /api/setData` with `{"path": "{path}", "role": "value", "value": {"type": "...", "...": ...}}`

| 機能 | `path` | 値の型 (`type`) |
| :--- | :--- | :--- |
| **スピーカー名** | `settings:/deviceName` | `string_` |
| **UI言語** | `settings:/ui/language` | `string_` |
| **Airable言語** | `settings:/airable/language` | `string_` |
| **音量上限の有効化** | `settings:/kef/host/volumeLimit` | `bool_` |
| **最大音量** | `settings:/kef/host/maximumVolume` | `i32_` (0-100) |
| **音量ステップ幅** | `settings:/kef/host/volumeStep` | `i16_` |
| **各入力のデフォルト音量** | `settings:/kef/host/defaultVolume{Source}`\<br\>(Source: Wifi, Analogue, Optical, TV, USB, Bluetooth, Coaxial, Global) | `i32_` |
| **自動スタンバイ** | `settings:/kef/host/standbyMode` | `kefStandbyMode` |
| **自動起動ソース** | `settings:/kef/host/wakeUpSource` | `kefWakeUpSource` |
| **HDMIへ自動切替** | `settings:/kef/host/autoSwitchToHDMI` | `bool_` |
| **天面パネル無効化** | `settings:/kef/host/disableTopPanel` | `bool_` |
| **起動音** | `settings:/kef/host/startupTone` | `bool_` |
| **スタンバイLED無効化** | `settings:/kef/host/disableFrontStandbyLED` | `bool_` |
| **マスター/スレーブ接続** | `settings:/kef/host/cableMode` | `kefCableMode` ("wired"等) |
| **マスターチャンネル** | `settings:/kef/host/masterChannelMode` | `kefMasterChannelMode` ("left" or "right") |
| **USB充電** | `settings:/kef/host/usbCharging` | `bool_` |
| **サブウーファー常時ON** | `settings:/kef/host/subwooferForceOn` | `bool_` |
| **KW1サブウーファー強制ON** | `settings:/kef/host/subwooferForceOnKW1` | `bool_` |
| **アプリ解析無効化** | `settings:/kef/host/disableAppAnalytics` | `bool_` |

### 1.3 DSP/EQ（音質）設定

スピーカーの音質を詳細に調整します。設定項目の一覧は`getRows`で取得し、各項目の値は`getData`/`setData`で個別に操作します。

**設定項目一覧の取得**: `GET /api/getRows?path=kef:dsp/editValue&roles=@all`

**設定可能な項目 (`path`一覧)**:
| 機能 | `path` | 値の型 (`type`) |
| :--- | :--- | :--- |
| **バランス** | `settings:/kef/dsp/v2/balance` | `i32_` |
| **デスクモード ON/OFF** | `settings:/kef/dsp/v2/deskMode` | `bool_` |
| **デスクモード補正値** | `settings:/kef/dsp/v2/deskModeSetting` | `double_` (dB) |
| **壁モード ON/OFF** | `settings:/kef/dsp/v2/wallMode` | `bool_` |
| **壁モード補正値** | `settings:/kef/dsp/v2/wallModeSetting` | `double_` (dB) |
| **高音調整** | `settings:/kef/dsp/v2/trebleAmount` | `double_` (dB) |
| **低音拡張** | `settings:/kef/dsp/v2/bassExtension` | `string_` ("standard", "extra", "less") |
| **位相補正** | `settings:/kef/dsp/v2/phaseCorrection` | `bool_` |
| **サブウーファー出力** | `settings:/kef/dsp/v2/subwooferOut` | `bool_` |
| **ハイパス ON/OFF** | `settings:/kef/dsp/v2/highPassMode` | `bool_` |
| **ハイパス周波数** | `settings:/kef/dsp/v2/highPassModeFreq` | `double_` (Hz) |
| **サブウーファーゲイン** | `settings:/kef/dsp/v2/subwooferGain` | `i32_` (dB) |
| **サブウーファー極性** | `settings:/kef/dsp/v2/subwooferPolarity`| `string_` ("normal", "inverted") |
| **サブウーファーLP周波数**| `settings:/kef/dsp/v2/subOutLPFreq` | `double_` (Hz) |
| **サブウーファー数** | `settings:/kef/dsp/v2/subwooferCount` | `i32_` (0, 1, or 2) |
| **サブウーファープリセット**| `settings:/kef/dsp/v2/subwooferPreset` | `string_` |
| **KW1接続** | `settings:/kef/dsp/v2/isKW1` | `bool_` |
| **音声極性** | `settings:/kef/dsp/v2/audioPolarity` | `string_` ("normal", "inverted") |
| **ダイアログモード** | `settings:/kef/dsp/v2/dialogueMode` | `bool_` |

### 1.4 プレイヤーとシステム情報の取得

主に`getData`を使用し、再生中の状態やシステム情報を取得します。

| 機能 | `path` | API | 説明 |
| :--- | :--- | :--- | :--- |
| **現在再生中の情報** | `player:player/data` | `getData` | 曲、状態、制御オプションなどを含む詳細なJSONを返す |
| **再生時間** | `player:player/data/playTime`| `getData` | 現在の再生時間（ミリ秒）を返す |
| **現在の音量** | `player:volume` | `getData` | 現在の音量を返す (0-100の整数) |
| **現在のミュート状態**|`settings:/mediaPlayer/mute`|`getData`|ミュート状態を返す (`bool_`)|
| **MACアドレス**| `settings:/system/primaryMacAddress` | `getData` | プライマリMACアドレスを取得 |
| **ファームウェアバージョン**| `settings:/version` | `getData` | ファームウェアのバージョン文字列を取得 |
| **リリース情報** | `settings:/releasetext` | `getData` | リリース情報を取得 |
| **モデル名** | `settings:/kef/host/modelName`| `getData` | スピーカーのモデル名を取得 |
| **シリアル番号** | `settings:/kef/host/serialNumber`| `getData` | シリアル番号を取得 |
| **電源状態** | `settings:/kef/host/speakerStatus`| `getData` | 電源状態を取得 |
| **アラーム/タイマー** | `alerts:/list` | `getData` | 設定されているアラームやタイマーの一覧を取得 |
| **FW更新情報**| `kef:fwupgrade/info` | `getData` | ファームウェア更新の状態や進捗を取得 |
| **現在の入力ソース** | `settings:/kef/play/physicalSource` | `getData` | 現在の物理入力ソースを取得 |

### 1.5 イベント通知

アプリは`event` APIを利用して、スピーカーの状態変化をリアルタイムに受け取ることができます。

**フロー**:

1.  `POST /api/event/modifyQueue` を呼び出し、監視したい`path`を購読(`subscribe`)します。
2.  `GET /api/event/pollQueue?queueId={ID}` をロングポーリングで呼び出し続けます。
3.  スピーカー側で状態変化（例：音量変更）が起きると、`pollQueue`への応答として更新情報が返されます。
4.  アプリは応答を受け取ったら、すぐに次の`pollQueue`リクエストを送信します。

**`modifyQueue`リクエストボディ例**:

```json
{
  "subscribe": [
    {"path": "player:player/data", "type": "item"},
    {"path": "player:volume", "type": "itemWithValue"},
    {"path": "settings:/mediaPlayer/playMode", "type": "itemWithValue"},
    {"path": "playlists:pq/getitems", "type": "rows"}
  ],
  "unsubscribe": []
}
```

**`pollQueue`レスポンスボディ例**:

```json
[
  {
    "itemType": "update",
    "path": "player:volume",
    "itemValue": {"type": "i32_", "i32_": 35}
  }
]
```
