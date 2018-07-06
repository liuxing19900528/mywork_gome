#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys

shGerritServerIp = "192.168.59.30"
userName = "liuxing"
serverPort = "29418"

allProjectObj = open('allProjectList.list', 'r')

allProjectStr = allProjectObj.read().strip('\n')
allProject_L = allProjectStr.split('\n')

allProjectObj.close()

for i, project in enumerate(allProject_L):
    print "%s: %s" % (i+1, project)
    cmd = "ssh -p %s %s@%s gerrit set-project --submit-type REBASE_IF_NECESSARY %s" % (serverPort, userName, shGerritServerIp, project)
    print cmd
    ret = os.system(cmd)
    if ret == 0:
        print "change submit-type to  REBASE_IF_NECESSARY sucessed"
    else:
        break
