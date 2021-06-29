[English](./README.md) | [简体中文](./README-zh-CN.md)

# PHFS
💫 *This is a Python3 implementation of rejetto's [HTTP File Server](https://github.com/rejetto/hfs2)~*

----
🏗 Under construction...

🎉 Please help make this project grow. **Contributions are welcome!**

----

👏 Done Features:

- Filelist, download
- Sorting files, Archiving
- Upload, Search
- Accounts, Login
- Translations, `special:strings`
- Some macros, `special:alias`

🕳 To-do Features:

- Virtual File System
- File actions
- Ban, Limits, ...

🍉 Supported platforms:

- All x86, x64 platforms that Python 3.7 supports:
  - Windows 7 and upper
  - GNU/Linux, *nix, *BSD
  - ...

- Some ARM platforms:
  - Android, with [QPython 3L](https://www.qpython.org/)
  - ARM Boards like Raspberry Pi, with [PyPy](https://www.pypy.org/)
  - ...

- Maybe more!

## Developer Notes

👀 This project is not yet ready for production use. But, please, have a try!

You can try by using a release, or:

1. Install [Werkzeug](https://pypi.org/project/Werkzeug/#files) by either using `pip` or placing the folder `Werkzeug-(version)/src/werkzeug` from downloaded archive to cloned repo.

2. Install [WSGIserver](https://pypi.org/project/WSGIserver/#files) by either using `pip` or placing the file `WSGIserver-(version)/wsgiserver.py` from downloaded archive to cloned repo.

3. Get [sha256.js](https://github.com/AndersLindman/SHA256), place into repo folder.

4. Pick a HFS template (for HFS 2.4), rename it to `hfs.tpl` and place into cloned repo.

5. Configure port, base folder, upload-allowed folders and accounts in `hfs.ini`. Note: `hfs.ini` of original HFS is not compatible to PHFS.

6. For running a server, open `run.py`; for developing, open `test.py`.

Template choices:

- [HFS Default Template](https://github.com/rejetto/hfs2/raw/master/default.tpl)
- [Takeback](https://github.com/NaitLee/Takeback-HFS-Template/releases/latest) (Recommended)
- [Throwback](http://rejetto.com/forum/index.php?topic=12055.0)
- [Stripes](http://rejetto.com/forum/index.php?topic=13415.0)
- [mobil-light](http://rejetto.com/forum/index.php?topic=11754.msg1066583#msg1066583)

### Notes

- To use in QPython 3L on Android:
  - Put repo into folder `/sdcard/qpython/projects3`, ensure folder is not nested.
  - Follow trial steps, prepare all required files.
  - Rename `run.py` to `main.py`.
  - In QPython 3L app, go to Programs, in Projects tab, select repo name then run.

### Files

- `run.py`: Run a simple server. Has no debug feature, but works on [pypy](https://www.pypy.org/) on aarch64 architecture.
- `hfs.ini`: Some configs, like port, are here. Currently you can set a base path as the root dir of served pages, also can set upload-allowed paths.
- `hash.py`: Hash a password by executing this directly.

- `test.py`: Run a server for testing, debugging. It also contains werkzeug's reload feature.
- `_test_macro.py`: Run & test a macro, by entering as argv1 in commandline.

- `cfgLib.py`: The `Config` and `Account` object is inside this file.
- `classesLib.py`: Some useful classes are here.
- `helpersLib.py`: Some useful functions are here.
- `mimeLib.py`: Manages MIME types. Get a defined MIME type with something like `mimeLib.getmime('*.html')`. You can define your own MIMEs in `mime.ini`.
- `scriptLib.py`: When executing a macro/symbol, usually functions in this file will be called.
- `serverLib.py`: Defines a WSGI application, which acts like original HFS.
- `tplLib.py`: The template is interpreted by this.
- `hashLib.py`: Classes inside can hash passwords from/to base-hash/token-hash.