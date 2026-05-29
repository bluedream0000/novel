# 小说阅读器 - Kivy Android App

纯本地运行的小说阅读器 Android 应用，**无需后端服务器**。

## 功能特性

- 📚 **书架管理**：添加、删除、阅读本地书籍
- 🔍 **在线搜索**：内置爬虫搜索网络小说
- ⬇️ **离线下载**：下载章节到本地阅读
- ☁️ **云端同步**：支持七牛云上传下载（App 内直接生成 Token）
- ⚙️ **阅读设置**：字体大小、主题切换
- 🔄 **完全离线**：阅读已缓存书籍无需任何网络

## 技术栈

- **UI 框架**：Kivy
- **数据库**：SQLite
- **爬虫**：requests + BeautifulSoup4
- **云端**：七牛云（App 内直接生成 Token）
- **打包工具**：Buildozer

## 项目结构

```
kivy_app/
├── main.py              # 主程序入口
├── database.py          # 数据库管理器
├── qiniu_manager.py    # 七牛云管理器（Token 生成 + 上传下载）
├── buildozer.spec      # 打包配置
└── README.md           # 说明文档
```

## 核心功能

### 七牛云 Token 生成

App 内直接使用 Python 生成七牛云上传/下载 Token，无需后端：

```python
from qiniu_manager import QiniuManager

qn = QiniuManager(access_key, secret_key, bucket, domain)
token = qn.generate_upload_token()  # 生成上传 Token
url = qn.upload_json(key, data)    # 直接上传
```

### 云端同步功能

| 操作 | 公开空间 | 私有空间 | 说明 |
|------|----------|----------|------|
| 下载 | ✅ 支持 | ✅ 支持 | App 内直接下载 |
| 上传 | ✅ 支持 | ✅ 支持 | App 内生成 Token 并上传 |

**完全不需要电脑后端！**

## 开发环境搭建

### 1. 安装依赖

```bash
pip install kivy
pip install requests beautifulsoup4 lxml
```

### 2. 运行测试

```bash
cd kivy_app
python main.py
```

## 打包 APK

### 方法一：使用 Buildozer（推荐）

#### Linux/macOS

```bash
# 安装 buildozer
pip install buildozer

# 安装依赖 (Ubuntu/Debian)
sudo apt-get install -y git zip unzip openjdk-17-jdk python3-pip \
    autoconf libtool pkg-config zlib1g-dev libncurses5-dev \
    libncursesw5-dev libtinfo5 cmake libffi-dev libssl-dev

# 构建 APK
cd kivy_app
buildozer android debug

# 构建完成后 APK 在 bin/ 目录
```

#### Windows

Windows 不支持直接运行 Buildozer，需要使用：

- **WSL (Windows Subsystem for Linux)**
- **Docker 容器**
- **虚拟机（推荐 VirtualBox + Ubuntu）**

### 方法二：使用 Docker

```bash
# 拉取 buildozer 镜像
docker pull kivy/buildozer

# 运行构建
docker run --rm -v $(pwd):/home/user/hostcwd kivy/buildozer android debug
```

## 使用说明

### 首次使用

1. 打开 App
2. 在"云端同步"页面配置七牛云（AK、SK、Bucket、Domain）
3. 勾选"公开空间"（推荐）
4. 点击"上传到云端"备份数据

### 数据同步

1. **上传**：将本地书架上传到七牛云
2. **下载**：从七牛云恢复书架数据
3. **备份命名**：`novel-reader/{timestamp}_backup.json`

### 阅读书籍

1. 点击"搜索"搜索书籍
2. 点击"下载"下载书籍到本地
3. 点击"阅读"开始阅读
4. 章节自动保存阅读进度

## 注意事项

### 网络要求

- **首次使用**：需要网络下载 App（如果有安装包则不需要）
- **搜索/下载书籍**：需要网络
- **阅读已缓存书籍**：完全离线
- **云端同步**：需要网络

### 七牛云配置

1. **AccessKey/SecretKey**：在七牛云控制台获取
2. **Bucket**：存储空间名称
3. **Domain**：访问域名（不带 http://）
4. **公开空间**：推荐开启，方便下载

### 存储空间

- 数据库位置：Android 应用私有目录
- 无需额外权限（Android 11+）
- 约 10MB 基础大小

## 后续优化方向

1. **UI 美化**：使用 KivyMD 替代原生 Kivy
2. **阅读器增强**：添加翻页动画、夜间模式
3. **更多书源**：扩展爬虫支持更多网站
4. **本地导入**：支持 txt/epub 文件导入
5. **语音朗读**：集成 TTS 功能

## 许可证

MIT License
