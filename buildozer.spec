[app]
title = bactrack5
package.name = bactrack5
package.domain = org.seuusuario
source.dir = .
source.include_exts = py,png,jpg,kv,atlas,json,ttf,html,css,js
version = 0.1
requirements = python3,kivy==2.3.0,flask,setuptools
orientation = portrait
fullscreen = 0
android.permissions = INTERNET
android.api = 33
android.minapi = 21
android.archs = arm64-v8a
android.allow_backup = True
android.accept_sdk_license = True

[buildozer]
log_level = 2
warn_on_root = 1
