from time import sleep
from git_backup.config import load
from git_backup.sync import sync
from git_backup.types import Config

def run():
    conf = load()
    loop = conf['loop']
    
    if not loop['loop']:
        sync(conf)
    else:
        while True:
            sync(conf)
            
            if 'schedule' in loop:
                sleep(loop['schedule'].next())
            else:
                sleep(loop['interval']*60)

if __name__ == "__main__":
    run()