from os import stat_result
from typing import TYPE_CHECKING, Callable, List, Literal, Mapping, Optional, Union, TypedDict

from git_backup.cron import Cron

if TYPE_CHECKING:
    from git_backup.secrets import Secrets

CompressType = Union[Literal['zip'], Literal['tar'], Literal['gztar'], Literal['bztar'], Literal['xztar']]

OversizeHandlerType = Union[Literal['git_lfs'], Literal['chunk']]

# (path, file_stat, repo) => rm_from_git_cache
OversizeHandler = Callable[[str, stat_result, 'RepoConfig'], bool]

class PathConfig(TypedDict):
    local: str
    remote: str
    compress: Optional[CompressType]
    branch: Optional[str]
    
class GitConfig(TypedDict):
    add: Optional[bool] # default True
    commit: Optional[bool] # default True
    push: Optional[bool] # default True
    force_push: Optional[bool] # default False
    message: Optional[str] # default `chore(backup): update backup`
    email: Optional[str]
    name: Optional[str]

    
class RepoConfig(TypedDict):
    name: str
    owner: str
    storage_root: str
    endpoint: Optional[str]
    paths: List[PathConfig]
    branch: Optional[str]
    git: GitConfig
    max_file_size: int # bytes
    oversize_handler: OversizeHandlerType
    
class RepoSecrets(TypedDict):
    token: Optional[str]
    
# { owner -> { repo -> RepoSecrets}}    
SecretsConfig = Mapping[str, Mapping[str, RepoSecrets]]

class LoopConfig(TypedDict):
    loop: bool # whether to loop
    interval: float # minutes, default=1440 (1 day)
    schedule: Optional[Cron]
    
class StorageConfig(TypedDict):
    repo_root: str
    
class RSyncConfig(TypedDict):
    archive: bool

class Config(TypedDict):
    version: int
    storage: StorageConfig
    rsync: RSyncConfig
    repos: List[RepoConfig]
    secrets: 'Secrets'
    loop: LoopConfig