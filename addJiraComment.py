#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import re
from jira import JIRA

def main():
    jiraBaseUrl = "http://192.168.59.239:8090"
    jira = JIRA(jiraBaseUrl, basic_auth=('gerrit', 'gerrit'))
    title = os.environ.get("GERRIT_CHANGE_SUBJECT")
    gerritUrl = os.environ.get("GERRIT_CHANGE_URL")
    gerritProject = os.environ.get("GERRIT_PROJECT")
    gerritPatchsetUploader = os.environ.get("GERRIT_PATCHSET_UPLOADER_NAME")
    commentString = "Code-Review: %s\nProject: %s\nCommitter: %s" % (gerritUrl, gerritProject, gerritPatchsetUploader)
    all_L = re.findall("\[[A-Z0-9]+-[0-9]+\]", title)
    if all_L:
        for jiraidstr in all_L:
            jiraid = jiraidstr.replace("[", "").replace("]", "")
            jiraUrl = "%s/browse/%s" % (jiraBaseUrl,jiraid)
            comment = jira.add_comment(jiraid, commentString)
            print "add gerritUrl to %s succeed" % (jiraUrl)
            ret = 0
    else:
        print "标题中不包含有效的jiraid"
        ret = 1
    sys.exit(ret)

if __name__ == "__main__" :
    main()
