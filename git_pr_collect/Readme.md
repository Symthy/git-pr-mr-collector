# Github から PR一覧と 各PRのレビューコメント を収集するツール

## configuration

### 初期設定

- conf/token を作成
- tokenファイルに github access token を記載
- target_repository.conf.model をコピーして target_repository.conf を作成
- target_repository.conf に 収集対象のリポジトリとそのオーナーを記載

### フィルタ機能

- PRの作成者でフィルタ
    - pr_author_filter_list.txtに取得したいPRのPR作成者を記載（空の場合は全取得）
- PRのレビュ―アでフィルタ
    - pr_author_filter_list.txtに取得したいPRレビューコメントのPRレビューアを記載（空の場合は全取得）

## output

- outフォルダに出力
    - pr_list.csv : PRの一覧
    - <PRのタイトル>.csv : PRのレビューコメント一覧
    - <PRのタイトル>フォルダ : PRの各レビューコメントの詳細内容をmdファイルに出力