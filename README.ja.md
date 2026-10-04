# tern-jj

[English](README.md) | 日本語

Tern に Jujutsu サポートを追加するための Luau プラグイン開発環境。
現時点では `jj status` / `jj st` の出力をネイティブカードで表示します。
Jujutsu の操作や既存の Git UI の置き換えは行いません。

## 前提

- macOS、デスクトップセッション、利用可能な Tern アカウント
- `/Applications/Tern.app` にインストールした Tern
- `mise`、`jj`、Python 3（スモークチェック用）

確認済みの組み合わせ: Tern 0.4.1、jj 0.45.1、luau-lsp 1.70.1。
Tern の場所が異なる場合は `TERN=/path/to/tern mise run dev` のように指定します。

## 開始

```sh
mise trust
mise install github:JohnnyMorganz/luau-lsp@1.70.1
mise run setup
mise run check
mise run dev
```

Luau は Tern が直接実行するため、コンパイルやバンドルは不要です。
`check` が静的型検査、`dev` が実際の Tern 起動に相当します。
開いたペインで `jj status` を実行すると「Jujutsu status」カードが表示されます。
カード内では追加を緑、変更・リネームを黄、削除を赤で表示します。
change ID はアクセント色、commit ID は情報色、変更なしのメッセージは緑になります。
色は Tern のテーマに従い、認識できない行は元の文字列のまま表示します。
エラー・空の出力・5,000 行を超える出力は Raw 表示を維持します。
引数付きの status、`jj log`、`jj diff` などはレンズで取得せず通常の出力になります。

## 編集と確認

- `plugins/jj/host.luau`: ホスト側のレンズ実装。保存すると自動再読み込み。
- `plugins/jj/plugin.toml`: エントリーと取得するコマンドを宣言。
- `mise run reload`: 開発デーモンを手動再読み込み。`dev` の起動が必要。
- `mise run smoke`: 一時的な jj リポジトリと独立した Tern ウィンドウで、
  変更なし・追加／変更／削除／リネームの文字色・change/commit ID の文字色・リポジトリ外のエラー表示を確認。
  テスト用ウィンドウとデーモンは終了時に停止。
- スクリーンショット: `.dev/shots/live/jj-status.png`
- 表示要素の記録: `.dev/status-tree.json`
- 通常の開発ログ: `.dev/logs/`
- スモークチェックのログ: `.dev/smoke-process.log`、`.dev/smoke-logs/`

VS Code は推奨の **Luau Language Server** 拡張をインストールしてください。
`.vscode/settings.json` は Roblox 環境を無効にし、Tern の型定義を読み込みます。
`mise run types` でインストール済み Tern から `tern.d.luau` を再生成します。
この生成物は追跡しません。Tern 更新後も再生成してください。
`types/luau.d.luau` は standard 環境に不足している nominal な `userdata` 基底型を宣言し、
Tern の `extern` 型を型検査できるようにします。`any` による検査の回避は行いません。

## 通常の環境からの分離

開発用の環境変数は `mise` タスク内に限定し、このディレクトリへの移動時には
エクスポートしません。そのため、リポジトリ内で `tern plugin install` を実行しても
通常の Tern が対象になります。既に開いているシェルでは次の mise プロンプトフックで
環境を更新するか、zsh なら `eval "$(mise hook-env -s zsh)"` を実行してください。

タスクは以下を使用します。

- 設定・リンク・プラグインデータ: `.dev/config/`
- セッション用ソケット: `.dev/daemon.sock`
- ウィンドウ制御ソケット: `.dev/control.sock`
- zsh 起動設定: `dev/zsh/`（個人用の rc・alias は読み込まない）

`dev/settings.json` は初回のみ `.dev/config/settings.json` にコピーします。
既存の開発設定は上書きしません。自動アップデートは開発プロファイルでは無効です。
プラグイン本体だけをリンクするため、SDK、ログ、`.jj` の更新では再読み込みしません。
`tern-sdk/` は配布 SDK とサンプルとして保持し、変更していません。

