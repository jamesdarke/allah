"""
This module defines the API class, which makes use of a JSON-RPC client to provide higher-level methods to
interact easily with a remote aria2c process.
"""
from base64 import b64encode

from .downloads import Download
from .options import Options
from .stats import Stats


class API:
    """
    A class providing high-level methods to interact with a remote aria2c process.

    This class is instantiated with a reference to a :class:`aria2p.JSONRPCClient` instance. It then uses this client
    to call remote procedures, or remote methods. The client methods reflect exactly what aria2c is providing
    through JSON-RPC, while this class's methods allow for easier / faster control of the remote process. It also
    wraps the information the client retrieves in Python object, like  :class:`aria2p.Download`, allowing for
    even more Pythonic interactions, without worrying about payloads, responses, JSON, etc..
    """

    def __init__(self, json_rpc_client):
        """
        Initialization method.

        Args:
            json_rpc_client (:class:`aria2p.JSONRPCClient`): an instance of the ``JSONRPCClient`` class.
        """
        self.client = json_rpc_client

    def add_magnet(self, magnet_uri, options=None, position=None):
        """
        Add a download with a Magnet URI.

        Args:
            magnet_uri (str): the Magnet URI.
            options (:class:`aria2p.Options` or dict): an instance of the ``Options`` class or a dictionary
              containing Aria2c options to create the download with.
            position (int): the position where to insert the new download in the queue. Start at 0 (top).

        Returns:
            :class:`aria2p.Download` instance: the newly created download object.
        """
        if options is None:
            options = {}

        if isinstance(options, Options):
            client_options = options.get_struct()
        else:
            client_options = options

        gid = self.client.add_uri([magnet_uri], client_options, position)

        return self.get_download(gid)

    def add_torrent(self, torrent_file_path, uris=None, options=None, position=None):
        """
        Add a download with a Torrent file (usually .torrent extension).

        Args:
            torrent_file_path (str/Path): the path to the Torrent file.
            uris (list of str): a list of URIs used for Web-seeding.
            options (:class:`aria2p.Options` or dict): an instance of the ``Options`` class or a dictionary
              containing Aria2c options to create the download with.
            position (int): the position where to insert the new download in the queue. Start at 0 (top).

        Returns:
            :class:`aria2p.Download` instance: the newly created download object.
        """
        if uris is None:
            uris = []

        if options is None:
            options = {}

        if isinstance(options, Options):
            client_options = options.get_struct()
        else:
            client_options = options

        with open(torrent_file_path, "rb") as stream:
            torrent_contents = stream.read()
        encoded_contents = b64encode(torrent_contents).decode("utf8")

        gid = self.client.add_torrent(encoded_contents, uris, client_options, position)

        return self.get_download(gid)

    def add_metalink(self, metalink_file_path, options=None, position=None):
        """
        Add a download with a Metalink file.

        Args:
            metalink_file_path (str/Path): the path to the Metalink file.
            options (:class:`aria2p.Options` or dict): an instance of the ``Options`` class or a dictionary
              containing Aria2c options to create the download with.
            position (int): the position where to insert the new download in the queue. Start at 0 (top).

        Returns:
            :class:`aria2p.Download` instance: the newly created download object.
        """
        if options is None:
            options = {}

        if isinstance(options, Options):
            client_options = options.get_struct()
        else:
            client_options = options

        with open(metalink_file_path) as stream:
            metalink_contents = stream.read()
        encoded_contents = b64encode(metalink_contents)

        gids = self.client.add_metalink(encoded_contents, client_options, position)

        return self.get_downloads(gids)

    def add_url(self, urls, options=None, position=None):
        """
        Add a download with a URL (or more).

        Args:
            urls (list of str): the list of URLs that point to the same resource.
            options (:class:`aria2p.Options` or dict): an instance of the ``Options`` class or a dictionary
              containing Aria2c options to create the download with.
            position (int): the position where to insert the new download in the queue. Start at 0 (top).

        Returns:
            :class:`aria2p.Download` instance: the newly created download object.

        """
        if options is None:
            options = {}

        if isinstance(options, Options):
            client_options = options.get_struct()
        else:
            client_options = options

        gid = self.client.add_uri(urls, client_options, position)

        return self.get_download(gid)

    def search(self, patterns):
        """
        Not implemented.

        Search and return :class:`aria2p.Download` object based on multiple patterns.

        Args:
            patterns (list of dict): the patterns used to filter the download list.

        Returns:
            list of :class:`aria2p.Download` instances: the download objects matching the patterns.

        """
        # gid
        # status
        # totalLength
        # completedLength
        # uploadLength
        # bitfield
        # downloadSpeed
        # uploadSpeed
        # infoHash
        # numSeeders
        # seeder
        # pieceLength
        # numPieces
        # connections
        # errorCode
        # errorMessage
        # followedBy
        # following
        # belongsTo
        # dir
        # files
        # bittorrent
        #        announceList
        #        comment
        #        creationDate
        #        mode
        #        info
        #               name
        # verifiedLength
        # verifyIntegrityPending
        raise NotImplementedError

    def get_download(self, gid):
        """
        Get a :class:`aria2p.Download` object thanks to its GID.

        Args:
            gid (str): the GID of the download to get.

        Returns:
            :class:`aria2p.Download` instance: the retrieved download object.
        """
        return Download(self, self.client.tell_status(gid))

    def get_downloads(self, gids=None):
        """
        Get a list :class:`aria2p.Download` object thanks to their GIDs.

        Args:
            gids (list of str): the GIDs of the downloads to get. If None, return all the downloads.

        Returns:
            list of :class:`aria2p.Download` instances: the retrieved download objects.
        """
        downloads = []

        if gids:
            for gid in gids:
                downloads.append(Download(self, self.client.tell_status(gid)))
        else:
            downloads.extend(self.client.tell_active())
            downloads.extend(self.client.tell_waiting(0, 1000))
            downloads.extend(self.client.tell_stopped(0, 1000))
            downloads = [Download(self, d) for d in downloads]

        return downloads

    def move(self, download, pos):
        """
        Move a download in the queue, relatively to its current position.

        Args:
            download (:class:`aria2p.Download`): the download object to move.
            pos (int): the relative position (1 to move down, -1 to move up, -2 to move up two times, etc.).

        Returns:
            bool: Success or failure of the operation.
        """
        return self.client.change_position(download.gid, pos, "POS_CUR")

    def move_to(self, download, pos):
        """
        Move a download in the queue, with absolute positioning.

        Args:
            download (:class:`aria2p.Download`): the download object to move.
            pos (int): the absolute position in the queue where to move the download. 0 for top, -1 for bottom.

        Returns:
            bool: Success or failure of the operation.
        """
        return self.client.change_position(download.gid, pos, "POS_SET")

    def move_up(self, download, pos=1):
        """
        Move a download up in the queue.

        Args:
            download (:class:`aria2p.Download`): the download object to move.
            pos (int): number of times to move up. With negative values, will move down (use move or move_down instead).

        Returns:
            bool: Success or failure of the operation.
        """
        return self.client.change_position(download.gid, -pos, "POS_CUR")

    def move_down(self, download, pos=1):
        """
        Move a download down in the queue.

        Args:
            download (:class:`aria2p.Download`): the download object to move.
            pos (int): number of times to move down. With negative values, will move up (use move or move_up instead).

        Returns:
            bool: Success or failure of the operation.
        """
        return self.client.change_position(download.gid, pos, "POS_CUR")

    def move_to_top(self, download):
        """
        Move a download to the top of the queue.

        Args:
            download (:class:`aria2p.Download`): the download object to move.

        Returns:
            bool: Success or failure of the operation.
        """
        return self.client.change_position(download.gid, 0, "POS_SET")

    def move_to_bottom(self, download):
        """
        Move a download to the bottom of the queue.

        Args:
            download (:class:`aria2p.Download`): the download object to move.

        Returns:
            bool: Success or failure of the operation.
        """
        return self.client.change_position(download.gid, -1, "POS_SET")

    def remove(self, downloads, force=False):
        """
        Remove the given downloads from the list.

        Args:
            downloads (list of :class:`aria2p.Download`): the list of downloads to remove.
            force (bool): whether to force the removal or not.

        Returns:
            list of bool: Success or failure of the operation for each given download.
        """
        # TODO: batch/multicall candidate
        if force:
            remove_func = self.client.force_remove
        else:
            remove_func = self.client.remove
        return [remove_func(d.gid) for d in downloads]

    def remove_all(self, force=False):
        """
        Remove all downloads from the list.

        Args:
            force (bool): whether to force the removal or not.

        Returns:
            bool: Success or failure of the operation to remove all downloads.
        """
        # TODO: batch/multicall candidate
        if force:
            remove_func = self.client.force_remove
        else:
            remove_func = self.client.remove
        return [remove_func(d.gid) for d in self.get_downloads()]

    def pause(self, downloads):
        """
        Remove the given downloads from the list.

        Args:
            downloads (list of :class:`aria2p.Download`): the list of downloads to remove.

        Returns:
            list of bool: Success or failure of the operation for each given download.
        """
        # TODO: batch/multicall candidate
        return [self.client.pause(d.gid) for d in downloads]

    def pause_all(self):
        """
        Remove the given downloads from the list.

        Returns:
            bool: Success or failure of the operation to pause all downloads.
        """
        return self.client.pause_all()

    def resume(self, downloads):
        """
        Resume (unpause) the given downloads.

        Args:
            downloads (list of :class:`aria2p.Download`): the list of downloads to resume.

        Returns:
            list of bool: Success or failure of the operation for each given download.
        """
        # TODO: batch/multicall candidate
        return [self.client.unpause(d.gid) for d in downloads]

    def resume_all(self):
        """
        Resume (unpause) all downloads.

        Returns:
            bool: Success or failure of the operation to resume all downloads.
        """
        return self.client.unpause_all()

    def purge(self):
        """
        Delete completed, removed or failed downloads from the queue.

        Returns:
            bool: Success or failure of the operation.
        """
        return self.client.purge_download_result()

    def get_options(self, downloads):
        """
        Get options for each of the given downloads.

        Args:
            downloads (list of :class:`aria2p.Download`): the list of downloads to get the options of.

        Returns:
            list of :class:`aria2p.Options`: options object for each given download.
        """
        # TODO: batch/multicall candidate
        options = []
        for download in downloads:
            options.append(Options(self, self.client.get_option(download.gid), download))
        return options

    def get_global_options(self):
        """
        Get the global options.

        Returns:
            :class:`aria2p.Options` instance: the global Aria2c options.
        """
        return Options(self, self.client.get_global_option())

    def set_options(self, options, downloads):
        """
        Set options for specific downloads.

        Args:
            options (:class:`aria2p.Options` or dict): an instance of the ``Options`` class or a dictionary
              containing Aria2c options to create the download with.
            downloads (list of :class:`aria2p.Download`): the list of downloads to set the options for.

        Returns:
            list of bool: Success or failure of the operation for changing options for each given download.
        """
        if isinstance(options, Options):
            client_options = options.get_struct()
        else:
            client_options = options

        # TODO: batch/multicall candidate
        results = []
        for download in downloads:
            results.append(self.client.change_option(download.gid, client_options) == "OK")
        return results

    def set_global_options(self, options):
        """
        Set global options.

        Args:
            options (:class:`aria2p.Options` or dict): an instance of the ``Options`` class or a dictionary
              containing Aria2c options to create the download with.

        Returns:
            bool: Success or failure of the operation for changing global options.
        """
        if isinstance(options, Options):
            client_options = options.get_struct()
        else:
            client_options = options

        return self.client.change_global_option(client_options) == "OK"

    def get_stats(self):
        """
        Get the stats of the remote Aria2c process.

        Returns:
            :class:`aria2p.Stats` instance: the global stats returned by the remote process.
        """
        return Stats(self.client.get_global_stat())
