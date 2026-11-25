# gha-report-qase 設計メモ

この composite action の設計判断と内部の処理をまとめる。利用者向けの使い方は [README.md](./README.md) を参照。

## 設計判断

### テストの実行と Qase への送信を分ける

Qase のレポーターには、テストの実行中に直接送るモード（`QASE_MODE=testops`）もあるが、使わない。理由は以下:

- API トークンがテストのプロセスに入る（テストのコードや依存パッケージから読める）
- Qase の障害や遅延が、テストの実行時間や結果に響く
- 送信だけをやり直せない。送った内容が手元に残らない
- futokuho-cloud（PHPUnit・paratest）で直接送ったところ、結果が実際のテスト数より 95 件多く記録された。
  report モード + qasectl では一致した（2026-11-25、FTC-4054）

そのため、テストの実行中はレポーターを `QASE_MODE=report` にしてファイルに書くだけにし、この action で送る。

### 成果物は取ってこない

結果のファイルの用意（同じジョブで書く・`download-artifact` で取ってくる）は呼び出し側の責務にする。
この action は「このディレクトリの結果を送る」だけにし、どちらの使い方にも対応できるようにする。

### 失敗の扱いは呼び出し側が決める

送信に失敗したときにワークフローを失敗にするかは、呼び出し側が `continue-on-error` で決める。
結果のファイルが 1 件も無いときは、空のランを作らずに正常終了する。

## 時刻の単位の変換

Qase の PHP（qase-php-commons 2.1）と JavaScript（qase-javascript-commons 2.9）のレポーターは、
`execution.start_time` / `end_time` を秒で書く。一方、qasectl（v0.7.0）は、両方の時刻があるとミリ秒とみなして、
その差で `duration` を計算し直す（`internal/parsers/qase/qase.go` の `calculateDuration`）。
そのままでは 1 秒未満の実行時間が 0 になり、ランの合計時間も合わないため、`time-unit: seconds`（既定値）のときは
送る前に `scripts/convert-times.py` で 1000 倍する。

## ランの作成

`qasectl testops run create` でランを作り（`--environment` を付けられるため）、`result upload --id` で送り、
`run complete` で完了にする。ランの開始・終了の時刻は、テストを実行した時刻ではなく、この action で送った時刻になる。

Qase は送った結果を非同期に取り込むため、送った直後はランの結果が 0 件に見えることがある（1 分ほどで反映される）。

## qasectl の取得

`qasectl-version` で指定したタグの公式のリリース（`github.com/qase-tms/qasectl/releases`）からバイナリを取得する。
バージョンを固定し、上げるときは動作を確認してから既定値を変える。

## テスト

- `tests/test_convert_times.py`: 時刻の変換（`python3 -m unittest discover -s tests`）
- `.github/workflows/test.yml`: 上記の単体テストと、結果のファイルが無いときにランを作らないこと。
  Qase への送信そのものは、トークンが要るため、使う側のリポジトリで確かめる
