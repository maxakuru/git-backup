from crontab import CronTab

class Cron(CronTab):
    crontab: str
    def __init__(self, crontab: str, loop: bool = False, random_seconds: bool = False) -> None:
        """
        inputs:
            `crontab` - crontab specification of "[S=0] Mi H D Mo DOW [Y=*]"
            `loop` - do we loop when we validate / construct counts
                     (turning 55-5,1 -> 0,1,2,3,4,5,55,56,57,58,59 in a "minutes" column)
            `random_seconds` - randomly select starting second for tasks
        """
        self.crontab = crontab
        super().__init__(crontab, loop, random_seconds)
        
    def __str__(self) -> str:
        return self.crontab