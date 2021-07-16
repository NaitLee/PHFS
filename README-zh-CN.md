[English](./README.md) | [简体中文](./README-zh-CN.md)

# PHFS
💫 *Python3 版本的 rejetto HFS 哦~*

----
🏗 进入施工场地，请戴好安全帽……

🎉 让这个作品成长吧！**欢迎做出贡献！**

----

| 👏 可用功能： | 🕳 计划功能： |
| ---- | ---- |
| 文件列表，下载 | 虚拟文件系统（VFS） |
| 排序文件，打包下载 | 文件操作 |
| 上传，搜索 | 封禁、限制 |
| 账户、登录 | 其他 |


🍉 支持的平台:

- Windows 7 及以上
- GNU/Linux, \*nix, \*BSD
- Android，使用 [QPython 3L](https://www.qpython.org/)
- ARM 开发板，如树莓派，使用 [PyPy](https://www.pypy.org/)
- ……

## 小提示

Windows 平台的发行包包含便捷功能。可于[此处](https://github.com/NaitLee/phfs-bundler-win)了解。

拖放文件（夹）到批处理文件（`start.bat`）或命令行（`run.py`）以快速分享。

## 开发者信息

👀 此作品还不能正式投入使用。但是，试一试吧！

如果您有兴趣测试，可以使用一份 *[release](https://github.com/NaitLee/PHFS/releases)*，或者：

1. 安装 [Werkzeug](https://pypi.org/project/Werkzeug/#files)。可以使用 `pip`，或者将下载的压缩包中的文件夹 `Werkzeug-(版本)/src/werkzeug` 放入 clone 的 repo 内。

2. 安装 [WSGIserver](https://pypi.org/project/WSGIserver/#files)。可以使用 `pip`，或者将下载的压缩包中的文件夹 `WSGIserver-(version)/wsgiserver.py` 放入 clone 的 repo 内。

3. 获取 [sha256.js](https://github.com/AndersLindman/SHA256)，放入 repo 文件夹。

4. 选择一个用于 2.4 的 HFS 模板，重命名为 `hfs.tpl` 并放入 repo。

5. 在 `hfs.ini` 中配置端口、基文件夹、允许上传的文件夹、账户。注：原 HFS 的 `hfs.ini` 与 PHFS 不兼容。

6. 要开始一个服务器，用 `python3` 打开 `run.py`；要进行开发工作，打开 `test.py`。

可用的一些模板：

- [HFS 默认模板](https://github.com/rejetto/hfs2/raw/master/default.tpl)
- [Takeback](https://github.com/NaitLee/Takeback-HFS-Template/releases/latest) （推荐）
- [Throwback](http://rejetto.com/forum/index.php?topic=12055.0)
- [Stripes](http://rejetto.com/forum/index.php?topic=13415.0)
- [mobil-light](http://rejetto.com/forum/index.php?topic=11754.msg1066583#msg1066583)

### 注记

- 有缘相见 ♪(^∇^\*)~
  - QQ 交流群号：676460276

- 要在 Android QPython 3L 上使用：
  - 将一份 unix release 放置于 `/sdcard/qpython/projects3`，确保文件夹层级正确。
  - 从 Python 3 内置库获取 `dataclasses.py`，放入文件夹。或者，从 PIP 控制台安装 `dataclasses`。
  - 将 `run.py` 重命名为 `main.py`。
  - 在 QPython 3L app 内，进入 Programs，在 Projects 标签，选择 phfs-unix 并 Run。

### 配置文件

```ini
; 要绑定的 host 地址。设为 0.0.0.0 (ipv4) 或 ::1 (ipv6) 以绑定所有
host=0.0.0.0
; 端口
port=8090
; 服务器根目录。不要包含最后的斜杠 /
; 在 Windows 下也使用 / 而非 \
; 如. /mnt , E:
base_path=
; 允许上传的实目录（本地目录）。以管道分隔 |
upload_allowed_paths=/uploads
; 在此处添加账号。以管道分隔 |
accounts=root
; 每个账号密码的基哈希。使用 `hash.py` 获取。以管道分隔 |
passwords=8d969eef6ecad3c29a3a629280e686cf0c3f5d5a86aff3ca12020c923adc6c92
; 每个账号允许访问的实目录。以反斜杠分隔目录 \ ，以管道分隔账号 |
account_permitted=/root\/boot
; 启用预览压缩文件吗？
preview_zip=
; 总是递归搜索目录吗？1 为真，留空为假
recur_search=1
; 总是递归打包吗？
recur_archive=1
; 是否使用 IPv6?
ipv6=
; 区域代码。用于日志等的本地化。留空为自动检测。
locale=
; 使用哪种字符编码排序文件列表？
; 留空为自动检测。不过，当文件名包含不属于此编码的字符时，会出现错误。
; 提示：使用 gb18030 以使用拼音排序。
sort_encoding=utf-8
; 隐藏以点开头的文件吗？
; 仍然可以在地址栏输入正确的文件名以访问它们。
hide_dots=

```

### 文件

- `run.py`: 开始一个服务器。它可用于 aarch64 架构的 [pypy](https://www.pypy.org/)。
- `hfs.ini`: 一些如端口的配置在这里。此时您可以配置基文件夹作为根目录。
- `hash.py`: 直接运行此文件以获取密码哈希值。

- `test.py`: 开始一个服务器用于开发、调试。它包含 werkzeug 的重载功能。
- `_test_macro.py`: 运行指定在命令行 argv1 的宏。

- `cfgLib.py`: 对象 `Config` 在此文件中。
- `classesLib.py`: 这里有一些有用的类。
- `helpersLib.py`: 这里有一些有用的函数。
- `mimeLib.py`: 管理 MIME 类型。使用如 `mimeLib.getmime('*.html')` 获得对应的 MIME 类型。您可以在 `mime.ini` 定义您自己的 MIME 类型。
- `scriptLib.py`: 当运行宏或符号时，通常会调用这里的函数。
- `serverLib.py`: 定义了一个运行如 HFS 的 WSGI 应用。
- `tplLib.py`: 这是模板解释器。
- `hashLib.py`: 此文件中的类可获取文件哈希值（基哈希、会话哈希）。
- `i18n.ini`: 包含本地化数据。
- `i18nLib.py`: 其中的 `I18n.get_string()` 可获取本地化字符串。
