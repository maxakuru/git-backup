from typing import TYPE_CHECKING, Callable, List, Literal, Mapping, Optional, Union, TypedDict
from crontab import CronTab

if TYPE_CHECKING:
    from git_backup.secrets import Secrets

CompressType = Union[Literal['zip'], Literal['tar'], Literal["gztar"], Literal["bztar"], Literal["xztar"]]

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
    
class RepoSecrets(TypedDict):
    token: Optional[str]
    
# { owner -> { repo -> RepoSecrets}}
SecretsConfig = Mapping[str, Mapping[str, RepoSecrets]]

class LoopConfig(TypedDict):
    loop: bool # whether to loop
    interval: float # minutes, default=1440 (1 day)
    schedule: Optional[CronTab]
    
class StorageConfig(TypedDict):
    repo_root: str

class Config(TypedDict):
    storage: StorageConfig
    repos: List[RepoConfig]
    secrets: 'Secrets'
    loop: LoopConfig