import requests as requests

OWNER_NAME = "Symthy"
REPOSITORY = "TodoList-ts-pre"

GITHUB_BASEURL = "https://api.github.com"
GITHUB_GET_PULL_API = GITHUB_BASEURL + "/repos/" + OWNER_NAME + "/" + REPOSITORY + "/pulls"
STATE_VAL = "all"  # open, all, close
SORT_VAL = "created"  # updated, created, popularity, long-running
DIRECTION_VAL = "desc"  # desc, asc


def build_header():
    with open('./conf/token') as f:
        github_token = f.read()
    return {
        'Accept': 'application/vnd.github.v3+json',
        'Authorization': 'token {}'.format(github_token)
    }


def build_get_pulls_api_url():
    return GITHUB_GET_PULL_API + '?state=' + STATE_VAL


def main():
    headers = build_header()
    api_url = build_get_pulls_api_url()
    response = requests.get(api_url, headers=headers)
    # print(response.json())
    json_array = response.json()
    review_comments_url_datasets = []
    for data in json_array:
        pr_num = data['number']
        user_name = data['user']['login']
        review_comments_url = data['review_comments_url']
        review_comments_url_datasets.append({
            'pr': pr_num,
            'creator': user_name,
            'url': review_comments_url
        })

    for dataset in review_comments_url_datasets:
        print('=== PR : {} ==='.format(dataset['pr']))
        comments_res = requests.get(dataset['url'], headers=headers)
        print('comments:')
        for comment_obj in comments_res.json():
            print(comment_obj['body'])
        print('===============')


main()
