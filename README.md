# PHFS
💫 *Python3 implementation of rejetto [HTTP File Server](https://github.com/rejetto/hfs2)*

----
🏗 Under construction...

----

👏 Features that works:
- Filelist, download
- Sorting files, Archiving
- Some macros, special:alias
- Uploading (No permission restriction)
- Translations, special:strings

🕳 Features that doesn't work:
- Virtual File System
- File actions
- Accounts, Login, Ban, Limits, ...

## Developer Notes

👀 This project is working halfly now, but yet not for production use.

If you are interested in testing this project, please:

1. install [Werkzeug](https://pypi.org/project/Werkzeug/) by either using `pip` or placing the folder `Werkzeug-(version)/src/werkzeug` from downloaded archive to cloned repo.

2. Pick a HFS template (for HFS 2.4), rename it to `hfs.tpl` and place into cloned repo.

Template choices:
- HFS Default Template: In original HFS, press `F6` to edit the template, then save it
- [Takeback](https://github.com/NaitLee/Takeback-HFS-Template/releases/latest)
- [Throwback](http://rejetto.com/forum/index.php?topic=12055.0)
- [Stripes](http://rejetto.com/forum/index.php?topic=13415.0)

## Files

- `_test.py`: Run a server for testing, debugging. It also contains werkzeug's reload feature.
- `_test_macro.py`: Run & test a macro, by entering as argv1 in commandline.
- `_run_simple.py`: Run a simple server. Have no debug feature, but works on [pypy](https://www.pypy.org/) on aarch64 architecture.
- `cgi.cgi`: For being used as a CGI application with Apache, Nginx etc.
