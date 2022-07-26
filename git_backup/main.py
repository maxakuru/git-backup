from time import sleep
from git_backup.config import load
from git_backup.sync import sync

from logging import Logger
log = Logger('main')

def run():
    log.info('starting up')
    conf = load()
    log.info('loaded config')
    
    loop = conf['loop']
    
    if not loop['loop']:
        log.info('running single sync')
        sync(conf)
    else:
        scheduled = 'schedule' in loop
        if scheduled:
            log.info(f'running on schedule: {loop["schedule"].crontab}')
        else:
            log.info(f'running in loop every {loop["interval"]} minutes')
            
        while True:   
            log.debug('start sync')      
            sync(conf)
            
            if scheduled:
                sleep(loop['schedule'].next())
            else:
                sleep(loop['interval']*60)

if __name__ == "__main__":
    run()