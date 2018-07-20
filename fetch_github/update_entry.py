#!/usr/bin/env python3

import argparse
import os

import pygit2

from db_utils import GithubDb


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Update single entry of a database to add git informations')
    parser.add_argument('path', type=str, help='path to git repostiory', action='store')

    args = parser.parse_args()

    if not os.path.exists(args.path):
        parser.error('The directory "{}" does not exist'.format(args.path))

    git_repo = pygit2.Repository(args.path)

    github_url = git_repo.remotes['origin'].url

    db = GithubDb()

    db.update_entry_with_git(github_url, git_repo)
