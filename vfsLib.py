

class VFSManager():
    class ItemAttributes():
        isFolder = False
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
        name = ''
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
        parent = None
        def __init__(self, **args):
            super().__init__()
            for i in args:
                setattr(self, i, args[i])
    class Item():
        def __init__(self, properties):
            self.properties = properties
    class VirtualFolder(Item):
        def __init__(self, properties):
            super().__init__(properties)
    class RealFolder(Item):
        def __init__(self, properties):
            super().__init__(properties)
    class Link(Item):
        def __init__(self, properties):
            super().__init__(properties)
    def __init__(self, vfs_file='hfs.vfs'):
        self.vfs = {
            '': self.VirtualFolder(self.ItemProperties(
                name='/',
                resource='/',
                isFolder=True,
                isVirtual=True,
                isRoot=True,
                dontCountAsDownload=True,
                canArchive=True,
                icon=1
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
        return url
    