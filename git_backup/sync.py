from genericpath import isfile
import hashlib
from typing import List, Optional
import subprocess
import os
import shutil
import pathlib

from git_backup.config import DEFAULT_COMMIT_MESSAGE
from git_backup.secrets import Secrets
from git_backup.logger import get_logger
from git_backup.types import Config, OversizeHandler, OversizeHandlerType, PathConfig, RSyncConfig, RepoConfig

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

def git_status(repo: RepoConfig, porcelain: bool = False) -> str:
    local_path = get_repo_path(repo)
    cmd = ["git", "status"]
    if porcelain:
        cmd.append('--porcelain')
    return exec_sh(cmd, cwd=local_path)

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

def check_sizes(repo: RepoConfig, ppath: str, oversize_handler: OversizeHandler) -> List[str]:
    """Traverse each child, if size exceeds limit call oversize handler
    """
    
    max_file_size = repo['max_file_size']
    uncache_paths = []
    repo_path = get_repo_path(repo)
    
    def _check_sizes(path: str):
        if os.path.isfile(path):
            file_stat = os.stat(path)
            if file_stat.st_size > max_file_size:
                log.info(f'check_size() file over max size. path={path} size={file_stat.st_size}')
                if oversize_handler(path, file_stat, repo):                    
                    uncache_paths.append(path)
        elif os.path.isdir(path):
            for child in os.scandir(path):
                _check_sizes(child.path)
                
    _check_sizes(os.path.join(repo_path, ppath))
    return uncache_paths
    
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
    real_local = os.path.realpath(local_path)
    remote_path = resolve_remote(repo, path["remote"])
     
    if os.path.isfile(local_path):
        # syncing file
        # make parent dir
        mkdir_p(resolve_remote(repo, os.path.dirname(path["remote"])))
        log.info(f'rsync() local_file={local_path} real_local={real_local} remote_file={remote_path}')
    else:
        # syncing directory
        # make directory
        mkdir_p(resolve_remote(repo, path["remote"]))
        if not local_path.endswith('/'):
            local_path += '/'
        if remote_path.endswith('/'):
            remote_path = remote_path[0:-1]
        
        log.info(f'rsync() local_dir={local_path} real_local={real_local} remote_dir={remote_path}')
       
    
    cmd.append(local_path)
    cmd.append(remote_path)
    exec_sh(cmd)
    return remote_path

def git_rm(path: str, repo: RepoConfig, cached: bool = True):
    repo_path = get_repo_path(repo)
    
    cmd = ["git", "rm"]
    if cached:
        cmd.append("--cached")
    cmd.append(path)
    
    log.info(f'git_rm() cmd={" ".join(cmd)}')
    return exec_sh(cmd, cwd=repo_path)
    
def oh_git_lfs(path: str, file_stat: os.stat_result, repo: RepoConfig) -> bool:
    repo_path = get_repo_path(repo)
    rel_path = os.path.join('/', os.path.relpath(path, repo_path))
    exec_sh(['git', 'lfs', 'track', rel_path], repo_path)
    return False

def oh_chunking(path: str, file_stat: os.stat_result, repo: RepoConfig) -> bool:
    chunk_size = repo['max_file_size']
    full_size = file_stat.st_size
    fname = os.path.basename(path)
    chunk_dir = f'{path}.d'
    manifest_path = os.path.join(chunk_dir, 'manifest')
    
    # make directory to hold chunks
    mkdir_p(chunk_dir)
    
    # hash of original file
    hash = hashlib.sha256()
    
    # original oversized file
    f = open(path, 'rb')
    
    chunk = f.read(chunk_size)
    i = 0
    while chunk:
        hash.update(chunk)
        
        chunk_path = os.path.join(chunk_dir, str(i))
        chunk_file = open(chunk_path, "wb")
        chunk_file.write(chunk)
        chunk_file.close()
        
        chunk = f.read(chunk_size)
        i += 1
    f.close()
    
    # update or create manifest
    prev_version = 0
    try:
        with open(manifest_path, 'r', encoding='utf8') as manifest:
            v_line: str = manifest.readline(1)
            if v_line and v_line.startswith('version '):
                prev_version = int(v_line.split(' ')[1].strip())
    except Exception as e:
        if not isinstance(e, IOError) or e.errno != 2:
            log.warn(f'oh_chunking() could not read manifest {e}')
            
    with open(manifest_path, 'w', encoding='utf8') as manifest:
        manifest.write(f'''\
version {prev_version + 1}
name {fname}
oid sha256:{hash.hexdigest()}
size {full_size}
chunks {i}
''')
    return True
    
def get_oversize_handler(handler_t: OversizeHandlerType) -> OversizeHandler:
    if handler_t == "git_lfs":
        return oh_git_lfs
    elif handler_t == "chunking":
        return oh_chunking
    
    log.warn(f'Invalid oversize_handler type: {handler_t}')
    return lambda *_: False
    
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
               
            oversize_handler = get_oversize_handler(repo['oversize_handler'])
            uncache_paths = check_sizes(repo, change_path, oversize_handler)
            
            if repo['oversize_handler'] == 'git_lfs':
                git_add(repo, '.gitattributes')
            git_add(repo, change_path)
            
            for p in uncache_paths:
                git_rm(repo, p, True)
                        
        status = git_status(repo, True)
        if status:
            log.debug(f'sync() git_status: \n{git_status(repo)}')
            log.info(f'sync() git_status (porcelain): \n{status}')
            git_commit(repo)
            git_push(repo)
        else:
            log.info(f'sync() no changes, skipping commit to {repo["owner"]}/{repo["name"]}')