[English](./README.md) | [简体中文](./README-zh-CN.md)

# PHFS
💫 *Python3 版本的 rejetto HFS 哦~*

----
🏗 进入施工场地，请戴好安全帽……

🎉 让这个作品成长吧！**欢迎做出贡献！**

----

👏 可用功能：

- 文件列表，下载
- 排序文件，打包下载
- 上传，搜索
- 本地化，`special:strings`
- 一些宏，`special:alias`

🕳 仍不可用的功能：

- 虚拟文件系统（VFS）
- 文件操作
- 账户、登录、封禁、限制、……

🍉 支持的平台:

- 所有 Python 3.7 支持的 x86, x64 平台：
  - Windows 7 及以上
  - GNU/Linux, *nix, *BSD
  - ……

- 一些 ARM 平台:
  - Android，使用 [QPython 3L](https://www.qpython.org/)
  - ARM 开发板，如树莓派，使用 [PyPy](https://www.pypy.org/)
  - ……

- 可能更多！

## 开发者信息

👀 此作品现部分可用，不过还不能正式投入使用。

如果您有兴趣测试，可以：

1. 安装 [Werkzeug](https://pypi.org/project/Werkzeug/#files)。可以使用 `pip`，或者将下载的压缩包中的文件夹 `Werkzeug-(版本)/src/werkzeug` 放入 clone 的 repo 内。

2. 安装 [WSGIserver](https://pypi.org/project/WSGIserver/#files)。可以使用 `pip`，或者将下载的压缩包中的文件夹 `WSGIserver-(version)/wsgiserver.py` 放入 clone 的 repo 内。

3. 选择一个用于 2.4 的 HFS 模板，重命名为 `hfs.tpl` 并放入 repo。

4. 在 `hfs.ini` 中配置端口、基文件夹、允许上传的文件夹。

5. 要开始一个服务器，用 `python3` 打开 `run.py`；要进行开发工作，打开 `test.py`。

可用的一些模板：

- [HFS 默认模板](https://github.com/rejetto/hfs2/raw/master/default.tpl)
- [Takeback](https://github.com/NaitLee/Takeback-HFS-Template/releases/latest) （推荐）
- [Throwback](http://rejetto.com/forum/index.php?topic=12055.0)
- [Stripes](http://rejetto.com/forum/index.php?topic=13415.0)
- [mobil-light](http://rejetto.com/forum/index.php?topic=11754.msg1066583#msg1066583)

### 注记

- 有缘相见 ♪(^∇^*)~
  - QQ 交流群号：676460276

- 要在 Android QPython 3L 上使用：
  - 将 repo 放置于 `/sdcard/qpython/projects3`，确保文件夹层级正确。
  - 将 `run.py` 重命名为 `main.py`。
  - 在 QPython 3L app 内，进入 Programs，在 Projects 标签，选择 repo 名称并 Run。

### 文件

- `test.py`: 开始一个服务器用于开发、调试。它包含 werkzeug 的重载功能。
- `run.py`: 开始一个简单服务器。它可用于 aarch64 架构的 [pypy](https://www.pypy.org/)。
- `hfs.ini`: 一些如端口的配置在这里。此时您可以配置基文件夹作为根目录。

- `_test_macro.py`: 运行指定在命令行 argv1 的宏。

- `cfgLib.py`: 对象 `Config` 在此文件中。
- `classesLib.py`: 这里有一些有用的类。
- `helpersLib.py`: 这里有一些有用的函数。
- `mimeLib.py`: 管理 MIME 类型。使用如 `mimeLib.getmime('*.html')` 获得对应的 MIME 类型。您可以在 `mime.ini` 定义您自己的 MIME 类型。
- `scriptLib.py`: 当运行宏或符号时，通常会调用这里的函数。
- `serverLib.py`: 定义了一个运行如 HFS 的 WSGI 应用。
- `tplLib.py`: 这是模板解释器。
