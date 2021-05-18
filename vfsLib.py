
from classesLib import Resource

class VFSManager():
    class ItemAttributes():
        isVirtual = False
        isRoot = False
        isBrowsable = True
        isHidden = False
        isTemp = False
        isHiddenTree = False
        isLink = False
        isDownloadForbidden = False
        dontCountAsDownload = False
        hideExt = False
        dontLog = False
        canArchive = True
        def __init__(self, **args):
            for i in args:
                setattr(self, i, args[i])
    class ItemProperties(ItemAttributes):
        _locked = False
        _download_count = 0
        comment = ''
        resource = '/'
        node = None
        size = 0
        added_time = 0
        modified_time = 0
        icon = 0
        accounts = []
        files_filter = '*'
        folders_filter = '*'
        realm = ''
        diff_tpl = ''
        default_file_mask = '*'
        dont_count_as_download_mask = ''
        upload_filter_mask = '*'
        def __init__(self, **args):
            super().__init__()
            for i in args:
                setattr(self, i, args[i])
    class Item():
        def __init__(self, properties):
            self.properties = properties
    class Link(Item):
        def __init__(self, properties):
            super().__init__(properties)
    def __init__(self, vfs_file='hfs.vfs'):
        self.vfs = {
            '': self.Item(self.ItemProperties(
                resource='/',
                isVirtual=False,
                isRoot=True,
                dontCountAsDownload=True,
                canArchive=True,
                icon=1,
            )),
            '/1': self.Item(self.ItemProperties(
                resource='/mnt/319789E97FF27EB0/',
                isVirtual=False,
                canArchive=True,
                icon=2
            ))
        }
    def add_item(self, **args):
        new_item = self.Item(self.ItemProperties(
            flags=self.ItemAttributes(
                isFolder=True if args['type'] in ('virtual_folder', 'real_folder') else False,
                isVirtual=True if args['type'] == 'virtual_folder' else False,
            ),
        ))
        for i in args:
            setattr(new_item.properties, i, args[i])
        self.vfs[args['name']] = new_item
    def remove_item(self, name):
        for i in self.vfs:
            if i.properties.name == i:
                del i
    def url_to_resource(self, url):
        levels = url.split('/')
        path_virtual = url
        count = len(levels)
        while path_virtual not in self.vfs and count >= 0:
            path_virtual = '/'.join(levels[0:count])
            count -= 1
        if count != -1:
            item = self.vfs[path_virtual]
            path_real = item.properties.resource + '/'.join(levels[count + 1:]) if not item.properties.isVirtual else ''
            return Resource(url, path_virtual, path_real)
        else:
            return None
    