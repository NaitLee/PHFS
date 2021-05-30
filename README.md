[English](./README.md) | [简体中文](./README-zh-CN.md)

# PHFS
💫 *Python3 implementation of rejetto [HTTP File Server](https://github.com/rejetto/hfs2)~*

----
🏗 Under construction...

🎉 Please make this project grow. **Any contributions are welcome!**

----

👏 Features that works:

- Filelist, download
- Sorting files, Archiving
- Some macros, `special:alias`
- Upload (No permission restriction)
- Translations, `special:strings`

🕳 Features that doesn't work:

- Search
- Virtual File System
- File actions
- Accounts, Login, Ban, Limits, ...

## Developer Notes

👀 This project is working halfly now, but yet not for production use.

If you are interested in testing this project, please:

1. Install [Werkzeug](https://pypi.org/project/Werkzeug/) by either using `pip` or placing the folder `Werkzeug-(version)/src/werkzeug` from downloaded archive to cloned repo.

2. Pick a HFS template (for HFS 2.4), rename it to `hfs.tpl` and place into cloned repo.

3. Configure port and base folder in `hfs.ini`.

4. For running a server, open `_run_simple.py`; for developing, open `_test.py`; for using as a CGI server with Apache etc., use `cgi.cgi`, and consult Internet for how-to.

Template choices:

- [HFS Default Template](https://github.com/rejetto/hfs2/raw/master/default.tpl)
- [Takeback](https://github.com/NaitLee/Takeback-HFS-Template/releases/latest)
- [Throwback](http://rejetto.com/forum/index.php?topic=12055.0)
- [Stripes](http://rejetto.com/forum/index.php?topic=13415.0)

## Files

- `_test.py`: Run a server for testing, debugging. It also contains werkzeug's reload feature.
- `_run_simple.py`: Run a simple server. Have no debug feature, but works on [pypy](https://www.pypy.org/) on aarch64 architecture.
- `hfs.ini`: Some configs, like port, are here. Currently you can set a base path as the root dir of served pages.

- `_test_macro.py`: Run & test a macro, by entering as argv1 in commandline.
- `cgi.cgi`: For being used as a CGI application with Apache, Nginx etc.

- `cfgLib.py`: The `Config` object is inside this file.
- `classesLib.py`: Some useful `class`es are here.
- `helpersLib.py`: Some useful functions are here.
- `mimeLib.py`: Manages MIME types. Get a defined MIME type with something like `mimeLib.getmime('*.html')`. You can define your own MIMEs in `mime.ini`.
- `scriptLib.py`: When executing a macro/symbol, usually functions in this file will be called.
- `serverLib.py`: Defines a WSGI application, which acts like original HFS.
- `tplLib.py`: The template is interpretered by this.
