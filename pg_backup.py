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

from backup import Backup

if __name__ == '__main__':
    import sys
    b = Backup()
    for a in sys.argv[1:]:
        b.backup(a)
    if len(sys.argv) < 2:
        print 'Hey!!! I want to work ok? pass me the name of one or more schedules :P'