開発用 zsh は Tern がキャッシュに配置する公式シェル連携を利用します。
プラグインが新しいシェルの起動時に `JJ_PAGER=cat` を注入し、
対話的ページャーによるレンズ取得の中断を防ぎます。
個人のシェル設定や Jujutsu 設定ファイルは変更しません。

## 本番環境（通常の Tern）へのロード

本番環境では `link` ではなく `install` でコピーを配置します。
開発中のファイル保存が通常の Tern に即座に反映されないためです。
luau-lsp、Python、開発用 zsh 設定は本番での実行には不要です。

### 初回インストール

このリポジトリのルートで実行してください。サブシェル内で継承した設定・
ソケット・ウィンドウ指定（開発用 Tern のペインなど）を解除します。
親シェルの環境変数は変更しません。

```sh
(
  unset TERN_CONFIG_DIR TERN_DAEMON_SOCKET TERN_WINDOW_KEY TERN_WINDOW_SOCKET
  /Applications/Tern.app/Contents/MacOS/tern plugin install "$PWD/plugins/jj" &&
  /Applications/Tern.app/Contents/MacOS/tern plugin list
)
```

macOS の配置先は通常 `~/Library/Application Support/Tern/plugins/jj/` です。
通常のデーモンが起動中ならインストール時に自動再読み込みされます。
`no daemon running; changes apply at next start` と表示された場合は、
通常の Tern を起動してください。この場合の `list` の `ready` は
マニフェストが有効であることだけを示し、Lua の実行確認ではありません。

以前に通常環境へ `link` していた場合は、同じ環境変数を解除したサブシェルで
`tern plugin unlink jj` を実行してからインストールします。
リンク済みのパッケージは `install --force` でも置き換えられません。

### ロードと表示の確認

通常の Tern の Preferences › Plugins で Jujutsu が Ready になっていること、
プラグインと Settings › Terminal › Native command output が有効であることを確認します。
プラグインのロード後にシェル連携が有効な新しいペインを開き、
jj リポジトリへ移動して実行してください。

```sh
jj status
```

「Jujutsu status」カードが表示されれば、ホスト側のロードとレンズの動作を確認できます。
Raw 切り替えで元の出力も確認できます。プラグインは新しいペイン内の全 jj コマンド向けに
`JJ_PAGER=cat` を設定し、継承した値を上書きします。既存ペインは変更されないため、
インストールや再読み込み後は新しいペインを開いてください。
シェル起動設定やコマンド単位の明示的な指定では、注入した値を上書きできます。

### 更新

ソースの編集だけではインストール済みのコピーは更新されません。
型検査・スモークチェック後に明示的に置き換えます。

```sh
(
  unset TERN_CONFIG_DIR TERN_DAEMON_SOCKET TERN_WINDOW_KEY TERN_WINDOW_SOCKET
  /Applications/Tern.app/Contents/MacOS/tern plugin install "$PWD/plugins/jj" --force &&
  /Applications/Tern.app/Contents/MacOS/tern plugin list
)
```

### 無効化・削除

一時的な無効化は Preferences › Plugins で行います。
インストールしたコピーを削除する場合は次を実行します。開発用ソースは残ります。

```sh
(
  unset TERN_CONFIG_DIR TERN_DAEMON_SOCKET TERN_WINDOW_KEY TERN_WINDOW_SOCKET
  /Applications/Tern.app/Contents/MacOS/tern plugin remove jj
)
```

`link` で導入した場合の解除は `remove` ではなく `unlink jj` です。

## 公式仕様

- [Getting Started](https://docs.stencil.so/tern/guides/getting-started.html)
- [Command Lenses](https://docs.stencil.so/tern/guides/lenses.html)
- [Debugging / control endpoint](https://docs.stencil.so/tern/guides/debugging.html)
- [Plugin CLI](https://docs.stencil.so/tern/reference/cli.html)
