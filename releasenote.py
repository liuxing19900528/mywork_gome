#!/usr/bin/env python
# coding:utf-8

import os
import sys
import shlex
import subprocess
import shutil
import codecs
import xml.dom.minidom

def getRemote(manifest=".repo/manifest.xml"):
    ip = "192.168.59.30"  # default ip
    xmltree = xml.dom.minidom.parse(manifest)

    root = xmltree.documentElement
    remotes = root.getElementsByTagName("remote")
    if len(remotes) <= 0:
        pass
    else:
        fetch = remotes[0].getAttribute("fetch")
        if fetch == "../../NJ/AOSP":
            ip = "192.168.63.217"
    return ip


def parseManifest(manifest=".repo/manifest.xml"):
    xmltree = xml.dom.minidom.parse(manifest)

    root = xmltree.documentElement

    projects = root.getElementsByTagName("project")
    remotes = root.getElementsByTagName("remote")
    default = root.getElementsByTagName("default")
    defaultremote = default[0].getAttribute("remote")
    defaultrevision = default[0].getAttribute("revision")

    remotename_to_fetch = {}
    for remote in remotes:
        name = remote.getAttribute("name")
        fetch = remote.getAttribute("fetch")
        remotename_to_fetch[name] = fetch

    projects_L = []
    for pro in projects:
        path = pro.getAttribute("path")
        name = pro.getAttribute("name")
        revision = pro.getAttribute("revision")
        upstream = pro.getAttribute("upstream")
        remote = pro.getAttribute("remote")
        if revision == "":
            revision = defaultrevision
        if not path:
            path = name
        if not remote:  # this will use default remote
            fetch = remotename_to_fetch.get(defaultremote)
        else:
            fetch = remotename_to_fetch.get(remote)
        # project name in manifest,project path in local, revision, upstream, fetch path.
        pro_L = [name, path, revision, upstream, fetch]
        #print pro_L
        projects_L.append(pro_L)
    projects_L.sort()
    return projects_L

def getCommitId(intersectionProjectsInfo, lastProjectDict, currentProjectDict):
    remote_ip = getRemote(sys.argv[2]) 
    diffCommitIdDict = {}
    jsonFile = open('commit.json','w+')
    for index,project in enumerate(intersectionProjectsInfo):
    #[0]:project_name,[1]:local_path, [2]:revision, [3]:upstream, [4]:remote                                                                                                     
        projectName = project[0]
        lastProject = lastProjectDict.get(projectName, ["", "", ""])
        currentProject = currentProjectDict.get(projectName, ["", "", ""])
        if lastProject[2] == currentProject[2]:
            continue

        projectLocalPath = project[1]
        local = os.getcwd()
        try:
            os.chdir(projectLocalPath)
        except OSError as e:
            print "chdir fail. %s" % e
            os.chdir(local)
        #git_log_cmd = "git --no-pager log --left-right --cherry-pick --date=short --pretty='%%m || %%H ||  %%s (%%an %%ae) (%%cd)' %s...%s" % (lastProject[2], currentProject[2])
        git_log_cmd = "git --no-pager rev-list %s...%s" % (lastProject[2], currentProject[2])
        #print git_log_cmd
        cmd_args = shlex.split(git_log_cmd)
        #print cmd_args 
        proc = subprocess.Popen(cmd_args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        output = proc.communicate()
        #print "project %s" % (projectName)
        #print output[0]
        status = proc.returncode
        if status != 0:
            print "git log fail: %s" % (output[1])
        commitIdList = output[0].strip().split('\n')
        diffCommitIdDict[projectName] = commitIdList
        #print diffCommitIdDict[projectName]

        for commitid in diffCommitIdDict[projectName]: 
            gerrit_query_cmd = "ssh -p 29418 %s gerrit query --format=JSON commit:%s" % (remote_ip,commitid)
            cmd_args = shlex.split(gerrit_query_cmd)
            proc = subprocess.Popen(cmd_args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            output = proc.communicate()
            status = proc.returncode
            if status != 0:
                print "gerrit query fail: %s" % (output[1])
            jsonFile.write(output[0])
        jsonFile.close
        os.chdir(local)

if __name__ == "__main__" :
	lastManifest = sys.argv[1]
	lastProjects = parseManifest(lastManifest)
	lastProjectDict = {}
	for lastPro in lastProjects:
		lastProjectDict[lastPro[0]] = lastPro
		#print lastProjectDict[lastPro[0]]

	currentManifest = sys.argv[2]
	currentProjects = parseManifest(currentManifest)
	currentProjectDict = {}
	for currentPro in currentProjects:
		currentProjectDict[currentPro[0]] = currentPro
		#print currentProjectDict[currentPro[0]]

	lastOnlyProjects = [p[0] for p in lastProjects]
	currentOnlyProjects = [p[0] for p in currentProjects]
	#deleteProjects = [p for p in baseOnlyProjects if p not in currentOnlyProjects]
	#addProjects = [p for p in currentOnlyProjects if p not in baseOnlyProjects]
	intersectionProjects = list(set(lastOnlyProjects).intersection(set(currentOnlyProjects)))
	intersectionProjects.sort()
	intersectionProjectsInfo = [currentProjectDict.get(pro) for pro in intersectionProjects]
	getCommitId(intersectionProjectsInfo, lastProjectDict, currentProjectDict)
	#print intersectionProjectsInfo
