import datetime
import sqlite3

from git_utils import get_git_commit_count, get_git_commiter_count, get_first_last_commit_date, get_license


DATABASE_FILE = "database.db"


class GithubDb(object):
    def __init__(self):
        self.conn = sqlite3.connect(DATABASE_FILE)
        self.conn.execute("PRAGMA journal_mode=WAL")

        self.create_tables()

        self.c = self.conn.cursor()

    def create_tables(self):
        query = """CREATE TABLE IF NOT EXISTS `GithubProjectUnfiltered` (
            `ID`	INTEGER,
            `GITHUB_ID`	INTEGER NOT NULL UNIQUE,
            `GITHUB_URL`	TEXT NOT NULL UNIQUE,
            `GITHUB_OWNER_NAME`	TEXT NOT NULL,
            `GITHUB_PROJECT_NAME`	TEXT NOT NULL,
            `GITHUB_DESCRIPTION`	TEXT,
            `GITHUB_LICENSE`	TEXT,
            `GITHUB_IS_FORK`	INTEGER,
            `GITHUB_NR_STARGAZERS`	INTEGER,
            `GITHUB_NR_WATCHERS`	TEXT,
            `GITHUB_NR_FORKS`	INTEGER,
            `GITHUB_NR_OPEN_ISSUES`	INTEGER,
            `GITHUB_REPO_CREATION_DATE`	TEXT,
            `GITHUB_LANGUAGE`	TEXT,
            `GIT_PULL_HASH`	TEXT,
            `GIT_PULL_DATE`	TEXT,
            `GIT_NR_COMMITS`	INTEGER,
            `GIT_NR_COMMITTERS`	INTEGER,
            `GIT_FIRST_COMMIT_DATE`	TEXT,
            `GIT_LAST_COMMIT_DATE`	TEXT,
            `PROCESSED`	INTEGER DEFAULT 0,
            PRIMARY KEY(`ID`)
        );"""
        self.conn.execute(query)

    def github_project_exists(self, githubRepository):
        self.c.execute('SELECT ID FROM GithubProjectUnfiltered WHERE GITHUB_ID=?', (githubRepository.id, ))
        return self.c.fetchone() is not None

    def add_new_entry(self, githubRepository, gitRepository):
        query = """INSERT INTO GithubProjectUnfiltered(
            GITHUB_ID,
            GITHUB_URL,
            GITHUB_OWNER_NAME,
            GITHUB_PROJECT_NAME,
            GITHUB_DESCRIPTION,
            GITHUB_LICENSE,
            GITHUB_IS_FORK,
            GITHUB_NR_STARGAZERS,
            GITHUB_NR_WATCHERS,
            GITHUB_NR_FORKS,
            GITHUB_NR_OPEN_ISSUES,
            GITHUB_REPO_CREATION_DATE,
            GITHUB_LANGUAGE,

            GIT_PULL_HASH,
            GIT_PULL_DATE,
            GIT_NR_COMMITS,
            GIT_NR_COMMITTERS,
            GIT_FIRST_COMMIT_DATE,
            GIT_LAST_COMMIT_DATE,

            PROCESSED
            )

            VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0);
        """

        github_tupel = (
            githubRepository.id,
            githubRepository.html_url,
            githubRepository.owner.login,
            githubRepository.name,
            githubRepository.description,
            get_license(githubRepository),
            githubRepository.fork,
            githubRepository.stargazers,
            githubRepository.watchers,
            githubRepository.forks_count,
            githubRepository.open_issues_count,
            githubRepository.created_at.strftime('%Y-%m-%d'),
            githubRepository.language
        )

        if gitRepository:
            (first_date, last_date) = get_first_last_commit_date(gitRepository.workdir)
            git_first_commit_time = datetime.datetime.fromtimestamp(first_date)
            git_last_commit_time = datetime.datetime.fromtimestamp(last_date)  # gitRepository.head.peel().commit_time

            git_tupel = (
                str(gitRepository.head.target),
                datetime.datetime.now().strftime('%Y-%m-%d'),
                get_git_commit_count(gitRepository.workdir),
                get_git_commiter_count(gitRepository.workdir),
                git_first_commit_time.strftime('%Y-%m-%d'),
                git_last_commit_time.strftime('%Y-%m-%d')
            )
        else:
            git_tupel = (
                None,
                None,
                None,
                None,
                None,
                None
            )

        try:
            self.c.execute(query, github_tupel + git_tupel)
            self.conn.commit()
        except sqlite3.IntegrityError as e:
            print("{} is a duplicate!".format(githubRepository.git_url))

    def update_entry_with_git(self, github_url, gitRepository):
        query = """UPDATE GithubProjectUnfiltered
        SET GIT_PULL_HASH = ?,
            GIT_PULL_DATE = ?,
            GIT_NR_COMMITS = ?,
            GIT_NR_COMMITTERS = ?,
            GIT_FIRST_COMMIT_DATE = ?,
            GIT_LAST_COMMIT_DATE = ?
        WHERE GITHUB_URL = ?
        """

        (first_date, last_date) = get_first_last_commit_date(gitRepository.workdir)
        git_first_commit_time = datetime.datetime.fromtimestamp(first_date)
        git_last_commit_time = datetime.datetime.fromtimestamp(last_date)

        tupel = (
            str(gitRepository.head.target),
            datetime.datetime.now().strftime('%Y-%m-%d'),
            get_git_commit_count(gitRepository.workdir),
            get_git_commiter_count(gitRepository.workdir),
            git_first_commit_time.strftime('%Y-%m-%d'),
            git_last_commit_time.strftime('%Y-%m-%d'),
            github_url
        )

        try:
            self.c.execute(query, tupel)
            self.conn.commit()
        except sqlite3.IntegrityError as e:
            print("{} cannot be updated with {}!".format(github_url, gitRepository))
