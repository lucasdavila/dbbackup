# -*- coding: utf-8 -*-
"""
Copyright (c) 2011 Lucas D'Avila - email <lucassdvl@gmail.com> / twitter @lucadavila

This file is part of pgbackup.

pgbackup is free software: you can redistribute it and/or modify
it under the terms of the GNU Lesser General Public License (LGPL v3) as published by
the Free Software Foundation, on version 3 of the License.

pgbackup is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with pgbackup.  If not, see <http://www.gnu.org/licenses/>.
"""

import os.path, shlex, subprocess, json
from time import strftime

class Logger:

    logs_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logs")
    log_path = os.path.join(logs_path, strftime("%Y-%m-%d"))

    @classmethod
    def write(cls, msg, new_lines = 2):
        msg = "%s%s"%("\n" * new_lines, msg)

        print msg
        try:
            if not os.path.exists(cls.logs_path):
                os.makedirs(cls.logs_path)

            log_file = file(cls.log_path, 'a')
            log_file.write(msg)
        except Exception as detail:
            print "Oops! Could not write the log in file %s, details: %s"%(cls.log_path, detail)
        finally:
            log_file.close()


class AmazonWebServicesS3:
    def __init__(self, credentials = {}):
        self.access_key = credentials.get('aws_s3_access_key')
        self.secret_key = credentials.get('aws_s3_secret_key')


    def upload(self, schedule):
        from boto.s3.connection import S3Connection
        from boto.s3.key import Key

        local_file_path  = schedule['args_helpers']['file']
        remote_file_path = os.path.join(schedule['aws_s3_storage_key'], os.path.basename(local_file_path))

        connection       = S3Connection(self.access_key, self.secret_key)
        s3_uri           = "%s://%s:%s%s"%(connection.protocol, connection.host, connection.port, connection.get_path())

        Logger.write("* Uploading %s to aws s3 bucket: '%s', key: '%s', Uri: '%s'."%(local_file_path,
                     schedule['aws_s3_bucket_name'], remote_file_path, s3_uri))

        bucket = connection.get_bucket(schedule['aws_s3_bucket_name'])

        remote_file     = Key(bucket)
        remote_file.key = remote_file_path

        remote_file.set_contents_from_filename(local_file_path)
        remote_file_exists = remote_file.exists()

        if remote_file_exists:
          Logger.write("    Yep, backup uploaded to S3.")
        else:
          Logger.write("    Oops!, backup not uploaded to S3.")

        connection.close()
        return remote_file_exists


class Settings:

    def __init__(self, settings_type):
          self.settings_type = settings_type

          self.paths = {
              'root' : os.path.join(os.path.dirname(os.path.abspath(__file__)), self.settings_type)
          }


    def validates_existence_of(self, name):
        if not os.path.exists(self.get_path_for(name)):
            Logger.write('    %s not exists in path "%s" :('%(self.settings_type, name))
            return False
        return True


    def get_path_for(self, name):
        return os.path.join(self.paths['root'], name)


    def load(self):
        raise NotImplementedError


class Credential(Settings):

    def __init__(self):
        Settings.__init__(self, 'credentials')


    def load(self, name):
        return self._load(name) if self.validates_existence_of(name) else False


    def _load(self, name):
        Logger.write("* Loaded credential %s"%name)
        expected_args = ('aws_s3_access_key', 'aws_s3_secret_key')

        lines = open(self.get_path_for(name)).readlines()
        args = {}

        for line in lines:
            for key in expected_args:
                if line.startswith(key):
                    args[key] = line.split(key, 1)[1].strip()
                elif key not in args:
                    args[key] = ''

        return args


class Manager(Settings):

    def __init__(self):
        Settings.__init__(self, 'managers')


    def execute_commands(self, commands, schedule):
        Logger.write('* Started managers commands')

        for command in commands:
            args = (command % schedule['args_helpers']).encode('utf8')
            try:
                Logger.write('    Executing: %s'%args, 0)
                Logger.write('    %s'%(subprocess.check_output(shlex.split(args), stderr=subprocess.STDOUT) or ''), 0)
            except Exception as e:
                Logger.write('** Oops! errors ocurred :(\n        python traceback: %s\n        OS traceback: %s\n'%(args, e, e.output if 'output' in e.__dict__ else ''), 0)

        Logger.write('    Finalized commands', 1)


    def send_emails(self, emails, commands, commands_logs):
        print '\n* #TODO implementar metodo send_emails: %s'%emails


    def on_success(self, schedule):
        commands_logs = self.execute_commands(self.events['on_success']['commands'], schedule = schedule)
        self.send_emails(self.events['on_success']['send_emails_to'], commands = self.events['on_success']['commands'], commands_logs = commands_logs)


    def on_fail(self, schedule):
        raise NotImplementedError


    def load(self, name):
        if self.validates_existence_of(name):
            self.events = json.loads(open(self.get_path_for(name)).read())
            return self
        else:
            return False

