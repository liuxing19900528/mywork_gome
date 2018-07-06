#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import os
import re


def main():
    title=os.environ.get("GERRIT_CHANGE_SUBJECT")
    change_number=os.environ.get("GERRIT_CHANGE_NUMBER")
    patchset_number=os.environ.get("GERRIT_PATCHSET_NUMBER")
    project=os.environ.get("GERRIT_PROJECT")
    commit_message=os.environ.get("GERRIT_CHANGE_COMMIT_MESSAGE")
    commit_message_L=commit_message.splitlines()
    print "=",title,"="
    print "=",commit_message_L,"="

    msg = []
    #try:
    #    unicode(title, "ascii")
    #except Exception:
    #    msg.append("git commit 标题不允许有中文！")

    if len(title) > 150 :
        msg.append("git commit 标题不要超过150个字符长度！")

    if title.endswith("."):
        msg.append("git commit 标题不要点号结尾！")

    if title.endswith(";"):
        msg.append("git commit 标题不要;号结尾！")

    if len(title) > len(commit_message_L[0]):
        msg.append("git commit 标题后面要空一行的！")

    # 检查 jira单号
    if project.startswith("aosp/"):
        print "will check jira ID."
        all_L = re.findall("\[[A-Z0-9]+-[0-9]+\]:|\[fix\]:|\[feat\]:|\[docs\]:|\[style\]:|\[refactor\]:|\[test\]:|\[chore\]:", title)
        #print all_L
        if not all_L:
            msg.append("commit message 标题[]中缺少jira单号，或者[]中关键字不对，或者冒号:后缺少空格!")
        else:
            all_L = re.findall("\[[A-Z0-9]+-[0-9]+\]", title)
            if all_L:
                for jiraidstr in all_L:
                    jiraid = jiraidstr.replace("[", "").replace("]", "")
                    jiranum = jiraid.split("-")[1]
                try:
                    if int(jiranum) <= 0:
                        msg.append("jira id %s 单号不对,怎么能等于零!" % jiraidstr)
                except:
                    msg.append("jira id %s 单号不对!" % jiraidstr)
    if msg:
        message = " ".join(msg)
        message = """Error.
        %s

        commit message 提交规范请参考这里:http://wiki.iuv.com:8090/pages/viewpage.action?pageId=1081639

        """ % message
        cmd = "ssh -p 29418 jira@192.168.59.30 gerrit review --message '\"%s\"' --code-review -2 %s,%s" % (message, change_number, patchset_number)
        print "cmd : %s" % (cmd)
        os.system(cmd)
        ret = 1
    else:
        #填写的标题合法
        msg = """Good.
        第一行不要超过150个字符长度！
        第一行之后要空一行！
        第一行不允许点号结尾！
        """
        cmd = "ssh -p 29418 jira@192.168.59.30 gerrit review --message '\"%s\"' --code-review +1 %s,%s" % (msg, change_number, patchset_number)
        print "cmd : %s" % (cmd)
        os.system(cmd)
        ret = 0

    sys.exit(ret)
if __name__ == "__main__" :
    # need flush print
    sys.stdout = sys.stderr
    main()
