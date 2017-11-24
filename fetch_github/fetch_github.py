#!/usr/bin/env python3

import argparse
import os
import time

import github3
import pygit2

from git_utils import login_to_github, GitProgressCallback, printProgressBar
from db_utils import GithubDb


def fetch_repo(repo):
    git_repo = None
    if args.clone_repo:
        clone_dir_name = repo.full_name.replace('\\', '-').replace('/', '-')
        clone_dir = os.path.realpath(os.path.join(args.clone_repo_dir, clone_dir_name))

        if os.path.exists(clone_dir):
            print('Repository already downloaded: "{}"'.format(repo.full_name))
            if not db.github_project_exists(repo):
                print('Add: "{}" into Database'.format(repo.full_name))
                git_repo = pygit2.Repository(clone_dir)
                db.add_new_entry(repo, git_repo)
            return

        print('Clone: "{}" into "{}"'.format(repo.full_name, clone_dir))
        git_repo = pygit2.clone_repository(repo.clone_url, clone_dir, callbacks=GitProgressCallback())
        print()  # new line

    if not db.github_project_exists(repo):
        print('Add: "{}" into Database'.format(repo.full_name))
        db.add_new_entry(repo, git_repo)
    else:
        print('"{}" already inside Database'.format(repo.full_name))


def wait_some_time(seconds):
    for second in range(seconds):
        printProgressBar(second, seconds, prefix='Wait', suffix='Completed, {} of {} Seconds remaining'.format(seconds-second, seconds), length=50)
        time.sleep(1)
    print()  # new line


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Download Repositories from Github based on a search query.')
    parser.add_argument('query', type=str, help='query which search for the required repositories', action='store')
    parser.add_argument('--no-login', help='access api as anonymous user', action='store_true')
    parser.add_argument('--clone-repo', help='clone all found repositories to local disk', action='store_true')
    parser.add_argument('--clone-repo-dir',type=str, default='./', help='clone all found repositories into this subdir', action='store')
    parser.add_argument('--limit', type=int, default=-1, help='limit number of results. -1 means no limit')

    args = parser.parse_args()

    # authorize to GitHub
    if args.no_login:
        gh = github3.GitHub()
    else:
        gh = login_to_github(True)

    # check if clone dir exists
    if args.clone_repo:
        if not os.path.isdir(args.clone_repo_dir):
            print('"{0}" is not an existing directory!'.format( os.path.realpath(args.clone_repo_dir)))
            exit(1)

    # open database
    db = GithubDb()

    # search for repositories which match our query
    repo_found = gh.search_repositories(args.query, per_page=100, number=args.limit)

    for repo_result in repo_found:
        repo = repo_result.repository
        try:
            fetch_repo(repo)
        except github3.exceptions.ForbiddenError as e:
            print('Exceeded rate limit! Wait some time before continue')
            wait_some_time(5*60)
            fetch_repo(repo)
        except Exception as e:
            print('Exception occured while fetching: "{}". Try once again'.format(repo.full_name))
            fetch_repo(repo)
