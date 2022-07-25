import yaml
import os
from git_backup.cron import Cron
from git_backup.env import get_env

from typing import List, Optional
from git_backup.secrets import Secrets
from git_backup.types import CompressType, GitConfig, LoopConfig, PathConfig, RepoConfig, Config, SecretsConfig


SAVE_CONFIG = get_env("SAVE_CONFIG", True, "1", bool)
SAVE_SECRETS = get_env("SAVE_SECRETS", True, "1", bool)

CONF_ROOT = get_env("CONF_ROOT", True, "/backup/config")
CONF_PATH = os.path.join(CONF_ROOT, "config.yaml")

SECRETS_ROOT = get_env("SECRETS_ROOT", True, "/backup/secrets")
SECRETS_PATH = os.path.join(SECRETS_ROOT, "secrets.yaml")

DEFAULT_API_BASE = 'https://api.github.com'
DEFAULT_ENDPOINT = 'https://github.com'
DEFAULT_COMPRESSION = 'zip'
DEFAULT_INTERVAL = 1440
DEFAULT_COMMIT_MESSAGE = 'chore(backup): update backup'
DEFAULT_GIT_EMAIL = 'bot@backup.example'
DEFAULT_GIT_NAME = 'Backup (bot)'

def make_path_config(path_str: str, branch: str = "main", compress: CompressType = None) -> PathConfig:
    spl = path_str.split(':')
    local_path = spl[0]
    remote_path = spl[1] if len(spl) > 1 else local_path
    
    return {
        "local": os.path.abspath(local_path),
        "remote": remote_path,
        "compress": compress,
        "branch": branch
    }

def make_git_config() -> GitConfig:
    add = get_env('GIT_ADD', True, '1', bool)
    commit = get_env('GIT_COMMIT', True, '1', bool)
    push = get_env('GIT_PUSH', True, '1', bool)
    force_push = get_env('GIT_FORCE_PUSH', True, '0', bool)
    message = get_env('GIT_MESSAGE', True, DEFAULT_COMMIT_MESSAGE, str)
    email = get_env('GIT_EMAIL', True, DEFAULT_GIT_EMAIL)
    name = get_env('GIT_NAME', True, DEFAULT_GIT_NAME)
    
    
    return {
        "add": add,
        "commit": commit,
        "push": push,
        "force_push": force_push,
        "message": message,
        "name": name,
        "email": email
    }

def make_repo_config(
    compress: Optional[CompressType] = None
) -> RepoConfig:
    name = get_env('REPO_NAME')
    owner = get_env('REPO_OWNER')
    paths = get_env('PATHS', False, None, "list[str]")
    endpoint = get_env('REPO_ENDPOINT', True,  DEFAULT_ENDPOINT)
    api_base = get_env('API_BASE_URL', True,  DEFAULT_API_BASE)
    branch = get_env('REPO_BRANCH', True, "main")
    
    return {
        "name": name,
        "owner": owner,
        "branch": branch,
        "endpoint": endpoint,
        "api_base": api_base,
        "paths": [make_path_config(p, branch, compress) for p in paths],
        "git": make_git_config()
    }
    
def make_loop_config() -> LoopConfig:
    loop = get_env('LOOP', True, True, bool)
    interval = get_env('LOOP_INTERVAL', True, DEFAULT_INTERVAL, float)
    schedule = get_env('LOOP_SCHEDULE', True)
    
    loop_conf = {
        "loop": loop,
        "interval": interval
    }
    if schedule is not None:
        loop_conf['schedule'] = Cron(schedule)
    return loop_conf
    
def bootstrap() -> Config:
    '''
    Create config.yaml from env variables and defaults
    '''
    
    compress = get_env('COMPRESS', True)
    
    if compress:
        compress = compress.lower().strip()
        if compress == 'yes' or compress == '1' or compress == 'true':
            compress = DEFAULT_COMPRESSION
        
    data = {
        "repos": [make_repo_config(compress)],
        "loop": make_loop_config()
    }

    if SAVE_CONFIG:
        with open(CONF_PATH, "w", encoding='utf8') as stream:
            yaml.dump(data, stream, default_flow_style=False, allow_unicode=True)
    return data

def make_default_secrets(name: str, owner: str, token: Optional[str] = None) -> SecretsConfig:
    return {
        owner: {
            name: {
                "token": token
            }
        }
    }
    
def bootstrap_secrets(default_repo: RepoConfig) -> SecretsConfig:
    name = default_repo["name"]
    owner = default_repo["owner"]
    token = get_env('GIT_TOKEN', True)
    
    data = make_default_secrets(name, owner, token)
    
    if SAVE_SECRETS:
        with open(SECRETS_PATH, "w", encoding='utf8') as stream:
            yaml.dump(data, stream, default_flow_style=False, allow_unicode=True)
    return data

    
def _load_conf():
    try:
        stream = open(CONF_PATH, "r")
    except IOError as e:
        if e.errno != 2: # not "file does not exist"
            raise e
        return bootstrap()
    try:
        return yaml.safe_load(stream)
    except yaml.YAMLError as e:
        raise ValueError(f"Error reading config: {e}").with_traceback(e.__traceback__)

def _load_secrets(conf: Config) -> SecretsConfig:
    try:
        stream = open(SECRETS_PATH, "r")
    except IOError as e:
        if e.errno != 2: # not "file does not exist"
            raise e
        default_repo = conf['repos'][0]
        return bootstrap_secrets(default_repo)
    try:
        return yaml.safe_load(stream)
    except yaml.YAMLError as e:
        raise ValueError(f"Error reading secrets: {e}").with_traceback(e.__traceback__)

def load() -> Config:
    conf = _load_conf()
    conf['secrets'] = Secrets(_load_secrets(conf))
    return conf