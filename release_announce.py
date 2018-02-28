import argparse
from collections import defaultdict
import os

from redminelib import Redmine


EMAIL_TEMPLATE = """
Pulp {full_version} is now generally available, and can be downloaded from the {x_y_version} stable repositories:

https://repos.fedorapeople.org/repos/pulp/pulp/stable/{x_y_version}/

This release includes a small number bug fixes for: {projects}

Upgrading
=========

The Pulp {x_y_version} stable repository is included in the pulp repo files:
    https://repos.fedorapeople.org/repos/pulp/pulp/fedora-pulp.repo for Fedora
    https://repos.fedorapeople.org/repos/pulp/pulp/rhel-pulp.repo for RHEL 7

After enabling the pulp-stable repository, you'll want to follow the standard upgrade path with migrations:

$ sudo systemctl stop httpd pulp_workers pulp_resource_manager pulp_celerybeat pulp_streamer goferd
$ sudo yum upgrade
$ sudo -u apache pulp-manage-db
$ sudo systemctl start httpd pulp_workers pulp_resource_manager pulp_celerybeat pulp_streamer goferd

The pulp_streamer and goferd services should be omitted if those services are not installed.

Issues Addressed
================
{issue_str}

"""

REDMINE_URL = 'https://pulp.plan.io'


def x_y_z_version(version):
    if version.count('.') is not 2:
        raise ValueError('The version must be in x.y.z format')
    return version


def parse_args():
    parser = argparse.ArgumentParser(description='Create Pulp release announcements.')
    parser.add_argument('--version', type=x_y_z_version, help='The x.y.z version to create release notes for', required=True)
    parser.add_argument('--query-num', help='The number in the URL on Redmine that shows all issues for this release', type=int, required=True)
    return parser.parse_args()


def print_release_notes(args):
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
                                      full_version=args.version, x_y_version=x_y_version)
    print(email_msg)


def main():
    args = parse_args()
    print_release_notes(args)


if __name__ == "__main__":
    main()
