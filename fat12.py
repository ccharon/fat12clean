import struct


class BootSector:
    """
    0-2     Jump to bootstrap (E.g. eb 3c 90; on i86: JMP 003E NOP.
            One finds either eb xx 90, or e9 xx xx.
            The position of the bootstrap varies.)
    3-10    OEM name/version (E.g. "IBM  3.3", "IBM 20.0", "MSDOS5.0", "MSWIN4.0".
            Various format utilities leave their own name, like "CH-FOR18".
            Sometimes just garbage. Microsoft recommends "MSWIN4.1".)
            /* BIOS Parameter Block starts here */
    11-12   Number of bytes per sector (512)
            Must be one of 512, 1024, 2048, 4096.
    13      Number of sectors per cluster (1)
            Must be one of 1, 2, 4, 8, 16, 32, 64, 128.
            A cluster should have at most 32768 bytes. In rare cases 65536 is OK.
    14-15   Number of reserved sectors (1)
            FAT12 and FAT16 use 1. FAT32 uses 32.
    16      Number of FAT copies (2)
    17-18   Number of root directory entries (224)
            0 for FAT32. 512 is recommended for FAT16.
    19-20   Total number of sectors in the filesystem (2880)
            (in case the partition is not FAT32 and smaller than 32 MB)
    21      Media descriptor type (f0: 1.4 MB floppy, f8: hard disk; see below)
    22-23   Number of sectors per FAT (9)
            0 for FAT32.
    24-25   Number of sectors per track (12)
    26-27   Number of heads (2, for a double-sided diskette)
    28-29   Number of hidden sectors (0)
            Hidden sectors are sectors preceding the partition.
            /* BIOS Parameter Block ends here */
    30-509  Bootstrap
    510-511 Signature 55 aa
    """
    def __init__(self, raw_boot_sector):
        self.jump_instruction = ' '.join(f'{i:02x}' for i in raw_boot_sector[0:3])
        self.oem_name = raw_boot_sector[3:11].decode('ascii', errors='replace').ljust(8, ' ')
        self.bytes_per_sector = struct.unpack("<H", raw_boot_sector[11:13])[0]
        self.sectors_per_cluster = struct.unpack("<B", raw_boot_sector[13:14])[0]
        self.reserved_sectors = struct.unpack("<H", raw_boot_sector[14:16])[0]
        self.number_of_fats = struct.unpack("<B", raw_boot_sector[16:17])[0]
        self.root_entries = struct.unpack("<H", raw_boot_sector[17:19])[0]
        self.total_sectors = struct.unpack("<H", raw_boot_sector[19:21])[0]
        self.media_descriptor = ' '.join(f'{i:02x}' for i in raw_boot_sector[21:22])
        self.sectors_per_fat = struct.unpack("<H", raw_boot_sector[22:24])[0]
        self.sectors_per_track = struct.unpack("<H", raw_boot_sector[24:26])[0]
        self.number_of_heads = struct.unpack("<H", raw_boot_sector[26:28])[0]
        self.hidden_sectors = struct.unpack("<H", raw_boot_sector[28:30])[0]
        self.bootstrap = ' '.join(f'{i:02x}' for i in raw_boot_sector[30:510]).ljust(480, '0')
        self.signature = ' '.join(f'{i:02x}' for i in raw_boot_sector[510:512])

    def to_bytes(self):
        # Pack the attributes back into bytes
        raw_boot_sector = bytearray()
        raw_boot_sector.extend(bytes.fromhex(self.jump_instruction))
        raw_boot_sector.extend(self.oem_name[:8].encode('ascii'))
        raw_boot_sector.extend(struct.pack("<H", self.bytes_per_sector))
        raw_boot_sector.extend(struct.pack("<B", self.sectors_per_cluster))
        raw_boot_sector.extend(struct.pack("<H", self.reserved_sectors))
        raw_boot_sector.extend(struct.pack("<B", self.number_of_fats))
        raw_boot_sector.extend(struct.pack("<H", self.root_entries))
        raw_boot_sector.extend(struct.pack("<H", self.total_sectors))
        raw_boot_sector.extend(bytes.fromhex(self.media_descriptor))
        raw_boot_sector.extend(struct.pack("<H", self.sectors_per_fat))
        raw_boot_sector.extend(struct.pack("<H", self.sectors_per_track))
        raw_boot_sector.extend(struct.pack("<H", self.number_of_heads))
        raw_boot_sector.extend(struct.pack("<H", self.hidden_sectors))
        raw_boot_sector.extend(bytes.fromhex(self.bootstrap[:480]))
        raw_boot_sector.extend(bytes.fromhex(self.signature))

        return raw_boot_sector

    def __str__(self):
        return (
            f"Jump Instruction: {self.jump_instruction}\n"
            f"OEM Name: {self.oem_name}\n"
            f"Bytes Per Sector: {self.bytes_per_sector}\n"
            f"Sectors Per Cluster: {self.sectors_per_cluster}\n"
            f"Reserved Sectors: {self.reserved_sectors}\n"
            f"Number of FATs: {self.number_of_fats}\n"
            f"Root Entries: {self.root_entries}\n"
            f"Total Sectors: {self.total_sectors}\n"
            f"Media Descriptor: {self.media_descriptor}\n"
            f"Sectors Per FAT: {self.sectors_per_fat}\n"
            f"Sectors Per Track: {self.sectors_per_track}\n"
            f"Number of Heads: {self.number_of_heads}\n"
            f"Hidden Sectors: {self.hidden_sectors}\n"
            f"Bootstrap: {self.bootstrap}\n"
            f"Signature: {self.signature}\n"
        )


class File:
    def __init__(self, name, size, clusters, creation_datetime):
        self.name = name
        self.size = size
        self.clusters = clusters
        self.creation_datetime = creation_datetime

    def __str__(self):
        return f"File: {self.name}, Size: {self.size}, Clusters: {self.clusters}, Creation Date and Time: {self.creation_datetime}"


class Directory:
    def __init__(self, name, clusters, creation_datetime):
        self.name = name
        self.files = []
        self.directories = []
        self.clusters = clusters
        self.creation_datetime = creation_datetime

    def __str__(self, level=0):
        ret = "\t"*level + f"Directory: {self.name}, Clusters: {self.clusters}\n"
        for directory in self.directories:
            ret += directory.__str__(level + 1)
        for file in self.files:
            ret += "\t"*(level + 1) + str(file) + "\n"
        return ret
