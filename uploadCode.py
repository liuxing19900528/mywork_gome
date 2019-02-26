#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import commands
import subprocess
import xml.dom.minidom

from log import Log

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
    #print projects_L
    return projects_L

def getNewProject(projects_L, allProjects="allProjects.list"):
	allProjectsObj = open(allProjects, 'r')
	allProjectsStr = allProjectsObj.read().strip('\n')
	allProjects_L = allProjectsStr.split('\n')
	newProjects_L = []
	for project in projects_L:
		if project[0] not in allProjects_L:
			newProjects_L.append(project[0])
			#print project[0]
	return newProjects_L

def createNewProject(newProjects_L):
	createErrorObject = open('create_fail.log', 'w')
	for i, newProject in enumerate(newProjects_L):
		createProjectCmd = "ssh -p %s %s@%s gerrit create-project %s%s --empty-commit --submit-type REBASE_IF_NECESSARY" % (serverPort, userName, shGerritServerIp, projectNamePrefix, newProject)
		status,output = commands.getstatusoutput(createProjectCmd)
		if status != 0:
			Log.Error("[%s] create %s fail: %s" % (i+1, newProject, output))
			createErrorObject.write("[%s] create %s fail: %s\n" % (i+1, newProject, output))
		else:
			print "[%s]new project:%s\n%s\n" % (i+1, newProject, createProjectCmd)
	createErrorObject.close()

def intGitRepository(projects_L):
	for i, project in enumerate(projects_L):
		try:
			os.chdir("%s/%s" % (localPath, project[1]))
			print "[%s]: %s" % (i+1, os.getcwd())
 		except OSError as e:
 			Log.Warning("chdir failed: %s" % e)
			continue
		gitInitCmd = "git init"
		#Log.Green("[index:%s] %s\n" % (i+1, gitInitCmd))
		status,output = commands.getstatusoutput(gitInitCmd)
		if status != 0:
 			Log.Error("[%s]: %s" % (project, output))
		gitAddCmd = "git add -f -A"
		#Log.Green("[index:%s] %s\n" % (i+1, gitAddCmd))
		status,output = commands.getstatusoutput(gitAddCmd)
 		if status != 0:
 			Log.Error("[%s]: %s" % (project, output))
		gitCommitCmd = "git commit --allow-empty -m \"init %s\"" % newBranch
		#Log.Green("[index:%s] %s\n" % (i+1, gitCommitCmd))
		status,output = commands.getstatusoutput(gitCommitCmd)
		if status != 0:
			Log.Error("[%s]: %s" % (project, output))

def pushToServer(projects_L):
	errorPushObject = open('push_fail30.log', 'w')
	for i, project in enumerate(projects_L):
		try:
			os.chdir("%s/%s" % (localPath, project[1]))
			#print "[%s]: %s" % (i+1, os.getcwd())
		except OSError as e:
			Log.Error("chdir failed: %s" % e)
			continue
		pushCmd = "git push ssh://%s@%s:%s/%s%s HEAD:refs/heads/%s" % (userName, shGerritServerIp, serverPort, projectNamePrefix, project[0], newBranch)
		#print pushCmd
		status,output = commands.getstatusoutput(pushCmd)
		if status != 0:
			print "[%s]:%s push failed: %s" % (i+1, project[0], output)
			errorPushObject.write("[%s]:%s push failed: %s\n" % (i+1, project[0], output))
		else:
			print "[index:%s project:%s]\n%s\n" % (i+1, project[0], pushCmd)
	errorPushObject.close()

if __name__ == "__main__":
	shGerritServerIp = "192.168.59.100000"
 	userName = "liuxing"
	serverPort = "29418"
 	projectNamePrefix = "aosp/"
 	#projectNamePrefix = ""
 	localPath = os.getcwd()
 	newBranch = "alps-release-o1-mp1"

	projects_L = parseManifest(manifest="alps-release-o1.mp1-default.xml")
	newProjects_L = getNewProject(projects_L, allProjects="sh_all_projects.list")
	#print newProjects_L
	#createNewProject(newProjects_L)
	#intGitRepository(projects_L)
	pushToServer(projects_L)
