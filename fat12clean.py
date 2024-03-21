
import struct

from fat12 import BootSector, File, Directory
from filesystem import FileSystem, FileSystemEntry


def read_file_system(f, boot_sector, fat):
    file_system = FileSystem()
    root_dir_start_sector = boot_sector.reserved_sectors + (boot_sector.number_of_fats * boot_sector.sectors_per_fat)
    read_directory(f, file_system.root, root_dir_start_sector, boot_sector, fat, True)

    return file_system


def read_directory(f, directory, start_sector, boot_sector, fat, is_root=False):
    f.seek(start_sector * 512)  # Correctly align to the start of the directory
    entries_to_read = boot_sector.root_entries if is_root else boot_sector.sectors_per_cluster * 512 // 32

    for _ in range(entries_to_read):
        raw_entry = f.read(32)

        if raw_entry == b'\x00' * 32:
            continue  # Skip empty entry

        if raw_entry[0] == b'\xe5'[0]:
            continue  # Skip deleted entry

        entry = FileSystemEntry(raw_entry)
        # print(entry)

        if entry.name in [".", ".."]:
            continue  # Skip special directory entries

        if entry.is_volume_label():
            continue  # Skip volume label

        if entry.is_directory():  # Directory entry
            entry.clusters = populate_clusters(entry.first_cluster, fat)
            new_directory = Directory(entry.name, entry.clusters, entry.creation_datetime)
            directory.directories.append(new_directory)
            root_dir_sectors = ((boot_sector.root_entries * 32) + (boot_sector.bytes_per_sector - 1)) // boot_sector.bytes_per_sector
            first_data_sector = boot_sector.reserved_sectors + (boot_sector.number_of_fats * boot_sector.sectors_per_fat) + root_dir_sectors
            start_sector = ((entry.first_cluster - 2) * boot_sector.sectors_per_cluster) + first_data_sector

            # print(f"Reading directory {new_directory.name}, first cluster: {first_cluster}, start sector: {start_sector}")
            saved_position = f.tell()  # Save the current position of the file pointer
            read_directory(f, new_directory, start_sector, boot_sector, fat)
            f.seek(saved_position)  # Restore the file pointer to its original position

        else:  # File entry
            entry.clusters = populate_clusters(entry.first_cluster, fat)
            file = File(entry.name, entry.size, entry.clusters, entry.creation_datetime)
            directory.files.append(file)


def populate_clusters(first_cluster, fat):
    """Populate the clusters list by reading the FAT."""
    current_cluster = first_cluster

    clusters = [first_cluster]

    while True:
        next_cluster = fat[current_cluster]
        if next_cluster >= 0xFF8:  # End of file for FAT12
            break
        clusters.append(next_cluster)
        current_cluster = next_cluster

    return clusters


def read_fat(f, fat_start, fat_size):
    """Read the FAT from a file."""
    f.seek(fat_start)
    fat_data = f.read(fat_size)
    # Convert the data to an array of 12-bit entries
    fat = []
    for i in range(0, len(fat_data), 3):
        # Every three bytes contain two 12-bit entries
        entry1 = struct.unpack("<H", fat_data[i:i+2])[0] & 0x0FFF
        entry2 = struct.unpack("<H", fat_data[i+1:i+3])[0] >> 4
        fat.append(entry1)
        fat.append(entry2)
    return fat


def get_cluster_start(cluster_number, boot_sector):
    """Get the start of a cluster in bytes."""
    # Calculate the start of the data region
    root_dir_sectors = ((boot_sector.root_entries * 32) + (boot_sector.bytes_per_sector - 1)) // boot_sector.bytes_per_sector
    first_data_sector = boot_sector.reserved_sectors + (boot_sector.number_of_fats * boot_sector.sectors_per_fat) + root_dir_sectors
    data_start = first_data_sector * boot_sector.bytes_per_sector

    # Calculate the start of the cluster
    cluster_start = data_start + ((cluster_number - 2) * boot_sector.sectors_per_cluster * boot_sector.bytes_per_sector)

    return cluster_start


def get_occupied_clusters(file_system):
    """Get a list of all clusters occupied by files in the file system."""
    occupied_clusters = []
    for directory in file_system.root.directories:
        occupied_clusters.extend(directory.clusters)

        for file in directory.files:
            occupied_clusters.extend(file.clusters)

    return occupied_clusters


def get_free_clusters(boot_sector, fat, occupied_clusters):
    """Get a list of all free clusters in the file system."""
    # Calculate the total size of the disk
    total_disk_size = boot_sector.total_sectors * boot_sector.bytes_per_sector

    # Calculate the size of the reserved region, the FATs, and the root directory
    root_dir_size = boot_sector.root_entries * 32
    reserved_and_fats_size = (boot_sector.reserved_sectors + boot_sector.number_of_fats * boot_sector.sectors_per_fat) * boot_sector.bytes_per_sector + root_dir_size

    # Calculate the size of the data region
    data_region_size = total_disk_size - reserved_and_fats_size

    # Calculate the size of a cluster
    cluster_size = boot_sector.sectors_per_cluster * boot_sector.bytes_per_sector

    # Calculate the total number of clusters
    total_clusters = data_region_size // cluster_size

    print(total_clusters)

    all_clusters = list(range(2, total_clusters + 2))  # All possible clusters
    free_clusters = [cluster for cluster in all_clusters if cluster not in occupied_clusters]
    return free_clusters


def main():
    with open('floppy.img', 'rb') as f:
        raw_boot_sector = f.read(512)
        boot_sector = BootSector(raw_boot_sector)
        print(boot_sector)

        fat_start = boot_sector.reserved_sectors * boot_sector.bytes_per_sector
        fat_size = boot_sector.sectors_per_fat * boot_sector.bytes_per_sector
        fat = read_fat(f, fat_start, fat_size)

        # cluster_size = boot_sector.sectors_per_cluster * boot_sector.bytes_per_sector

        # clusters = populate_clusters(673, fat)
        # data = b''
        # bytes_to_read = 38272

        # for c in clusters:
        #    position = get_cluster_start(c, boot_sector)
        #    f.seek(position)
        #    data_size = cluster_size if bytes_to_read > cluster_size else bytes_to_read
        #    cluster = f.read(data_size)
        #    bytes_to_read -= data_size
        #    data += cluster

        # print(data.decode('ascii', errors='replace').strip())

        file_system = read_file_system(f, boot_sector, fat)

        occupied_clusters = get_occupied_clusters(file_system)
        print(f"Occupied clusters: {occupied_clusters}")

        free_clusters = get_free_clusters(boot_sector, fat, occupied_clusters)
        print(f"Free clusters: {free_clusters}")

        print(file_system)


if __name__ == "__main__":
    main()
