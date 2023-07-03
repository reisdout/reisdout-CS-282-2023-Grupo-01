import json
import os.path
import pandas
import random
import requests

from requests.auth import HTTPBasicAuth

SONAR_USER_TOKEN = 'squ_9ce7035a094c04fcac7f13c705c88ec354b92302'
SONAR_HTTP_URL = 'http://localhost:9000'
REPRODUCTION_FOLDER = 'C:\\Users\\Andre\\Desktop\\reproducao_artigo\\'
PROJECT_PATH = 'C:\\Users\\Andre\\guava\\guava'
CODE_WINDOW = 5
# Function to get all issues from a project
def get_project_issues(project_key: str):
    has_next_page = True
    issues = []
    issues_counter = 0
    page_index = 1
    basic = HTTPBasicAuth(SONAR_USER_TOKEN, '')
    while has_next_page:
        resp = requests.get('{}/api/issues/search?componentKeys={}&ps=500&p={}'.format(SONAR_HTTP_URL, project_key, page_index), auth=basic)
        resp = resp.json()
        issues += resp['issues']
        issues_counter += len(resp['issues'])
        page_index += 1
        has_next_page = resp['total'] != issues_counter

    return issues


# Function to get only issues contained in a list
def filter_issues(issues, acceptable_squid):
    filtered_issues = []
    for issue in issues:
        if len(issue['flows']) != 0:
            continue
        if issue['rule'] in acceptable_squid:
            filtered_issues += [ issue ]

    return filtered_issues

# Function to get known squid values from the raw dataset from the original work
def get_acceptable_squid(filepath):
    dataset = pandas.read_csv(filepath)
    rules = dataset['rule'].unique().tolist()
    rules = [ rule.replace('squid', 'java') for rule in rules]
    return rules

def load_code_window(filename, line, window):
    with open(filename, 'r') as file:
        lines = file.readlines()
        start_line = line - int(window/2) - 1
        end_line = line + int(window/2) - 1
        print(filename, line, start_line, end_line)
        selected_lines = lines[start_line: end_line + 1]  # Adjusting indices for 0-based indexing

        lines_with_prefix = []
        index = start_line + 1
        for line in selected_lines:
            lines_with_prefix += [ '{}: {}'.format(index, line)]
            index += 1
        return ''.join(lines_with_prefix)

def load_code_from_issues(project_path, issues, window):
    index = 1
    for issue in issues:
        src_file = issue['component'].split(':')[1]
        line = issue['line']
        code_window = load_code_window('{}\\{}'.format(project_path, src_file), line, window)

        with open('code_issue_idx_{}_key_{}.txt'.format(index, issue['key']), 'w') as f:
            f.write(code_window)

        index += 1

# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    if not os.path.exists('sample.json'):
        # get all the squids for which the model was trained
        squid = get_acceptable_squid('{}\\raw_data\\true_positives\\tp_complete.csv'.format(REPRODUCTION_FOLDER))
        squid += get_acceptable_squid('{}\\raw_data\\false_positives\\fp_complete.csv'.format(REPRODUCTION_FOLDER))
        squid = list(set(squid))

        # get all issues from project under evaluation
        all_issues = get_project_issues('google-guava')

        # keep only issues known to the model
        filtered_issues = filter_issues(all_issues, squid)

        # randomly select 40 issues
        sampled_issues = random.sample(filtered_issues, 40)

        with open('sample.json', 'w') as f:
            json.dump(sampled_issues, f)

    issues = []
    with open('sample.json') as f:
        issues = json.load(f)

    load_code_from_issues(PROJECT_PATH, issues, CODE_WINDOW)