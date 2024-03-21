import datetime
import struct

from fat12 import Directory


class FileSystem:
    def __init__(self):
        self.root = Directory("root", 0, None)

    def __str__(self):
        return str(self.root)


class FileSystemEntry:
    """
    | Bytes |  Content                                                        |
    |-------|-----------------------------------------------------------------|
    |  0-10 | File name (8 bytes) with extension (3 bytes)                    |
    |    11 | Attribute - a bitvector.                                        |
    |       |   Bit 0: read only.                                             |
    |       |   Bit 1: hidden.                                                |
    |       |   Bit 2: system file.                                           |
    |       |   Bit 3: volume label.                                          |
    |       |   Bit 4: subdirectory.                                          |
    |       |   Bit 5: archive.                                               |
    |       |   Bits 6-7: unused.                                             |
    | 12-21 | Reserved (see below)                                            |
    | 22-23 | Time (5/6/5 bits, for hour/minutes/doubleseconds)               |
    | 24-25 | Date (7/4/5 bits, for year-since-1980/month/day)                |
    | 26-27 | Starting cluster (0 for an empty file)                          |
    | 28-31 | Filesize in bytes                                               |

    The first byte of a name (byte 0-10) must not be 0x20 (space). Short names or extensions are padded with spaces.
    Special ASCII characters 0x22 ("), 0x2a (*), 0x2b (+), 0x2c (,), 0x2e (.), 0x2f (/), 0x3a (:), 0x3b (;), 0x3c (<),
    0x3d (=), 0x3e (>), 0x3f (?), 0x5b ([), 0x5c (\), 0x5d (]), 0x7c (|) are not allowed.
    """
    def __init__(self, entry):
        self.name = entry[:11].decode('ascii', errors='replace').strip()
        self.attributes = entry[11]
        # Extract creation time and date
        self.creation_time = struct.unpack("<H", entry[22:24])[0]
        self.creation_date = struct.unpack("<H", entry[24:26])[0]

        self.first_cluster = struct.unpack("<H", entry[26:28])[0]
        self.size = struct.unpack("<I", entry[28:32])[0]

        # Initialize clusters list with the first cluster
        self.clusters = [self.first_cluster]

    @property
    def creation_datetime(self):
        year = ((self.creation_date >> 9) & (1 << 7) - 1) + 1980
        month = (self.creation_date >> 5) & ((1 << 4) - 1)
        day = (self.creation_date & (1 << 5) - 1)

        hour = (self.creation_time >> 11) & ((1 << 5) - 1)
        minute = (self.creation_time >> 5) & ((1 << 6) - 1)
        second = (self.creation_time & (1 << 5) - 1) * 2

        return datetime.datetime(year, month, day, hour, minute, second)

    def is_readonly(self):
        return self.attributes & 0x01

    def is_hidden(self):
        return self.attributes & 0x02

    def is_system(self):
        return self.attributes & 0x04

    def is_volume_label(self):
        return self.attributes & 0x08

    def is_directory(self):
        return self.attributes & 0x10

    def is_archive(self):
        return self.attributes & 0x20

    def is_file(self):
        return not self.is_directory()

    def __str__(self):
        attributes = f"{'R' if self.is_readonly() else '-'} {'H' if self.is_hidden() else '-'} {'S' if self.is_system() else '-'} {'A' if self.is_archive() else '-'}"
        return f"Name: {self.name}, Attributes: {attributes}, First Cluster: {self.first_cluster}, Size: {self.size}, Creation Date and Time: {self.creation_datetime}"