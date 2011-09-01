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

        path = os.path.join(self.paths['schedules'], name)
        expected_args = ('command', 'manager', 'storage_path')
        lines = open(path).readlines()
        args = {}
        manager = None
        
        for line in lines:
            for key in expected_args:
                if line.startswith(key):
                    args[key] = line.split(key)[1].lstrip()
                elif key not in args:
                    args[key] = ''

        if args['command']:
            print '    loaded schedule %s with args %s'%(os.path.basename(name), args)

            if args['manager']:
                arg_manager = args['manager'].split()
                manager_name = arg_manager[0]
                manager_args = arg_manager[1:]

                if manager_name:
                    manager = self._get_manager_by_name(manager_name, manager_args)

        elif len(lines) > 0:
            print '    failed on load schedule %s (oops! where is my backup command ?)'%os.path.basename(name)
        else:
            print "    failed on load schedule %s (oops! i'm empty ?)"%os.path.basename(name)

        return dict(name = name, command = args['command'], manager = manager, storage_path = args['storage_path'])

    def _get_manager_by_name(self, name, args):
      return "#TODO _get_manager (%s, %s)"%(name, args)


    def backup(self, name):
        return self._backup(schedule = self._load_schedule(name))


    def _backup(self, schedule):

        if not schedule.get('command', ''):
            print '    * backup of schedule "%s" aborted, I need a argument called "command" to backup it duuu :P'%schedule.get('name', '')
            return False

        args_helpers = self._get_args_helpers(schedule = schedule)
        args = shlex.split(schedule['command']%args_helpers)
        self._create_dir_if_not_exists(args_helpers['storage_path'])

        result = subprocess.Popen(args).communicate()
        ##return subprocess.check_output(args, stderr = subprocess.STDOUT)
        return result


    def _get_args_helpers(self, schedule):
        args = {
            'now' : strftime("%H-%M-%S_%Y-%m-%d"),
            'storage_path' : schedule.get('storage_path', '').strip()
        }

        args.update({'file' : os.path.join(args['storage_path'], '%s_%s'%(schedule.get('name', ''), args['now']))})
        return args


    def _create_dir_if_not_exists(self, path):
        if not os.path.exists(path):
            return os.makedirs(path)
        return True

if __name__ == '__main__':
    print "Oops, you called me but I'm a lazy script, try to call my friend pg_bakup.py"
