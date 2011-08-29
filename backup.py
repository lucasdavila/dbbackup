import os.path, shlex, subprocess
from time import strftime

class Backup:

    def __init__(self):
        p = os.path.dirname(os.path.abspath(__file__))
        self.paths = {
            'schedules' : os.path.join(p, 'schedules'),
            'managers' : os.path.join(p, 'managers')
        } 

    
    def _load_schedule(self, name):

        def get_manager_info(line_manager):
            info = dict(name = '', args = '')

            infos = line_manager.split('#')
            if len(infos) < 1:
                print "        failed on load manager %s :("%os.path.basename(s)
                return info
            elif len(line_manager) > 1:
                info['args'] = infos[1].strip()

            info['name'] = infos[0].strip()
            return info

        path = os.path.join(self.paths['schedules'], name)
        lines = open(path).readlines()
        if len(lines) > 1:
            print '    loaded %s'%os.path.basename(name)
        elif len(lines) > 0:
            print '    loaded %s (without manager)'%os.path.basename(name)
        else:
            print '    failed on load %s (oops! schedule is empty)'%os.path.basename(name)

        if len(lines) > 1:
            manager_info = get_manager_info(lines[1])      
            manager = self._get_manager_by_name(manager_info['name'], manager_info['args']) if manager_info['name'] else None
        else:
            manager = None

        return dict(name = name, args = lines[0].strip(), manager = manager)

    def _get_manager_by_name(self, name, args):
      return "#TODO _get_manager (%s, %s)"%(name, args)


    def backup(self, name):
        return self._backup(schedule = self._load_schedule(name))

    def _backup(self, schedule):
        raise NotImplementedError

    def _get_args_helpers(self):
        return dict(now = strftime("%H%M%S-%Y%m%d"))


class PgBackup(Backup):

    def _backup(self, schedule):
        print '\nrunning backup %s with args "%s"\n'%(schedule['name'], schedule['args'])
        args = shlex.split(schedule['args']%self._get_args_helpers())
        result = subprocess.Popen(args).communicate()
        ##return subprocess.check_output(args, stderr = subprocess.STDOUT)
        return result

b = PgBackup()
b.backup('backup_name')
