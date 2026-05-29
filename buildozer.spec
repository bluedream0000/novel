[app]
# 应用标题
 title = 小说阅读器
# 应用包名
package.name = novelreader
# 应用包域名
package.domain = org.example
# 源代码目录
source.dir = .
# 主程序入口
source.include_exts = py,png,jpg,kv,atlas,ttf,db,json
# 版本号
version = 1.0.0
# 应用图标
icon.filename = %(source.dir)s/icon.png
# 应用要求
requirements = python3,kivy,sqlite3,requests,beautifulsoup4,lxml,urllib3,certifi,chardet,idna,qiniu
# 安卓 API 版本（使用稳定版本）
android.api = 31
# 安卓最小 API
android.minapi = 21
# 安卓 NDK 版本
android.ndk = 23b
# 安卓 SDK 版本
android.sdk = 31
# 安卓 Build Tools 版本
android.build_tools = 31.0.0
# 权限
android.permissions = INTERNET,WRITE_EXTERNAL_STORAGE,READ_EXTERNAL_STORAGE,ACCESS_NETWORK_STATE
# 架构
android.archs = arm64-v8a, armeabi-v7a
# 屏幕方向
orientation = portrait
# 全屏
fullscreen = 0
# 服务
services =

[buildozer]
# 日志级别
log_level = 2
# 构建目录
build_dir = ./.buildozer
# 打包后 APK 目录
bin_dir = ./bin
