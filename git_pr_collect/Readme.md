# Github から PR一覧と 各PRのレビューコメント を収集するツール

## configuration

### 初期設定

- conf/github_access_token を作成
- github_access_token ファイルを作成し、github access token のみを記載
- target_github_repository.conf.model をコピーして target_github_repository.conf を作成

初期ファイル作成コマンド (Readme.md がある階層で要実行)

```shell
touch ./conf/github_access_token
copy ./conf/target_github_repository.conf.model ./conf/target_github_repository.conf
```

## 実行

- target_github_repository.conf に 収集対象のリポジトリとそのオーナーを記載してから実行要
- 収集対象のリポジトリを変更したい場合は、都度 target_github_repository.conf を変更すること

例：リポジトリのURLが `https://github.com/owner-name/repository-name` だった場合、target_github_repository.conf にには以下のように記載

```
[DEFAULT]
REPOSITORY_OWNER_NAME=owner-name
REPOSITORY=repository-name
```

### PR全収集

コマンド

```
collect_github_pr_review_comments.py
```

以下により、フィルタが可能

- PRの作成者でフィルタ
    - conf/pr_author_filter_list.txtにPR作成者のGithubアカウント名を記載（空の場合は全取得）
- PRのレビュアーでフィルタ
    - conf/pr_author_filter_list.txtにPRレビュアーのGithubアカウント名を記載（空の場合は全取得）

### 特定のPRのみ収集

コマンド (PRは複数指定可能)

```
./collect_github_pr.sh --pr <pr番号>
```

command example:

```
./collect_github_pr.sh --pr 111 112 113
```

## 出力

- outフォルダに出力
    - pr_list.csv : PRの一覧
    - <PRのタイトル>.csv : PRのレビューコメント一覧
    - <PRのタイトル>フォルダ : PRの各レビューコメントの詳細内容をmdファイルに出力

## 雑記

reference memo:

- [python docker environment setting](https://zuma-lab.com/posts/docker-python-settings)