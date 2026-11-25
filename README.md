# Report to Qase

Qase のレポーターが report モード（`QASE_MODE=report`）で書いたテスト結果のファイルを、Qase の CLI
[`qasectl`](https://github.com/qase-tms/qasectl) で Qase に送る composite action です。
テストのランを作り、結果を送り、ランを完了にします。

> 設計判断や内部の処理は [AGENTS.md](./AGENTS.md) を参照してください。

## 前提

- テストの実行中は、Qase のレポーターを `QASE_MODE=report` で動かし、結果を Qase の形式（JSON）のファイルに書いておくこと。
  テストの実行中は Qase に接続しません。
  - PHPUnit: [`qase/phpunit-reporter`](https://github.com/qase-tms/qase-phpunit)（書き出し先は `QASE_REPORT_CONNECTION_PATH`、既定値 `./build/qase-report`）
  - Playwright: [`playwright-qase-reporter`](https://github.com/qase-tms/qase-javascript/tree/main/qase-playwright)（同上）
- 結果のファイルを別のジョブで書いた場合は、この action の前に `actions/download-artifact` などで取ってくること。
  この action は成果物を取ってきません。
- `python3` と `curl` がある runner（GitHub ホストの Linux / macOS runner）。

## inputs

| input             | required | default   | 説明                                                                                   |
|-------------------|----------|-----------|--------------------------------------------------------------------------------------|
| `results-path`    | yes      | —         | 結果の JSON ファイルがあるディレクトリ（例: `build/qase-report/results`）                              |
| `project`         | yes      | —         | Qase のプロジェクトコード（例: `TFTC`）                                                          |
| `api-token`       | yes      | —         | Qase の API トークン。Secret から渡す                                                         |
| `title`           | yes      | —         | 作るランの名前                                                                              |
| `description`     | no       | `''`      | ランの説明（例: GitHub Actions の実行の URL）                                                    |
| `environment`     | no       | `''`      | ランに付ける Qase の環境のスラッグ。空なら付けない                                                      |
| `time-unit`       | no       | `seconds` | 結果のファイルの `execution.start_time` / `end_time` の単位。`seconds`（Qase の PHP・JavaScript のレポーター）か `milliseconds` |
| `qasectl-version` | no       | `v0.7.0`  | 使う qasectl のリリースのタグ                                                                 |

## outputs

| output    | 説明                                         |
|-----------|--------------------------------------------|
| `run-id`  | 作ったランの ID。結果のファイルが無いときは空                    |
| `run-url` | 作ったランの Qase の URL。結果のファイルが無いときは空             |

結果のファイルが 1 件も無いときは、ランを作らずに終わります（エラーにしません）。

## 使い方

送信に失敗してもワークフローを失敗にしたくない場合は、呼び出す手順に `continue-on-error: true` を付けます。
トークンはこの手順にだけ渡し、テストを実行する手順には渡しません。

### 同じジョブで書いた結果を送る（Playwright）

```yaml
jobs:
  test:
    runs-on: ubuntu-latest
    env:
      QASE_MODE: report
      QASE_REPORT_CONNECTION_PATH: ${{ github.workspace }}/build/qase-report
    steps:
      - uses: actions/checkout@v6
      - run: npx playwright test
      - uses: lepusinc/gha-report-qase@v1
        if: ${{ !cancelled() }}
        continue-on-error: true
        with:
          results-path: build/qase-report/results
          project: TFTC
          api-token: ${{ secrets.QASE_TESTOPS_API_TOKEN }}
          title: "CI E2E #${{ github.run_number }}"
          description: ${{ github.server_url }}/${{ github.repository }}/actions/runs/${{ github.run_id }}
          environment: staging
```

### 別のジョブで書いた結果を送る（PHPUnit）

```yaml
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v6
      - run: vendor/bin/phpunit
        env:
          QASE_MODE: report
          QASE_REPORT_CONNECTION_PATH: /tmp/qase-report
      - uses: actions/upload-artifact@v7
        if: always()
        with:
          name: qase-report
          path: /tmp/qase-report

  report:
    runs-on: ubuntu-latest
    needs: [test]
    if: ${{ !cancelled() }}
    steps:
      - uses: actions/download-artifact@v8
        with:
          name: qase-report
          path: ${{ runner.temp }}/qase-report
      - uses: lepusinc/gha-report-qase@v1
        continue-on-error: true
        with:
          results-path: ${{ runner.temp }}/qase-report/results
          project: TFTC
          api-token: ${{ secrets.QASE_TESTOPS_API_TOKEN }}
          title: "CI Feature - ${{ github.ref_name }} #${{ github.run_number }}"
          description: ${{ github.server_url }}/${{ github.repository }}/actions/runs/${{ github.run_id }}
```

## リリース

`vX.Y.Z` のタグを push すると、`update-major-tag.yml` がメジャーのタグ（`v1` など）を付け替えます。
