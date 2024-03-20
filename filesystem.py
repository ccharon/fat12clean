import datetime
import struct

from fat12 import Directory


class FileSystem:
    def __init__(self):
        self.root = Directory("root", None)

    def __str__(self):
        return str(self.root)


class FileSystemEntry:
    def __init__(self, entry):
        self.name = entry[:11].decode('ascii', errors='replace').strip()
        self.attributes = entry[11]
        self.first_cluster = struct.unpack("<H", entry[26:28])[0]
        self.size = struct.unpack("<I", entry[28:32])[0]

        # Extract creation time and date
        self.creation_time = struct.unpack("<H", entry[22:24])[0]
        self.creation_date = struct.unpack("<H", entry[24:26])[0]

    @property
    def creation_datetime(self):
        year = self.creation_date >> 9
        month = (self.creation_date >> 5) & 0b1111
        day = self.creation_date & 0b11111

        hour = self.creation_time >> 11
        minute = (self.creation_time >> 5) & 0b111111
        second = (self.creation_time & 0b11111) * 2

        # Convert from 0-based to 1-based values
        year += 1980  # The year is stored as the number of years since 1980

        return datetime.datetime(year, month, day, hour, minute, second)

    def is_directory(self):
        return self.attributes & 0x10

    def is_file(self):
        return not self.is_directory()

    def __str__(self):
        return f"Name: {self.name}, Attributes: {self.attributes}, First Cluster: {self.first_cluster}, Size: {self.size}, Creation Date and Time: {self.creation_datetime}"
