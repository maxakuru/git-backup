from time import sleep
import traceback
from typing import Any, Callable, List

from git_backup.config import load
from git_backup.sync import sync
from git_backup.logger import get_logger

log = get_logger('main')

def backoff(fn: Callable, args: List[Any], timeout: int = 60*60, delay: int = 100):
    attempt = 0
    timer = 0
    while timer < timeout:
        try:  
            return fn(*args)
        except Exception as e:
            log.error(f'ERROR: back_off({attempt}) Unhandled exception: \n{traceback.format_exc()}')
            attempt += 1
            delay *= 2
            timer += delay
            if timer > timeout:
                break
            sleep(delay)
    log.error(f'ERROR: timeout while attempting to backoff call')

def run():
    log.info('starting up')
    conf = load()
    log.info('loaded config')
    
    loop = conf['loop']
    
    if not loop['loop']:
        log.info('running single sync')
        backoff(sync, [conf])
    else:
        scheduled = 'schedule' in loop
        if scheduled:
            log.info(f'running on schedule: {loop["schedule"].crontab}')
        else:
            log.info(f'running in loop every {loop["interval"]} minutes')
            
        while True:   
            if scheduled:
                t = loop['schedule'].next()
                log.info(f'next sync in {t} seconds')
                sleep(t)
                log.info('start sync')
                backoff(sync, [conf])
            else:
                log.info('start sync')
                backoff(sync, [conf])
                t = loop['interval']*60
                log.info(f'next sync in {t} seconds')
                sleep(t)

if __name__ == "__main__":
    run()