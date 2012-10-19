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

import os.path, shlex, subprocess, json, traceback
from time import strftime


class MsgError(Exception):
    pass


class Logger:
    logs_root_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logs")
    log_path       = os.path.join(logs_root_path, 'log.log')

    @classmethod
    def log(cls, msg):
        print msg

        try:
            if not os.path.exists(cls.logs_root_path):
                os.makedirs(cls.logs_root_path)

            log_file = file(cls.log_path, 'a')
            log_file.write(msg)

        except Exception as detail:
            print "\nOops! Couldn't write the log in file %s, details: %s"%(cls.log_path, detail)

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

        Logger.log("\n* Uploading %s to aws s3 bucket: '%s', key: '%s', Uri: '%s'."%(local_file_path,
                     schedule['aws_s3_bucket_name'], remote_file_path, s3_uri))

        bucket = connection.get_bucket(schedule['aws_s3_bucket_name'])

        remote_file     = Key(bucket)
        remote_file.key = remote_file_path

        remote_file.set_contents_from_filename(local_file_path)
        remote_file_exists = remote_file.exists()

        if remote_file_exists:
          Logger.log("\nYep, backup uploaded to S3.\n")
        else:
          Logger.log("\nOops!, backup not uploaded to S3.\n")

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
            raise MsgError('no %s present with name "%s" :('%(self.settings_type, name))

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
        Logger.log("\n* Loaded credential %s"%name)
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


#TODO extend class Settings
class Backup:

    def __init__(self):
        self.paths = {
            'schedules' : os.path.join(os.path.dirname(os.path.abspath(__file__)), 'schedules'),
        }


    def backup(self, name, options = []):
        Logger.log("\n\n[%s] Starting backup for schedule '%s' with options %s"%(strftime("%H:%M:%S %Y-%m-%d"), name, options))

        schedule = self._load_schedule(name, options)
        args     = shlex.split(schedule['command']%schedule['args_helpers'])

        self._create_dir_if_not_exists(schedule['args_helpers']['storage_path'])

        Logger.log("\n*  Executing backup with command: %s"%" ".join(args))

        subprocess.Popen(args).communicate()
        valid_backup = self._validate_backup(schedule)

        if valid_backup and schedule['aws_s3_credential']:
            AmazonWebServicesS3(schedule['aws_s3_credential']).upload(schedule)


    # TODO alterar arquivo schedules para formato json ?
    def _load_schedule(self, name, options = []):
        path = os.path.join(self.paths['schedules'], name)

        if not os.path.exists(path):
            raise MsgError('failed on load schedule "%s" file not exists :('%name)

        # setup default vars

        required_args = ('command', 'storage_path', 'aws_s3_credential', 'aws_s3_bucket_name', 'aws_s3_storage_key')
        loaded_args   = {}

        lines         = open(path).readlines() + options

        # read args from each line

        for line in lines:
            for arg_name in required_args:
                if line.startswith(arg_name):
                    arg_value             = line.split(arg_name, 1)[1].strip()
                    loaded_args[arg_name] = arg_value


        # validates required args

        not_present_args = set(required_args) - set(loaded_args)

        if not_present_args:
            error_msg = (
                "the args %s are required, but they aren't present in schedule either in received command line options,\n" +
                "please define this args in the schedule or send via command line with syntax -OargName=argValue"
            )%list(not_present_args)

            raise MsgError(error_msg)

        Logger.log("\n* Loaded schedule '%s' with args %s"%(os.path.basename(name), loaded_args))


        # load credentials

        aws_s3_credential = self._get_credential_by_name(loaded_args['aws_s3_credential'])


        # setup schedule with args loaded and return it

        schedule = dict(
            name               = name,
            command            = loaded_args['command'],
            storage_path       = loaded_args['storage_path'],
            aws_s3_credential  = aws_s3_credential,
            aws_s3_bucket_name = loaded_args['aws_s3_bucket_name'],
            aws_s3_storage_key = loaded_args['aws_s3_storage_key']
        )

        schedule['args_helpers'] = self._get_args_helpers(schedule)

        return schedule


    def _get_credential_by_name(self, name):
        return Credential().load(name) if name else None


    def _validate_backup(self, schedule):
        # it validates only if the file size is more than 0, the format of the file isn't validated.
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


if __name__ == '__main__':
    import sys

    args_description = (
        ('postgresql', 'realiza backup de uma base dados postgresql'),
        ('help', 'lista  os comandos disponiveis'),
        ('list', 'lista schedules disponiveis conforme tipo informado')
    )
    expected_args = ('postgresql', 'list', 'help')


    def print_help():
        print 'Usage: backup.py <command> [-OargName=argValue -OargName2=argValue2]'
        print '\nCommandos disponiveis:'
        for a in args_description:
            print '    %s - %s'%(a[0], a[1])


    def backup(args):
        schedule_names = []
        options        = []

        if len(args) < 2:
            print 'Pass the name of one or more schedules'

        b = Backup()

        for arg in args[1:]:
            if arg.startswith('-O'):
                options.append(arg[2:].replace('=', ' '))
            else:
                schedule_names.append(arg)

        for schedule_name in schedule_names:
            try:
                b.backup(schedule_name, options)

            except MsgError as msg:
                Logger.log('** Error: %s\n'%msg)

            except Exception as detail:
                Logger.log("** Oops! Some error ocurred: %s\n"%detail)
                traceback.print_exc()


    def list_schedules():
        raise NotImplementedError


    if len(sys.argv) < 2:
        print_help()
    elif sys.argv[1] not in expected_args:
        print 'Oops!, invalid command "%s"\n'%sys.argv[1]
        print_help()
    elif sys.argv[1] == 'help':
        print_help()
    elif sys.argv[1] == 'list':
        list_schedules()
    elif sys.argv[1] == 'postgresql':
        backup(sys.argv[1:])
