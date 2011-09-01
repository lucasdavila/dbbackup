from backup import Backup

if __name__ == '__main__':
    import sys
    b = Backup()
    for a in sys.argv[1:]:
        b.backup(a)
    if len(sys.argv) < 2:
        print 'Hey!!! I want to work ok? pass me the name of one or more schedules :P'
