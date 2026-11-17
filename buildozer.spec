[app]
android.extra_manifest_application_xml = ./android/extra_manifest_application_xml.xml
p4a.branch = develop
p4a.commit = 32994bea648eddf6808477ac91cd74632287a7fe
android.add_src = ./android/src
title = BackTrack5
package.name = bactrack5
package.domain = org.backtrack5
source.dir = app
source.include_exts = py,kv,png,jpg,jpeg,atlas,json,ttf
version = 0.1
requirements = python3,kivy==2.3.2,pyjnius,requests,certifi
orientation = portrait
fullscreen = 0
android.permissions = INTERNET, com.termux.permission.RUN_COMMAND
android.api = 33
android.minapi = 21
android.archs = arm64-v8a
android.allow_backup = True
android.accept_sdk_license = True

[buildozer]
log_level = 2
warn_on_root = 1
android.extra_manifest_xml = ./android/extra_manifest.xml
