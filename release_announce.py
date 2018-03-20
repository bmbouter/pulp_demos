"""
This module will produces various announcements for announcing Pulp GA and Beta releases.

It uses a query on pulp.plan.io to identify the issues in the release. This is required because the
python-redmine client doesn't support filtering so another approach would require a full search of
issues each time.

Run it in a virtualenv and install the requirements file with something like:

python3 -m venv announce_env
source announce_env/bin/activate
pip install -r requirements.txt
python3 release_announce.py --help

See the --help for more info on the arguments.
"""

import argparse
from collections import defaultdict
import os

from redminelib import Redmine


EMAIL_TEMPLATE = """
Pulp {full_version}{beta_name_number} is now available, and can be downloaded from the {x_y_version} {beta_or_stable} repositories:

https://repos.fedorapeople.org/repos/pulp/pulp/{beta_or_stable}/{x_y_version}/

This release includes {features_or_fixes} for: {projects}

Upgrading
=========

The Pulp {x_y_version} {beta_or_stable} repository is included in the pulp repo files:
    https://repos.fedorapeople.org/repos/pulp/pulp/fedora-pulp.repo for Fedora
    https://repos.fedorapeople.org/repos/pulp/pulp/rhel-pulp.repo for RHEL 7

After enabling the pulp-{beta_or_stable} repository, you'll want to follow the standard upgrade path
with migrations:

$ sudo systemctl stop httpd pulp_workers pulp_resource_manager pulp_celerybeat pulp_streamer goferd
$ sudo yum upgrade
$ sudo -u apache pulp-manage-db
$ sudo systemctl start httpd pulp_workers pulp_resource_manager pulp_celerybeat pulp_streamer goferd

The pulp_streamer and goferd services should be omitted if those services are not installed.

Issues Addressed
================
{issue_str}

"""


BLOG_POST_TEMPLATE = """
---
title: Pulp {full_version}{beta_name_number}
author: {author}
tags:
  - release
---

Pulp {full_version}{beta_name_number} is now available in the {beta_or_stable} repositories:

* [pulp-2-{beta_or_stable}](https://repos.fedorapeople.org/pulp/pulp/{beta_or_stable}/2/)
* [pulp-{beta_or_stable}](https://repos.fedorapeople.org/pulp/pulp/{beta_or_stable}/latest/)

This release includes {features_or_fixes} for {projects}.

## Upgrading

The Pulp 2 {beta_or_stable} repositories are included in the pulp repo files:

- [Fedora](https://repos.fedorapeople.org/repos/pulp/pulp/fedora-pulp.repo)
- [RHEL 7](https://repos.fedorapeople.org/repos/pulp/pulp/rhel-pulp.repo)

After enabling the pulp-{beta_or_stable} or pulp-2-{beta_or_stable} repository, you'll want to
follow the standard upgrade path with migrations:

```sh
$ sudo systemctl stop httpd pulp_workers pulp_resource_manager pulp_celerybeat pulp_streamer goferd
$ sudo yum upgrade
$ sudo -u apache pulp-manage-db
$ sudo systemctl start httpd pulp_workers pulp_resource_manager pulp_celerybeat pulp_streamer goferd
```

The `pulp_streamer` and `goferd` services should be omitted if those services are not installed.


## Issues Addressed
{issue_str}
"""


TWEET_TEMPLATE = "Pulp {full_version}{beta_name_number} is available with {features_or_fixes} for {projects}. {upgrade_or_test} is recommended. Read more here: "


REDMINE_URL = 'https://pulp.plan.io'


def x_y_z_version(version):
    if version.count('.') is not 2:
        raise ValueError('The version must be in x.y.z format')
    return version


def parse_args():
    parser = argparse.ArgumentParser(description='Create Pulp release announcements.')
    parser.add_argument('--version', type=x_y_z_version, help='The x.y.z version to create release notes for', required=True)
    parser.add_argument('--author', help='The full name of the author used in the blogpost.', required=True)
    parser.add_argument('--query-num', help='The number in the URL on Redmine that shows all issues for this release', type=int, required=True)
    parser.add_argument('--beta', help='The Beta build number. Only set if it is a Beta build.', type=int)
    args = parser.parse_args()

    if args.version.endswith('0'):
        args.features_or_fixes = 'new features'
    else:
        args.features_or_fixes = 'bugfixes'

    if args.beta is None:
        args.beta_or_stable = 'stable'
        args.upgrade_or_test = 'Upgrading'
        args.beta_name_number = ''
    else:
        args.beta_or_stable = 'beta'
        args.upgrade_or_test = 'Beta testing'
        args.beta_name_number = ' Beta {num}'.format(num=args.beta)

    return args


def print_announcements(args):
    redmine = Redmine(REDMINE_URL, key=os.environ['REDMINE_KEY'])
    issues = [issue for issue in redmine.issue.filter(query_id=args.query_num)]
    issues_by_project = defaultdict(list)
    for issue in issues:
        issues_by_project[issue.project.name].append(issue)

    issue_str = ''
    projects = sorted(issues_by_project.keys())
    for project_name in projects:
        issue_str += '\n' + project_name + '\n'
        for issue in issues_by_project[project_name]:
            issue_str += '\t{num}\t{subject}\n'.format(num=issue.id, subject=issue.subject)

    project_str = ', '.join(projects[:-1]) + ', and {last_one}'.format(last_one=projects[-1])
    x_y_version = args.version.rpartition('.')[0]
    email_msg = EMAIL_TEMPLATE.format(issue_str=issue_str, projects=project_str,
                                      full_version=args.version, x_y_version=x_y_version,
                                      beta_or_stable=args.beta_or_stable,
                                      features_or_fixes=args.features_or_fixes,
                                      beta_name_number=args.beta_name_number)
    print(email_msg)

    print('---------------------------------------------------\n')

    template_issue_str = ''
    for project_name in projects:
        template_issue_str += '\n### ' + project_name + '\n'
        for issue in issues_by_project[project_name]:
            template_issue_str += '- [{num}\t{subject}]({url})\n'.format(num=issue.id,
                                                                          subject=issue.subject,
                                                                          url=issue.url)
    blog_msg = BLOG_POST_TEMPLATE.format(issue_str=template_issue_str, projects=project_str,
                                         full_version=args.version, author=args.author,
                                         beta_or_stable=args.beta_or_stable,
                                         features_or_fixes=args.features_or_fixes,
                                         beta_name_number=args.beta_name_number)

    print(blog_msg)

    print('---------------------------------------------------\n')

    tweet_msg = TWEET_TEMPLATE.format(full_version=args.version, projects=project_str,
                                      features_or_fixes=args.features_or_fixes,
                                      upgrade_or_test=args.upgrade_or_test,
                                      beta_name_number=args.beta_name_number)
    print(tweet_msg)


def main():
    args = parse_args()
    print_announcements(args)


if __name__ == "__main__":
    main()
