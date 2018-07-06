#!/usr/bin/python
# coding:utf-8
import os
import xml.dom.minidom


class ManifestXml(object):
    def __init__(self, env):
        self.android_env = env

        self.git_server = self.android_env.GIT_SERVER
        self.git_manifest_path = self.android_env.REPO_MANIFEST_ADDR
        self.git_manifest_root = "/".join(os.path.dirname(self.git_manifest_path).split("/")[3:])
        self.git_android_root = ["git/android/", "m0/"]
        self.SetGitAndroidRoot(self.android_env.GIT_ANDROID_ROOT)

    def SetGitAndroidRoot(self, path):
        root = path.split(",")
        root.extend(self.git_android_root)
        root = list(set(root))
        if "" in root:
            root.remove("")
        self.git_android_root = root

    def RemoveWhitespceNodes(self, node):
        # delete whiltespace test node in xml file, more detail can see <python cookbook> charpter 12.6
        remove_list = []
        for child in node.childNodes:
            if child.nodeType == node.TEXT_NODE and not child.data.strip():
                remove_list.append(child)
            elif child.hasChildNodes():
                self.RemoveWhitespceNodes(child)

        for node in remove_list:
            node.parentNode.removeChild(node)
            node.unlink()

    def UpdateManifestBranchName(self, manifest, newmanifest, newbranch):
        # update default tag revision to newbranch name,then delete projects tag revision
        try:
            tree = xml.dom.minidom.parse(manifest)
        except Exception as e:
            return 1
        self.RemoveWhitespceNodes(tree)

        root = tree.documentElement
        default = root.getElementsByTagName("default")
        projects = root.getElementsByTagName("project")
        default[0].setAttribute("revision", newbranch)
        for pro in projects:
            try:
                pro.removeAttribute("revision")
                pro.removeAttribute("upstream")
            except xml.dom.NotFoundErr as e:
                pass

        writer = open(newmanifest, "w")
        tree.writexml(writer, indent="", addindent="  ", newl="\n", encoding="UTF-8")
        writer.close()


    def ParseManifest(self, manifest=".repo/manifest.xml"):
        # parse manifest.xml file,return a list [name, path, revision, upstream]
        try:
            tree = xml.dom.minidom.parse(manifest)
        except Exception as e:
            return []
        root = tree.documentElement
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
            projects_L.append(pro_L)
        projects_L.sort()
        return projects_L

