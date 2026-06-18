# TPDP2026 文献調査

TPDP2026で委員会がピックアップした29件の論文・発表について、個別調査を進めるためのリポジトリです。

## 構成

- `docs/`: 調査対象リスト、未確認チェックなどの管理資料
- `papers/`: 個別調査結果のMarkdown原本
- `site/`: GitHub Pagesで公開するHTML

## 運用

1. 個別Issueで文献・コード・実験可否を調査する。
2. 調査結果を `papers/` 配下のMarkdownにまとめる。
3. HTMLを `site/` に生成し、GitHub Pagesへデプロイする。
4. 整理表では、個別調査結果へのURLを「詳細調査結果」欄に記載する。

## Pages同期

公開ページの整理表は、Issue #30「文献管理」の表をマスターとして生成します。

- `main` へのpush時に GitHub Actions がIssue #30を読み取り、`site/index.html` の表を同期してからPagesへデプロイします。
- Issue #30が編集された時も同じActionsが走り、公開ページへ反映します。
- ローカルで同期する場合は、`GH_TOKEN` を設定して `python scripts/sync_issue30_table.py --issue 30` を実行します。
