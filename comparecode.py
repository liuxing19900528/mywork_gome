#!/usr/bin/env python
# coding:utf-8

import os
import sys
import shlex
import subprocess
import shutil
import codecs
import xml.dom.minidom

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

def getAddOrDeletePorjectsInfo(projects):
	project_string = ""
	for p in projects:
		project_string += "%s\n" % (p)
	return project_string   	

def getChangeProjectList(intersectionProjectsInfo, baseProjectDict, currentProjectDict):
	changeProjectList = []
	changeProjectListStr = ""
	for index,project in enumerate(intersectionProjectsInfo):
		projectName = project[0]
		baseProject = baseProjectDict.get(projectName, ["", "", ""])
		currentProject = currentProjectDict.get(projectName, ["", "", ""])
		if baseProject[2] != currentProject[2]:
			changeProjectList.append(project[1])
	for p in changeProjectList:
		changeProjectListStr += "%s\n" % (p)
	return changeProjectListStr
	
	
def getIntersectionProjectsInfo(intersectionProjectsInfo, baseProjectDict, currentProjectDict):
	diff_string = ""
	for index,project in enumerate(intersectionProjectsInfo):
	#[0]:project_name,[1]:local_path, [2]:revision, [3]:upstream, [4]:remote                                                                                                     
		projectName = project[0]
		baseProject = baseProjectDict.get(projectName, ["", "", ""])
		currentProject = currentProjectDict.get(projectName, ["", "", ""])
		if baseProject[2] == currentProject[2]:
			continue

		projectLocalPath = project[1]
		local = os.getcwd()
   		try:
			os.chdir(projectLocalPath)
 		except OSError as e:
			print "chdir fail. %s" % e
			os.chdir(local)
		git_log_cmd = "git --no-pager log --left-right --cherry-pick --date=short --pretty='%%m || %%H ||  %%s (%%an %%ae) (%%cd)' %s...%s" % (baseProject[2], currentProject[2])
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
		diff_string += "project %s\n" % (projectName)
		diff_string += unicode(output[0], "utf-8")
		diff_string += "\n\n"
		os.chdir(local)
	return diff_string

def getIntersectionProjectsPatch(intersectionProjectsInfo, baseProjectDict, currentProjectDict):
	patchPackage = "diff_patch"
	currentPath = os.getcwd()
	patchPath = os.path.join(currentPath, patchPackage)
	#print patchPath
	
	os.makedirs(patchPath)
  
	for index,project in enumerate(intersectionProjectsInfo):
		#[0]:project_name,[1]:local_path, [2]:revision, [3]:upstream, [4]:remote
		projectName = project[0]
		baseProject = baseProjectDict.get(projectName, ["", "", ""])
		currentProject = currentProjectDict.get(projectName, ["", "", ""])
		if baseProject[2] == currentProject[2]:
			#Log.Warning("[%s] %s, same revision project" % (index, right_project[0]))
			continue
  		projectLocalPath = project[1]
		local = os.getcwd()
		try:                                                                                                                                                                         
			os.chdir(projectLocalPath)
		except OSError as e:
			print "chdir fail. %s" % (e)
			os.chdir(local)
  
		patchOutputPath = os.path.join(patchPath, projectLocalPath)
		#print patchOutputPath
		if not os.path.exists(patchOutputPath):
			os.makedirs(patchOutputPath)
		git_patch_cmd = "git format-patch -o %s %s...%s" % (patchOutputPath, baseProject[2], currentProject[2])
		#print git_patch_cmd
		cmd_args = shlex.split(git_patch_cmd)
		#print cmd_args
		proc = subprocess.Popen(cmd_args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
		output = proc.communicate()
		print output[0]
		status = proc.returncode
		#status,output = commands.getstatusoutput(git_patch_cmd)
		if status != 0: 
			print "git format patch fail: %s" % (output[1])
		os.chdir(local)

	os.system("cd %s && tree . -o patch_structure.txt" % (patchPath))
	publish_patch_gztar_file = os.path.join(patchPath)
	shutil.make_archive(publish_patch_gztar_file, "gztar", patchPath)

def doCodeCompare(baseManifest=".repo/baseManifest.xml", currentManifest=".repo/currentManifest.xml"):
	localPath = os.getcwd()
	baseProjects = parseManifest(baseManifest)
	baseProjectDict = {}
	for basePro in baseProjects:
		baseProjectDict[basePro[0]] = basePro
	currentProjects = parseManifest(currentManifest)
	currentProjectDict = {}
	for currentPro in currentProjects:
		currentProjectDict[currentPro[0]] = currentPro
	
	baseOnlyProjects = [p[0] for p in baseProjects]
	currentOnlyProjects = [p[0] for p in currentProjects]
	deleteProjects = [p for p in baseOnlyProjects if p not in currentOnlyProjects]
	addProjects = [p for p in currentOnlyProjects if p not in baseOnlyProjects]
	intersectionProjects = list(set(baseOnlyProjects).intersection(set(currentOnlyProjects)))
	intersectionProjects.sort()
	intersectionProjectsInfo = [currentProjectDict.get(pro) for pro in intersectionProjects]
	intersectionProjectsInfo.sort(key=lambda p:p[0])
	diffString = "---base manifest:%s\n+++current manifest:%s\nAdded/Removed projects:\n========================\n" % (baseManifest, currentManifest)
	diffString += "----------------------------------------\n"
	diffString += getAddOrDeletePorjectsInfo(deleteProjects)
	diffString += "++++++++++++++++++++++++++++++++++++++++\n"
	diffString += getAddOrDeletePorjectsInfo(addProjects)
	diffString += "\n\nChanges in each projects:\n========================\n"
	diffString += getIntersectionProjectsInfo(intersectionProjectsInfo, baseProjectDict, currentProjectDict)
	print diffString
	changeProjectFile = os.path.join(localPath, "diff_project.list")
	patchDiffFile = os.path.join(localPath, "diff_patch_list.diff")
	fd1 = codecs.open(patchDiffFile, "w", encoding="utf-8")
	fd2 = codecs.open(changeProjectFile, "w", encoding="utf-8")
	fd1.write(diffString)
	fd2.write(getChangeProjectList(intersectionProjectsInfo, baseProjectDict, currentProjectDict))
	fd1.close()
	fd2.close()                                                                                                                                                                    
	getIntersectionProjectsPatch(intersectionProjectsInfo, baseProjectDict, currentProjectDict)

if __name__ == "__main__" :
	doCodeCompare(sys.argv[1], sys.argv[2])
