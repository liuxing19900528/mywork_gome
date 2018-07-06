#!/bin/bash

set -e -o nounset
currentDate=`date "+%Y-%m-%d-%H-%M-%S"`

function downloadCode()
{
	
	GIT_SERVER_IP=192.168.59.30
	GIT_SERVER_PORT=29418
	MANIFEST_PATH=aosp/gome/manifest
	LOCAL_MIRROR=/home/sh-mirror
	echo "-------------------------start download code-----------------------------------------"
	echo "repo init -u ssh://$GIT_SERVER_IP:$GIT_SERVER_PORT/$MANIFEST_PATH -b $branch --no-repo-verify --reference=$LOCAL_MIRROR"
	echo "-------------------------------------------------------------------------------------"

	repo init -u ssh://$GIT_SERVER_IP:$GIT_SERVER_PORT/$MANIFEST_PATH -b $branch --no-repo-verify --reference=$LOCAL_MIRROR
	repo sync -c -d -j8 --no-tags
	echo "-------------------------start save manifest------------------------------------------"	
	repo manifest -o manifest.xml -r
}

function createReleaseNote()
{
	echo "-------------------------start generate releasenote------------------------------------------"
    lastBuildStr=`cat /mnt/$product"_"$branch"_"$CIB_S_VARIANT.txt`
    lastManifest="/mnt/dailybuild/$product/$branch/$lastBuildStr/manifest.xml"
    python ~/jenkins/workspace/scm_tools/releasenote.py $lastManifest manifest.xml
    python3 ~/jenkins/workspace/scm_tools/json2html3.py
}

function setVerNum()
{
	echo "-------------------------start set version number------------------------------------------"
	verNumString=`echo $currentDate | sed 's/-//g'`
	verNumDate=${verNumString:2:6}

	dailyVerNum=$versionNum"_"$verNumDate
	userdebug_dailyVerNum=$versionNum"_userdebug_"$verNumDate
	eng_dailyVerNum=$versionNum"_eng_"$verNumDate
	#if [ ! -n "$versionNum" ]; then
	if [ "$CIB_S_VARIANT" = "user" ]; then
		sed -i 's/$BUILD_DISPLAY_ID/'"$dailyVerNum"'/' build/tools/buildinfo.sh
		sed -i 's/$BUILD_NUMBER/'"$dailyVerNum"'/' build/tools/buildinfo.sh
	elif [ "$CIB_S_VARIANT" = "userdebug" ]; then
		sed -i 's/$BUILD_DISPLAY_ID/'"$userdebug_dailyVerNum"'/' build/tools/buildinfo.sh
		sed -i 's/$BUILD_NUMBER/'"$userdebug_dailyVerNum"'/' build/tools/buildinfo.sh
	elif [ "$CIB_S_VARIANT" = "eng" ]; then
		sed -i 's/$BUILD_DISPLAY_ID/'"$eng_dailyVerNum"'/' build/tools/buildinfo.sh
		sed -i 's/$BUILD_NUMBER/'"$eng_dailyVerNum"'/' build/tools/buildinfo.sh
	else
		echo "wrong CIB_S_VARIANT, please set user||uerdebug||eng"
	fi
}

get_cpu_number(){
	local L_CPU_NUM=$(grep -c processor /proc/cpuinfo)
	L_CPU_NUM=${AAIS_CPU_NUM:-$L_CPU_NUM}
	echo $L_CPU_NUM
}

function compile()
{
	echo "-------------------------start compile------------------------------------------"
	local L_CPU_NUM=$(get_cpu_number)
	source build/envsetup.sh
	lunch "full"_$product"-"$CIB_S_VARIANT
	#make update-api
	make -j $L_CPU_NUM 2>&1 | tee build.log

	#grep "completed successfully" build.log 1>/dev/null
	#if [ $? -ne 0 ];then
	#	exit 1
	#else
	#	echo "**********************************************compile android ok ok ok ok!****************************************************"
	#fi
	makeeeee -j20
	if $otaTargetFiles; then
		echo "-------------------------start compile otapackage------------------------------------------"
		make otapackage -j $L_CPU_NUM
 	else
		echo "-------------------------start compile otapackage------------------------------------------"
 		echo "don't need to buildotapackage"
	fi
}

function make_ota_package()
{
if $otaTargetFiles; then
	make otapackage -j20
else
	echo "don't need to buildotapackage"
fi
}

downloadCode
createReleaseNote
setVerNum
compile
