import os.path, shlex, subprocess, json
from time import strftime

class Manager:

    def __init__(self):
        self.paths = {
            'managers' : os.path.join(os.path.dirname(os.path.abspath(__file__)), 'managers')
        }

    def execute_commands(self, commands, schedule):
        def now():
            return strftime("%H:%M:%S-%Y-%m-%d")
        logs = ''        
        logs += '\n* Started commands (at %s):'%now()
        logs += '\n    %s\n\nresults:\n'%('\n    '.join(commands)%schedule['args_helpers'])
        for command in commands:
            args = (command%schedule['args_helpers']).encode('utf8')
            #subprocess.Popen(shlex.split(args)).communicate()
            try:
                result = subprocess.check_output(shlex.split(args), stderr=subprocess.STDOUT)
                logs += ('    %s'%result) if result else ''
            except Exception as e:
                logs+= '\n** Oops! errors ocurred on command "%s":\n        python traceback: %s\n        OS traceback: %s\n'%(args, e, e.output if 'output' in e.__dict__ else '')
        logs += 'Finalized commands at %s\n\n'%now()

        print logs

    def send_emails(self, emails, commands, commands_logs):
        print '#TODO implementar metodo send_emails: %s'%emails


    def on_success(self, schedule):
        commands_logs = self.execute_commands(self.events['on_success']['commands'], schedule = schedule)
        self.send_emails(self.events['on_success']['send_emails_to'], commands = self.events['on_success']['commands'], commands_logs = commands_logs)


    def on_fail(self, schedule):
        raise NotImplementedError


    def load_manager(self, name, args):

        path = os.path.join(self.paths['managers'], name)
        if not os.path.exists(path):
            print '    failed on load manager "%s" file not exists :('%name
            return False

        self.events = json.loads(open(path).read())
        return self    

class Backup:

    def __init__(self):
        self.paths = {
            'schedules' : os.path.join(os.path.dirname(os.path.abspath(__file__)), 'schedules'),
        } 

    
    def _load_schedule(self, name):

        path = os.path.join(self.paths['schedules'], name)
        if not os.path.exists(path):
            print '    failed on load schedule "%s" file not exists :('%name
            return False

        expected_args = ('command', 'manager', 'storage_path')
        lines = open(path).readlines()
        args = {}
        manager = None
        
        #TODO alterar arquivo schedules para formato json 
        for line in lines:
            for key in expected_args:
                if line.startswith(key):
                    args[key] = line.split(key, 1)[1].lstrip()
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

        schedule = dict(name = name, command = args['command'], manager = manager, storage_path = args['storage_path'])
        schedule['args_helpers'] = self._get_args_helpers(schedule)
        return schedule


    def _get_manager_by_name(self, name, args):
        return Manager().load_manager(name, args)


    def backup(self, name):
        schedule = self._load_schedule(name)

        if not schedule:
            print '    * backup of schedule "%s" aborted, invalid schedule :('%name

        elif not schedule.get('command', ''):
            print '    * backup of schedule "%s" aborted, I need a argument called "command" to backup it duuu :P'%name

        else:
            args = shlex.split(schedule['command']%schedule['args_helpers'])
            self._create_dir_if_not_exists(schedule['args_helpers']['storage_path'])

            subprocess.Popen(args).communicate()
            #return subprocess.check_output(args, stderr = subprocess.STDOUT)
        
            if schedule['manager'] and self._validate_backup(schedule):
                schedule['manager'].on_success(schedule)
            elif schedule['manager']:
                schedule['manager'].on_fail(schedule)


    def _validate_backup(self, schedule):
        return os.path.exists(schedule['args_helpers']['file']) and os.path.getsize(schedule['args_helpers']['file']) > 0


    def _get_args_helpers(self, schedule):
        args = {
            'now' : strftime("%H-%M-%S_%Y-%m-%d"),
            'storage_path' : schedule.get('storage_path', '').strip()
        }

        args.update({'file_basename' : '%s_%s.backup'%(schedule.get('name', ''), args['now'])})
        args.update({'file' : os.path.join(args['storage_path'], args['file_basename'])})
        return args


    def _create_dir_if_not_exists(self, path):
        if not os.path.exists(path):
            return os.makedirs(path)
        return True

if __name__ == '__main__':
    print "Oops, you called me but I'm a lazy script, try to call my friend pg_bakup.py"
