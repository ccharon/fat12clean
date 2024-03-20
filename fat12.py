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
    def __init__(self, name, size, clusters, creation_datetime):
        self.name = name
        self.size = size
        self.clusters = clusters
        self.creation_datetime = creation_datetime

    def __str__(self):
        return f"File: {self.name}, Size: {self.size}, Clusters: {self.clusters}, Creation Date and Time: {self.creation_datetime}"


class Directory:
    def __init__(self, name, creation_datetime):
        self.name = name
        self.files = []
        self.directories = []
        self.creation_datetime = creation_datetime

    def __str__(self, level=0):
        ret = "\t"*level + f"Directory: {self.name}\n"
        for directory in self.directories:
            ret += directory.__str__(level + 1)
        for file in self.files:
            ret += "\t"*(level + 1) + str(file) + "\n"
        return ret
