from typing import List, Optional
import subprocess
import os
import shutil
import pathlib

from git_backup.config import DEFAULT_COMMIT_MESSAGE
from git_backup.secrets import Secrets
from git_backup.logger import get_logger
from git_backup.types import Config, PathConfig, RSyncConfig, RepoConfig

log = get_logger('sync')

def exec_sh(cmd: List[str], cwd: Optional[str] = None) -> str:
    proc = subprocess.Popen(cmd, 
                            cwd=cwd,
                            stdout=subprocess.PIPE, 
                            stderr=subprocess.PIPE, 
                            universal_newlines=True)
    stdout, stderr = proc.communicate()
    if proc.returncode != 0:
        log.error(f'ERROR: exec_sh() Failed to execute command: {" ".join(cmd)}. \nError: {stderr}')
        raise RuntimeError(f'Failed to execute command: {" ".join(cmd)}. \nError: {stderr}')
        
    return stdout

def mkdir_p(path: str):
    pathlib.Path(path).mkdir(parents=True, exist_ok=True)

def get_repo_path(repo: RepoConfig):
    if "storage_root" in repo:
        return repo['storage_root']
    return os.path.join('/backup/repos', repo['owner'], repo['name'])

def get_repo_url(repo: RepoConfig, token: Optional[str] = None) -> str:
    url = f'{repo["endpoint"]}/{repo["owner"]}/{repo["name"]}.git'
    if token is None:
        return url
    
    spl = url.split('://')
    if len(spl) > 1:
        protocol, url = spl
    else:
        protocol, url = 'https', spl[0]
    return f'{protocol}://{token}@{url}'

def git_fetch(repo: RepoConfig, secrets: Secrets):
    """
    Fetch the ref from remote
    """
    local_path = get_repo_path(repo)
    git_path = f'{local_path}/.git'
    
    exists = os.path.exists(git_path)
    if exists and not os.path.isdir(git_path):
        log.error(f'ERROR: git_fetch() Invalid path. Expecting .git directory at path: {git_path}')
        raise RuntimeError(f'Invalid path. Expecting .git directory at path: {git_path}')
    
    url = get_repo_url(repo, secrets.get_token(repo['owner'], repo['name']))
    branch = repo['branch']

    if not exists:
        # first pull
        log.info('git_fetch() first pull')
        exec_sh(["git", "clone", url, '-q', "--depth", "1", "--branch", branch, "."], cwd=local_path)
    else:
        # subsequent pulls
        log.info('git_fetch() subsequent pull')
        exec_sh(["git", "fetch", '-q', url], cwd=local_path)
        exec_sh(["git", "switch", '-q', branch], cwd=local_path)
        exec_sh(["git", "pull", '-q', url, branch], cwd=local_path)
        
def git_checkout(repo: RepoConfig, branch: str, secrets: Secrets):
    """
    Checkout the branch
    """
    owner, name = repo['owner'], repo['name']
    log.info(f'git_checkout() owner={owner} repo={name} branch={branch}')
    
    local_path = get_repo_path(repo)
    url = get_repo_url(repo, secrets.get_token(owner, name))
    
    exec_sh(["git", "fetch", '-q', url], cwd=local_path)
    exec_sh(["git", "switch", '-q', branch], cwd=local_path)
    exec_sh(["git", "pull", '-q', url, branch], cwd=local_path)
    
def git_add(repo: RepoConfig, path: str):
    if repo['git']['add'] == False:
        return
    
    local_path = get_repo_path(repo)
    log.info(f'git_add() path={path}')
    exec_sh(["git", "add", path], cwd=local_path)
    

def resolve_remote(repo: RepoConfig, path: str) -> str:
    out = f'{get_repo_path(repo)}'
    if os.path.isabs(path):
        out = out + path
    elif path.startswith('./'):
        out = out + path[1:]
    else:
        out = out + f'/{path}'
    return os.path.normpath(out)

def git_status(repo: RepoConfig) -> str:
    local_path = get_repo_path(repo)
    return exec_sh(["git", "status"], cwd=local_path)

