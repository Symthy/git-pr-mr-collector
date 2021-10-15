# Github PR and GitLab MR Collect Tool

- Github の指定 repository から PR一覧と 各PR内のレビューコメントを収集
    - レビューコメントの一覧を csv ファイルで出力
    - 個々のレビューコメントの詳細情報を md ファイルで出力（PR毎にフォルダを切って出力）

- GitLab の指定 project から MR一覧と 各MR内のレビューコメントを収集
    - レビューコメントの一覧を csv ファイルで出力
    - ※ 現状 diff と レビューコメントのURL 取れないため md ファイル出力は未提供

## Initialize

前提：dockerがインストール済み

以下をコマンド実行

```
./initialize.sh
```

## Github PR collect tool

### Configuration

- conf/github_access_token.txt に、Github access token を記載
- conf/target_github_repository.conf に 収集対象のリポジトリとそのオーナーを記載

設定例：リポジトリのURLが `https://github.com/owner-name/repository-name` だった場合、target_github_repository.conf には以下のように記載

```
[DEFAULT]
REPOSITORY_OWNER_NAME=owner-name
REPOSITORY=repository-name
```

### Execute

収集方法は以下２通りを提供

#### All Github PR collect

設定ファイルに指定された repository 内の全PRを収集

コマンド

```
./github_pr_collect.sh
```

以下により、フィルタが可能

- PRの作成者でフィルタ
    - conf/pr_author_filter_list.txtにPR作成者のGithubアカウント名を記載（空の場合は全取得）
- PRのレビュアーでフィルタ
    - conf/pr_author_filter_list.txtにPRレビュアーのGithubアカウント名を記載（空の場合は全取得）

#### Specified Github PR collect

指定したPRのみを収集。オプションでrepositoryの指定も可能

以下により、フィルタが可能

- PRのレビュアーでフィルタ
    - conf/pr_author_filter_list.txtにPRレビュアーのGithubアカウント名を記載（空の場合は全取得）

コマンド (オプションは順不同)

```
./github_pr_collect.sh --pr[ <pr番号>]... [--repo <repository名>]
```

オプション：

- pr: 収集対象のPR番号を指定（PRは複数指定可能）
- repo: PR取得対象のrepository指定(任意)。指定ない場合は設定ファイルのrepositoryを対象とする

command example:

```
./github_pr_collect.sh --pr 111 112 113
./github_pr_collect.sh --pr 111 112 113 --repo target_repository
./github_pr_collect.sh --repo target_repository --pr 111 112 113
```

### Output

- outフォルダに出力
    - pr_list.csv : PRの一覧
    - <PR番号>-<PRのタイトル>.csv : PRのレビューコメント一覧
    - <PR番号>-<PRのタイトル>フォルダ : PRの各レビューコメントの詳細内容をmdファイルに出力

## GitLab MR collect tool

### Configuration

- conf/gitlab_access_token.txt に、GitLab access token を記載
- conf/target_github_repository.conf に GitLab の ホスト名と、収集対象のリポジトリ(project)のID を記載

設定例：リポジトリのURLが `https://<Gitlab Host Name>/xxxxx/project-name` だった場合、

- GITHUB_HOST に<Gitlab Host Name>を設定。
- PROJECT_ID には UI上に表示されるリポジトリのID(番号)を記載

```
[DEFAULT]
GITHUB_HOST=host-name
PROJECT_ID=xx
```

### Execute

収集方法は以下２通りを提供

#### All GitLab MR collect

設定ファイルに指定された repository(= project) 内の全MRを収集

コマンド

```
./gitlab_mr_collect.sh
```

以下により、フィルタが可能

- MRの作成者でフィルタ
    - conf/mr_author_filter_list.txtにPR作成者のGitLabアカウント名を記載（空の場合は全MR作成者を対象とする）
- MRのレビュアーでフィルタ
    - conf/mr_author_filter_list.txtにPRレビュアーのGitLabアカウント名を記載（空の場合は全レビュアーを対象とする）

#### Specified GitLab MR collect

指定したMRのみを収集。オプションでrepository(= project)の指定も可能

以下により、フィルタが可能

- MRのレビュアーでフィルタ
    - conf/mr_author_filter_list.txtにPRレビュアーのGitLabアカウント名を記載（空の場合は全レビュアーを対象とする）

コマンド (オプションは順不同)

```
./gitlab_mr_collect.sh --mr[ <MR番号>]... [--proj <Project ID>]
```

オプション：

- mr: 収集対象のPR番号を指定（PRは複数指定可能）
- proj: PR取得対象のrepository(project)指定(任意)。指定ない場合は設定ファイルのrepositoryを対象とする

command example:

```
./gitlab_mr_collect.sh  --mr 111 112 113
./gitlab_mr_collect.sh  --mr 111 112 113 --proj 98
./gitlab_mr_collect.sh  --proj 98 --mr 111 112 113
```

### Output

- out/gitlabフォルダに出力
    - mr_list.csv : PRの一覧
    - <MR番号>-<MRのタイトル>.csv : MRのレビューコメント一覧

# 雑記

reference memo:

- [python docker environment setting](https://zuma-lab.com/posts/docker-python-settings)