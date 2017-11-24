import os
import subprocess
from getpass import getpass

import github3
import pygit2


CREDENTIALS_FILE = "CREDENTIALS_FILE"

AUTH_NOTE = "fetch_github.py"
AUTH_NOTE_URL = "http://example.com"
AUTH_SCOPES = []


def _get_username_password():
    username = password = ''

    while not username:
        username = input('Username for github.com: ')
    while not password:
        password = getpass('Password for {0}: '.format(username))

    return username, password


def authorize_use_credentials():
    username, password = _get_username_password()
    return github3.login(username, password)


def authorize_use_token():
    if not os.path.isfile(CREDENTIALS_FILE):
        return authorize_new_token()

    token = id = ''
    with open(CREDENTIALS_FILE, 'r') as fd:
        token = fd.readline().strip()
        id = fd.readline().strip()

    return github3.login(token=token)


def authorize_new_token():
    username, password = _get_username_password()
    auth = github3.authorize(username, password, AUTH_SCOPES, AUTH_NOTE, AUTH_NOTE_URL)
    with open(CREDENTIALS_FILE, 'w') as fd:
        fd.write('{token}\n{id}'.format(token=auth.token, id=auth.id))

    return github3.login(token=auth.token)


def login_to_github(useAccessToken):
    if useAccessToken:
        return authorize_use_token()
    else:
        return authorize_use_credentials()


# Print iterations progress
# @see: https://stackoverflow.com/a/34325723/2967999
def printProgressBar (iteration, total, prefix = '', suffix = '', decimals = 1, length = 100, fill = '█'):
    """
    Call in a loop to create terminal progress bar
    @params:
        iteration   - Required  : current iteration (Int)
        total       - Required  : total iterations (Int)
        prefix      - Optional  : prefix string (Str)
        suffix      - Optional  : suffix string (Str)
        decimals    - Optional  : positive number of decimals in percent complete (Int)
        length      - Optional  : character length of bar (Int)
        fill        - Optional  : bar fill character (Str)
    """
    percent = ("{0:." + str(decimals) + "f}").format(100 * (iteration / float(total)))
    filledLength = int(length * iteration // total)
    bar = fill * filledLength + '-' * (length - filledLength)
    print('\r%s [%s] %s%% %s' % (prefix, bar, percent, suffix), end = '\r')


class GitProgressCallback(pygit2.RemoteCallbacks):
    def __init__(self):
        super(pygit2.RemoteCallbacks, self).__init__()

    def sideband_progress(self, string):
        print(string)

    def push_update_reference(self, refname, message):
        print(message)

    def transfer_progress(self, stats):
        clone_stats = '{}/{} objects, {} bytes received'.format(stats.received_objects, stats.total_objects, stats.received_bytes)
        printProgressBar(stats.received_objects,  stats.total_objects, prefix='Progress', suffix='Complete, {}'.format(clone_stats), length=50)


def get_license(repo):
    # workaround until new github3.py is released
    url = repo._build_url('license', base_url=repo._api)
    json = repo._json(repo._get(url, headers={'Accept': 'application/vnd.github.drax-preview+json'}), 200)
    if json is not None:
        return json.get('license', {}).get('key')
    else:
        return None

def get_git_commit_count(path):
    """ Gets the number of commits without merges from a Git repository. """
    process = subprocess.Popen(['git', 'rev-list', 'HEAD', '--count', '--no-merges'], cwd=path, stdout=subprocess.PIPE)
    stdout, _ = process.communicate()
    number = stdout.decode().strip("\n")
    return int(number)


def get_git_commiter_count(path):
    """ Gets the number of committers from a Git repository. """
    process = subprocess.Popen(['git', 'shortlog', '-sn'], cwd=path, stdout=subprocess.PIPE)
    stdout, _ = process.communicate()
    committers = stdout.decode("ISO-8859-1")
    return len(committers.split('\n'))


def get_first_last_commit_date(path):
    """ Gets the first and repository commit as a timestamp. """
    # %at specifies a UNIX time stamp
    process = subprocess.Popen(['git', 'log', '--format=%at'], cwd=path, stdout=subprocess.PIPE)
    stdout, _ = process.communicate()
    log = stdout.decode().strip('\n').split('\n')
    last = int(log[0])
    first = int(log[-1])
    return (first, last)