#TODO herdar classe Settings
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

        expected_args = ('command', 'manager', 'storage_path', 'aws_s3_credential', 'aws_s3_bucket_name', 'aws_s3_storage_key')
        lines = open(path).readlines()
        args = {}
        manager = None

        #TODO alterar arquivo schedules para formato json ?
        for line in lines:
            for key in expected_args:
                if line.startswith(key):
                    args[key] = line.split(key, 1)[1].strip()
                elif key not in args:
                    args[key] = ''

        if args['command']:
            Logger.write('* Loaded schedule %s with args %s'%(os.path.basename(name), args))

            if args['manager']:
                arg_manager = args['manager'].split()
                manager_name = arg_manager[0]
                manager_args = arg_manager[1:]

                if manager_name:
                    manager = self._get_manager_by_name(manager_name)

            aws_s3_credential = self._get_credential_by_name(args['aws_s3_credential'])

        elif len(lines) > 0:
            Logger.write('    failed on load schedule %s (oops! where is my backup command ?)'%os.path.basename(name))
        else:
            Logger.write("    failed on load schedule %s (oops! I'm empty ?)"%os.path.basename(name))

        schedule = dict(name = name,
                        command = args['command'],
                        manager = manager,
                        storage_path = args['storage_path'],
                        aws_s3_credential = aws_s3_credential,
                        aws_s3_bucket_name = args['aws_s3_bucket_name'],
                        aws_s3_storage_key = args['aws_s3_storage_key']
                        )
        schedule['args_helpers'] = self._get_args_helpers(schedule)

        return schedule


    def _get_manager_by_name(self, name):
        return Manager().load(name)


    def _get_credential_by_name(self, name):
        return Credential().load(name) if name else None


    def backup(self, name):
        Logger.write("Starting backup for schedule %s"%name)

        schedule = self._load_schedule(name)
        if not schedule:
            Logger.write('    * backup of schedule "%s" aborted, invalid schedule :('%name)

        elif not schedule.get('command', ''):
            Logger.write('    * backup of schedule "%s" aborted, I need a argument called "command" to backup it duuu :P'%name)

        else:
            args = shlex.split(schedule['command']%schedule['args_helpers'])
            self._create_dir_if_not_exists(schedule['args_helpers']['storage_path'])

            Logger.write("*  Executing backup with command: %s\n"%" ".join(args))
            subprocess.Popen(args).communicate()
            #return subprocess.check_output(args, stderr = subprocess.STDOUT)

            valid_backup = self._validate_backup(schedule)

            if valid_backup and schedule['aws_s3_credential']:
              AmazonWebServicesS3(schedule['aws_s3_credential']).upload(schedule)

            #TODO replace manager by email_settings in schedules?
            if valid_backup and schedule['manager']:
                schedule['manager'].on_success(schedule)
            elif schedule['manager']:
                schedule['manager'].on_fail(schedule)

    def _validate_backup(self, schedule):
        # validates only existence of file with size > 0.
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
    import sys
    args_description = (
        ('postgresql', 'realiza backup de uma base dados postgresql'),
        ('help', 'lista  os comandos disponiveis'),
        ('list', 'lista schedules e managers disponiveis conforme tipo informado')
    )
    expected_args = ('postgresql', 'list', 'help')

    def print_help():
        print 'Usage: backup.py <command>'
        print '\nCommandos disponiveis:'
        for a in args_description:
            print '    %s - %s'%(a[0], a[1])


    def backup(args):
        if len(args) < 2:
            print 'Pass the name of one or more schedules'
        b = Backup()
        for a in args[1:]:
            try:
                b.backup(a)
            except Exception as detail:
                print "Oops! Some error has occurred. Errors logged."
                Logger.write(detail)


    def list_schelules_and_managers():
        raise NotImplementedError

    if len(sys.argv) < 2:
        print_help()
    elif sys.argv[1] not in expected_args:
        print 'Oops!, invalid command "%s"\n'%sys.argv[1]
        print_help()
    elif sys.argv[1] == 'help':
        print_help()
    elif sys.argv[1] == 'list':
        list_schelules_and_managers()
    elif sys.argv[1] == 'postgresql':
        backup(sys.argv[1:])
