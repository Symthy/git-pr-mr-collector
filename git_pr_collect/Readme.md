# Github PR Collect Tool

Github の指定 repository から PR一覧と 各PR内のレビューコメント を収集するツールです

- レビューコメントの一覧を csv ファイルで出力
- 個々のレビューコメントの詳細情報を md ファイルで出力（PR毎にフォルダを切って出力）

## Configuration

### Initialize

前提：dockerがインストール済み

以下をコマンド実行し、 conf/github_access_token ファイルに、github access token のみを記載

```
./initialize.sh
```

### Target Repository Setting

- conf/target_github_repository.conf に 収集対象のリポジトリとそのオーナーを記載
- 収集対象のリポジトリを変更したい場合は、都度 target_github_repository.conf を変更すること

設定例：リポジトリのURLが `https://github.com/owner-name/repository-name` だった場合、target_github_repository.conf にには以下のように記載

```
[DEFAULT]
REPOSITORY_OWNER_NAME=owner-name
REPOSITORY=repository-name
```

## Execute

収集方法は以下２通りを提供

### All PR collect

設定ファイルに指定された repository 内の全PRを収集

コマンド

```
./collect_github_pr.sh
```

以下により、フィルタが可能

- PRの作成者でフィルタ
    - conf/pr_author_filter_list.txtにPR作成者のGithubアカウント名を記載（空の場合は全取得）
- PRのレビュアーでフィルタ
    - conf/pr_author_filter_list.txtにPRレビュアーのGithubアカウント名を記載（空の場合は全取得）

### Specified PR collect

指定したPRのみを収集。オプションでrepositoryの指定も可能

コマンド (オプションは順不同)

```
./collect_github_pr.sh --pr[ <pr番号>]... [--repo <repository名>]
```

オプション：

- pr: 収集対象のPR番号を指定（PRは複数指定可能）
- repo: PR取得対象のrepository指定(任意)。指定ない場合は設定ファイルのrepositoryを対象とする

command example:

```
./collect_github_pr.sh --pr 111 112 113
./collect_github_pr.sh --pr 111 112 113 --repo target_repository
./collect_github_pr.sh --repo target_repository --pr 111 112 113
```

## Output

- outフォルダに出力
    - pr_list.csv : PRの一覧
    - <PR番号>-<PRのタイトル>.csv : PRのレビューコメント一覧
    - <PR番号>-<PRのタイトル>フォルダ : PRの各レビューコメントの詳細内容をmdファイルに出力

## 雑記

reference memo:

- [python docker environment setting](https://zuma-lab.com/posts/docker-python-settings)