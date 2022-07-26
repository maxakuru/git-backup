from logging import Logger, getLogger

PREFIX = 'git_backup'

def get_root_logger() -> Logger:
    return getLogger(f'{PREFIX}')

def get_logger(name: str) -> Logger:
    return getLogger(f'{PREFIX}.{name}')