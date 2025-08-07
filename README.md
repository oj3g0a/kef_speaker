# KEF LSX II ネットワークスピーカー 外部コントロールAPI仕様

## 概要

本文書は、KEF LSX II ネットワークスピーカーを外部プログラムから制御するためのHTTP/JSON API仕様を網羅的に解説するものです。

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
            "...": "..."
        },
        "mediaRoles": {
            "type": "container",
            "path": "playlists:pq/getitems",
            "mediaData": {
                "metaData": { "playLogicPath": "playlists:playlogic" }
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

### 1.2 スピーカーの各種設定

`getData`で現在の値を取得し、`setData`で値を変更できます。

**取得**: `GET /api/getData?path={path}&roles=value`
**設定**: `POST /api/setData` with `{"path": "{path}", "role": "value", "value": { ... }}`

| 機能 | `path` | `setData`のvalueオブジェクト例 |
| :--- | :--- | :--- |
| **スピーカー名** | `settings:/deviceName` | `{"type":"string_","string_":"新しい名前"}` |
| **UI言語** | `settings:/ui/language` | `{"type":"string_","string_":"ja_JP"}` |
| **Airable言語** | `settings:/airable/language`| `{"type":"string_","string_":"ja_JP"}` |
| **音量上限の有効化** | `settings:/kef/host/volumeLimit` | `{"type":"bool_","bool_":true}` |
| **最大音量** | `settings:/kef/host/maximumVolume`| `{"type":"i32_","i32_":80}` |
| **音量ステップ幅** | `settings:/kef/host/volumeStep`| `{"type":"i16_","i16_":5}` |
| **デフォルト音量(Wifi)** | `settings:/kef/host/defaultVolumeWifi`| `{"type":"i32_","i32_":25}` |
| **デフォルト音量(TV)** | `settings:/kef/host/defaultVolumeTV`| `{"type":"i32_","i32_":30}` |
| **デフォルト音量(Optical)**| `settings:/kef/host/defaultVolumeOptical`| `{"type":"i32_","i32_":30}` |
| **デフォルト音量(USB)** | `settings:/kef/host/defaultVolumeUSB`| `{"type":"i32_","i32_":30}` |
| **デフォルト音量(Coaxial)**| `settings:/kef/host/defaultVolumeCoaxial`| `{"type":"i32_","i32_":30}` |
| **デフォルト音量(Bluetooth)**|`settings:/kef/host/defaultVolumeBluetooth`| `{"type":"i32_","i32_":30}` |
| **デフォルト音量(Analogue)**|`settings:/kef/host/defaultVolumeAnalogue`| `{"type":"i32_","i32_":30}` |
| **自動スタンバイ** | `settings:/kef/host/standbyMode` | `{"type":"kefStandbyMode","kefStandbyMode":"standby_60mins"}` |
| **自動起動ソース** | `settings:/kef/host/wakeUpSource`| `{"type":"kefWakeUpSource","kefWakeUpSource":"tv"}` |
| **HDMIへ自動切替** | `settings:/kef/host/autoSwitchToHDMI`| `{"type":"bool_","bool_":false}` |
| **天面パネル無効化** | `settings:/kef/host/disableTopPanel`| `{"type":"bool_","bool_":true}` |
| **起動音** | `settings:/kef/host/startupTone` | `{"type":"bool_","bool_":true}` |
| **スタンバイLED無効化** |`settings:/kef/host/disableFrontStandbyLED`| `{"type":"bool_","bool_":false}` |
| **マスター/スレーブ接続** | `settings:/kef/host/cableMode` | `{"type":"kefCableMode","kefCableMode":"wired"}` |
| **マスターチャンネル** | `settings:/kef/host/masterChannelMode`| `{"type":"kefMasterChannelMode","kefMasterChannelMode":"left"}`|
| **USB充電** | `settings:/kef/host/usbCharging` | `{"type":"bool_","bool_":true}` |
| **サブウーファー常時ON** | `settings:/kef/host/subwooferForceOn`| `{"type":"bool_","bool_":true}` |
| **KW1サブウーファー強制ON** | `settings:/kef/host/subwooferForceOnKW1`| `{"type":"bool_","bool_":true}` |
| **アプリ解析無効化** | `settings:/kef/host/disableAppAnalytics` | `{"type":"bool_","bool_":true}` |

### 1.3 DSP/EQ（音質）設定

`getRows?path=kef:dsp/editValue`で全項目の一覧を取得後、`getData`と`setData`で個別に操作します。

| 機能 | `path` | `setData`のvalueオブジェクト例 |
| :--- | :--- | :--- |
| **バランス** | `settings:/kef/dsp/v2/balance` | `{"type":"i32_","i32_":-5}` |
| **デスクモード ON/OFF** | `settings:/kef/dsp/v2/deskMode` | `{"type":"bool_","bool_":true}` |
| **デスクモード補正値** | `settings:/kef/dsp/v2/deskModeSetting`| `{"type":"double_","double_":-2.5}` |
| **壁モード ON/OFF** | `settings:/kef/dsp/v2/wallMode` | `{"type":"bool_","bool_":false}` |
| **壁モード補正値** | `settings:/kef/dsp/v2/wallModeSetting`| `{"type":"double_","double_":-6.0}` |
| **高音調整** | `settings:/kef/dsp/v2/trebleAmount` | `{"type":"double_","double_":1.5}` |
| **低音拡張** | `settings:/kef/dsp/v2/bassExtension` | `{"type":"string_","string_":"extra"}` |
| **位相補正** | `settings:/kef/dsp/v2/phaseCorrection`| `{"type":"bool_","bool_":false}` |
| **サブウーファー出力** | `settings:/kef/dsp/v2/subwooferOut` | `{"type":"bool_","bool_":false}` |
| **ハイパス ON/OFF** | `settings:/kef/dsp/v2/highPassMode` | `{"type":"bool_","bool_":true}` |
| **ハイパス周波数** | `settings:/kef/dsp/v2/highPassModeFreq`| `{"type":"double_","double_":80.0}`|
| **サブウーファーゲイン** | `settings:/kef/dsp/v2/subwooferGain`| `{"type":"i32_","i32_":2}` |
| **サブウーファー極性** | `settings:/kef/dsp/v2/subwooferPolarity`|`{"type":"string_","string_":"inverted"}`|
| **サブウーファーLP周波数**| `settings:/kef/dsp/v2/subOutLPFreq` | `{"type":"double_","double_":100.0}`|
| **サブウーファー数** | `settings:/kef/dsp/v2/subwooferCount` | `{"type":"i32_","i32_":1}` |
| **サブウーファープリセット**| `settings:/kef/dsp/v2/subwooferPreset` | `{"type":"string_","string_":"kc62"}`|
| **KW1接続** | `settings:/kef/dsp/v2/isKW1` | `{"type":"bool_","bool_":true}` |
| **音声極性** | `settings:/kef/dsp/v2/audioPolarity` | `{"type":"string_","string_":"inverted"}`|
| **ダイアログモード** | `settings:/kef/dsp/v2/dialogueMode`| `{"type":"bool_","bool_":true}` |

### 1.4 イベント通知システム

スピーカーの状態変化をリアルタイムに受け取るための高度な機能です。

**フロー**:

1.  **購読開始**: アプリ起動時に一度だけ、`POST /api/event/modifyQueue` を呼び出し、監視したい`path`を購読(`subscribe`)します。応答として`queueId`が返されます。
2.  **ポーリング**: `GET /api/event/pollQueue?queueId={ID}&timeout=25` をロングポーリングで呼び出し続けます。`timeout`は秒単位で、この時間内に変化がなければ空の応答が返ります。
3.  **イベント受信**: スピーカー側で状態変化が起きると、`pollQueue`への応答として更新情報が返されます。
4.  **継続**: アプリは応答を受け取ったら、すぐに次の`pollQueue`リクエストを送信して監視を続けます。

**`modifyQueue`リクエストボディ**:

```json
{
  "subscribe": [
    {"path": "player:player/data", "type": "item"},
    {"path": "player:volume", "type": "itemWithValue"},
    {"path": "settings:/mediaPlayer/playMode", "type": "itemWithValue"}
  ]
}
```

**`modifyQueue`レスポンスボディ**:

```json
"{d3474c09-4408-4aff-8bae-c06041a7925b}"
```

**`pollQueue`レスポンスボディ (イベント発生時)**:

```json
[
  {
    "itemType": "update",
    "path": "player:volume",
    "itemValue": {"type": "i32_", "i32_": 35}
  },
  {
    "itemType": "update",
    "path": "settings:/mediaPlayer/playMode",
    "itemValue": {"type": "playerPlayMode", "playerPlayMode": "shuffle"}
  }
]
```

### 1.5 エラーハンドリング

API呼び出しが失敗した場合、HTTPステータスコードと、場合によってはエラーメッセージを含むJSONが返されます。

| ステータスコード | 意味 | 考えられる原因 |
| :--- | :--- | :--- |
| **404 Not Found** | リクエストされた`path`が存在しない。 | `path`のスペルミス。 |
| **500 Internal Server Error**| スピーカー内部で処理エラーが発生した。| - `setData`の`value`オブジェクトの形式が間違っている。\<br\>- 必須のパラメータが不足している。\<br\>- スピーカーが一時的に不安定な状態にある。|

**`500`エラー時のレスポンスボディ例**:

```json
{
  "error": "Internal Server Error",
  "message": "An unexpected error occurred"
}
```

(注: エラーメッセージの内容は状況により異なる場合があります)

-----

このドキュメントが、あなたのアプリケーション開発の確かな土台となることを願っています。
