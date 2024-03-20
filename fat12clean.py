
import struct

from fat12 import BootSector, File, Directory
from filesystem import FileSystem, FileSystemEntry


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
    read_directory(f, file_system.root, root_dir_start_sector, boot_sector, True)

    return file_system


def read_directory(f, directory, start_sector, boot_sector, is_root=False):
    f.seek(start_sector * 512)  # Correctly align to the start of the directory
    entries_to_read = boot_sector.root_entries if is_root else boot_sector.sectors_per_cluster * 512 // 32

    for _ in range(entries_to_read):
        raw_entry = f.read(32)

        if raw_entry == b'\x00' * 32:
            continue  # Skip empty entry

        if raw_entry[0] == b'\xe5'[0]:
            continue  # Skip deleted entry

        entry = FileSystemEntry(raw_entry)

        if entry.name in [".", ".."]:
            continue  # Skip special directory entries

        if entry.is_directory():  # Directory entry
            new_directory = Directory(entry.name, entry.creation_datetime)
            directory.directories.append(new_directory)
            first_cluster = entry.first_cluster
            root_dir_sectors = ((boot_sector.root_entries * 32) + (boot_sector.bytes_per_sector - 1)) // boot_sector.bytes_per_sector
            first_data_sector = boot_sector.reserved_sectors + (boot_sector.number_of_fats * boot_sector.sectors_per_fat_short) + root_dir_sectors
            start_sector = ((first_cluster - 2) * boot_sector.sectors_per_cluster) + first_data_sector

            print(f"Reading directory {new_directory.name}, first cluster: {first_cluster}, start sector: {start_sector}")
            saved_position = f.tell()  # Save the current position of the file pointer
            read_directory(f, new_directory, start_sector, boot_sector)
            f.seek(saved_position)  # Restore the file pointer to its original position

        else:  # File entry
            file = File(entry.name, entry.size, entry.first_cluster, entry.creation_datetime)
            directory.files.append(file)


def main():
    with open('floppy.img', 'rb') as f:
        boot_sector = read_boot_sector(f)
        print(boot_sector)

        file_system = read_file_system(f, boot_sector)
        print(file_system)


if __name__ == "__main__":
    main()
