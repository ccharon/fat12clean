
import struct


# The boot sector of a FAT filesystem
class BootSector:
    def __init__(self):
        self.jump_instruction = ""
        self.oem_name = ""
        self.bytes_per_sector = 0
        self.sectors_per_cluster = 0
        self.reserved_sectors = 0
        self.number_of_fats = 0
        self.root_entries = 0
        self.total_sectors_short = 0
        self.media_descriptor = 0
        self.sectors_per_fat_short = 0
        self.sectors_per_track = 0
        self.number_of_heads = 0
        self.hidden_sectors = 0
        self.total_sectors_long = 0

    def __str__(self):
        return (
            f"Jump Instruction: {self.jump_instruction}\n"
            f"OEM Name: {self.oem_name}\n"
            f"Bytes Per Sector: {self.bytes_per_sector}\n"
            f"Sectors Per Cluster: {self.sectors_per_cluster}\n"
            f"Reserved Sectors: {self.reserved_sectors}\n"
            f"Number of FATs: {self.number_of_fats}\n"
            f"Root Entries: {self.root_entries}\n"
            f"Total Sectors (short): {self.total_sectors_short}\n"
            f"Media Descriptor: {self.media_descriptor}\n"
            f"Sectors Per FAT (short): {self.sectors_per_fat_short}\n"
            f"Sectors Per Track: {self.sectors_per_track}\n"
            f"Number of Heads: {self.number_of_heads}\n"
            f"Hidden Sectors: {self.hidden_sectors}\n"
            f"Total Sectors (long): {self.total_sectors_long}\n"
        )


class File:
    def __init__(self, name, size, clusters):
        self.name = name
        self.size = size
        self.clusters = clusters

    def __str__(self):
        return f"File: {self.name}, Size: {self.size}, Clusters: {self.clusters}"


class Directory:
    def __init__(self, name):
        self.name = name
        self.directories = []
        self.files = []

    def __str__(self, level=0):
        ret = "\t"*level + f"Directory: {self.name}\n"
        for directory in self.directories:
            ret += directory.__str__(level + 1)
        for file in self.files:
            ret += "\t"*(level + 1) + str(file) + "\n"
        return ret


class FileSystem:
    def __init__(self):
        self.root = Directory("root")

    def __str__(self):
        return str(self.root)


class DirectoryEntry:
    def __init__(self, entry):
        self.name = entry[:11].decode('ascii', errors='replace').strip()
        self.attributes = entry[11]
        self.first_cluster = struct.unpack("<H", entry[26:28])[0]
        self.size = struct.unpack("<I", entry[28:32])[0]

    def is_directory(self):
        return self.attributes & 0x10

    def is_file(self):
        return not self.is_directory()

    def __str__(self):
        return f"Name: {self.name}, Attributes: {self.attributes}, First Cluster: {self.first_cluster}, Size: {self.size}"

# Python
def read_boot_sector(f):
    boot_sector = BootSector()
    f.seek(0)

    boot_sector.jump_instruction = ' '.join(f'{i:02x}' for i in f.read(3))
    boot_sector.oem_name = f.read(8).decode('ascii')
    boot_sector.bytes_per_sector = struct.unpack("<H", f.read(2))[0]
    boot_sector.sectors_per_cluster = struct.unpack("<B", f.read(1))[0]
    boot_sector.reserved_sectors = struct.unpack("<H", f.read(2))[0]
    boot_sector.number_of_fats = struct.unpack("<B", f.read(1))[0]
    boot_sector.root_entries = struct.unpack("<H", f.read(2))[0]
    boot_sector.total_sectors_short = struct.unpack("<H", f.read(2))[0]
    boot_sector.media_descriptor = struct.unpack("<B", f.read(1))[0]
    boot_sector.sectors_per_fat_short = struct.unpack("<H", f.read(2))[0]
    boot_sector.sectors_per_track = struct.unpack("<H", f.read(2))[0]
    boot_sector.number_of_heads = struct.unpack("<H", f.read(2))[0]
    boot_sector.hidden_sectors = struct.unpack("<I", f.read(4))[0]
    boot_sector.total_sectors_long = struct.unpack("<I", f.read(4))[0]

    return boot_sector


def read_file_system(f, boot_sector):
    file_system = FileSystem()
    root_dir_start_sector = boot_sector.reserved_sectors + (boot_sector.number_of_fats * boot_sector.sectors_per_fat_short)
    print(f"Reserved Sectors: {boot_sector.reserved_sectors}")
    print(f"Number of FATs: {boot_sector.number_of_fats}")
    print(f"Sectors Per FAT: {boot_sector.sectors_per_fat_short}")
    print(f"Calculated Root Directory Start Sector: {root_dir_start_sector}")
    read_directory(f, file_system.root, root_dir_start_sector, boot_sector, True)

    return file_system


def read_directory(f, directory, start_sector, boot_sector, is_root=False):
    f.seek(start_sector * 512)  # Correctly align to the start of the directory
    entries_to_read = boot_sector.root_entries if is_root else boot_sector.sectors_per_cluster * 512 // 32
    subdirectories = []

    for _ in range(entries_to_read):
        raw_entry = f.read(32)

        if raw_entry == b'\x00' * 32:
            continue  # Skip empty entry

        if raw_entry[0] == b'\xe5'[0]:
            continue  # Skip deleted entry

        entry = DirectoryEntry(raw_entry)

        if entry.is_directory():  # Directory entry
            new_directory = Directory(entry.name)
            directory.directories.append(new_directory)
            first_cluster = entry.first_cluster

            sectors_per_fat = boot_sector.sectors_per_fat_short
            reserved_sectors = boot_sector.reserved_sectors
            number_of_fats = boot_sector.number_of_fats
            sectors_per_cluster = boot_sector.sectors_per_cluster
            start_sector = first_cluster * sectors_per_cluster + reserved_sectors + number_of_fats * sectors_per_fat
            read_directory(f, new_directory, start_sector, boot_sector)

        else:  # File entry
            file = File(entry.name, entry.size, entry.first_cluster)
            directory.files.append(file)


def main():
    with open('floppy.img', 'rb') as f:
        boot_sector = read_boot_sector(f)
        print(boot_sector)

        file_system = read_file_system(f, boot_sector)
        print(file_system)


if __name__ == "__main__":
    main()