def git_commit(repo: RepoConfig) -> str:
    if repo['git']['commit'] == False:
        return
    
    local_path = get_repo_path(repo)
    
    if 'email' in repo['git']:
        email = repo['git']['email']
        exec_sh(["git", "config", "user.email", email], cwd=local_path)
        
    if 'name' in repo['git']:
        name = repo['git']['name']
        exec_sh(["git", "config", "user.name", name], cwd=local_path)
    
    message = repo['git']['message'] if 'message' in repo['git'] else DEFAULT_COMMIT_MESSAGE
    
    log.info('git_commit()')
    return exec_sh(["git", "commit", "-m", message], cwd=local_path)

def git_push(repo: RepoConfig) -> str:
    if repo['git']['push'] == False:
        return
    
    local_path = get_repo_path(repo)
    
    cmd = ["git", "push"]
    if 'force_push' in repo['git'] and repo['git']['force_push'] == True:
        cmd.append('-f')
        
    log.info(f'git_push() cmd={" ".join(cmd)}')
    return exec_sh(cmd, cwd=local_path)
    
    
def compress(repo: RepoConfig, path: PathConfig) -> str:
    archive_type = path['compress']
    if archive_type is None:
        return
        
    # directory to begin archiving from (local path)
    root_dir = os.path.dirname(path['local'])
    
    # directory that will contain the archive in the repo
    remote_dir = resolve_remote(repo, os.path.dirname(path["remote"]))
    mkdir_p(remote_dir)
    
    # destination filename without extension (/backup/repos/{owner}/{repo}/{remote_dirname}/{remote_basename})
    remote_file = os.path.basename(path['remote'])
    remote_file = os.path.splitext(remote_file)[0]
    dest = os.path.join(remote_dir, remote_file)
    
    # file/directory to archive
    base_dir = os.path.basename(path['local'])
    
    log.info(f'compress() dest={dest} root_dir={root_dir} base_dir={base_dir}') 
    
    return shutil.make_archive(dest, archive_type, root_dir, base_dir)
        
def rsync(repo: RepoConfig, path: PathConfig, config: RSyncConfig) -> str:   
    cmd = ['rsync']
    if config['archive']:
        cmd.append('-a')
    else: 
        cmd.append('-r')
    
    local_path = path["local"]
    cmd.append(path['local'])
        
    if os.path.isdir(path['local']):
        # syncing directory
        # make directory
        mkdir_p(resolve_remote(repo, path["remote"]))
        remote_path = resolve_remote(repo, os.path.join(os.path.dirname(path["remote"]), ''))
        if not local_path.endswith('/'):
            local_path += '/'
        
        log.info(f'rsync() local_dir={local_path} remote_dir={remote_path}')
    else:
        # syncing file
        # make parent dir
        mkdir_p(resolve_remote(repo, os.path.dirname(path["remote"])))
        remote_path = resolve_remote(repo, path["remote"])
        log.info(f'rsync() local_file={local_path} remote_file={remote_path}')
    
    cmd.append(local_path)
    cmd.append(remote_path)
    exec_sh(cmd)
    return remote_path
    
def sync(conf: Config):
    """
    Sync changes into repository
    """
    for repo in conf['repos']:
        repo_path = get_repo_path(repo)
        log.debug(f'sync() start repo_path={repo_path}')
        
        mkdir_p(repo_path)
        
        git_fetch(repo, conf['secrets'])
        cur_branch = repo['branch']
        
        for path in repo['paths']:
            next_branch = path['branch'] if 'branch' in path and path['branch'] is not None else cur_branch
            
            if next_branch != cur_branch:
                git_checkout(repo, next_branch, conf['secrets'])
                cur_branch = next_branch
            
            if path['compress']:
                # if compressing, zip the path directly into the repo directory, overwrite existing
                archive_name = compress(repo, path)
                change_path = os.path.relpath(archive_name, repo_path)
            else:
                # otherwise, use rsync to pull changes into repo
                change_path = rsync(repo, path, conf['rsync'])
                
            git_add(repo, change_path)
                
        log.debug(f'sync() git_status: \n{git_status(repo)}')
        git_commit(repo)
        git_push(repo)