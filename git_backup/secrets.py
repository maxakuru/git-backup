from typing import Optional
from git_backup.types import SecretsConfig


class Secrets:
    data: SecretsConfig
    
    def __init__(self, data: SecretsConfig) -> None:
        self.data = data
        
    def get_secret(self, owner: str, repo: str, key: str) -> Optional[str]:
        try:
            return self.data[owner][repo][key]
        except:
            return None
        
    def get_token(self, owner: str, repo: str) -> Optional[str]:
        return self.get_secret(owner, repo, 'token')