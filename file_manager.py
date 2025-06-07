import os
import shutil
import re
import pandas as pd
import numpy as np
from datetime import datetime

"""
The functions sloth_gui_to_2sp and sloth2p are thanks to Luka Guzenko. 
"""
class FileManager:
    def sloth_gui_to_s2p(self, source_folder, target_folder):
        """
        :param source_folder: Folder where the csv files of the sloth gui measurements are saved.
        :param target_folder: Target folder where s2p files will be saved.
        :return: None
        """
        for filename in os.listdir(source_folder):
            if filename.lower().endswith('.csv'):
                inpath = os.path.join(source_folder, filename)
                filename_prefix = os.path.splitext(filename)[0]  # Remove .csv
                self.sloth2p(inpath, target_folder, filename_prefix)
                print(f"File: {filename.lower()} written to touchstone format")

    def sloth2p(self,inpath: str, outdir: str, filename_prefix: str, name="Default"):
        """
        :param inpath: source directory
        :param outdir: target directory
        :param filename_prefix: file name without s2p
        :param name: written to s2p file
        :return: None
        """
        sparams = pd.read_csv(inpath, delimiter=',', header=5, skipinitialspace=True)
        # Convert radians to degrees
        for angle_col in ['S11 Ang', 'S21 Ang', 'S12 Ang', 'S22 Ang']:
            sparams[angle_col] = sparams[angle_col] * 180 / np.pi

        sparams['RF Frequency'] = sparams['RF Frequency'].astype('int64')

        for rep in sparams['repetition'].dropna().unique():
            spwr = sparams[sparams['repetition'] == rep]

            out_filename = f"{filename_prefix}.s2p"
            out_filepath = os.path.join(outdir, out_filename)

            with open(out_filepath, 'w') as file:
                file.write('! ETH Zürich\n')
                file.write(f'! {name}\n')
                file.write(f'! {out_filename}\n')
                file.write('!\n')
                file.write('# Hz S DB R 50\n')
                file.write('!\tf\tS11\tS21\tS12\tS22\t\t\t\t\n')
                file.write('!\tHz\tMAG\tANG\tMAG\tANG\tMAG\tANG\tMAG\tANG\n')
                file.write(spwr.to_csv(sep=' ', columns=[
                    'RF Frequency', 'S11 Mag', 'S11 Ang', 'S21 Mag', 'S21 Ang',
                    'S12 Mag', 'S12 Ang', 'S22 Mag', 'S22 Ang'
                ], header=False, index=False))

    def reformat_s2p_files(self, source_folder, target_folder, copy_files = True):
        """
        Based on timestamp the format will be ID based, which matches the id-s on Slumble Chip
        :param source_folder: folder in which s2p files are stored
        :param target_folder: target folder where results will be copied/moved
        :param copy_files: Copy or move original files?
        :return: None
        """
        os.makedirs(target_folder, exist_ok=True)

        file_info = []
        pattern = re.compile(r'_(\d+)_ID\d+_SParameter_(\d{4}-\d{2}-\d{2}_\d{6})')

        for filename in os.listdir(source_folder):
            match = pattern.search(filename)
            if match:
                number = match.group(1)
                timestamp_str = match.group(2)
                try:
                    timestamp = datetime.strptime(timestamp_str, "%Y-%m-%d_%H%M%S")
                except ValueError:
                    print(f"Skipped (bad timestamp): {filename}")
                    continue
                file_info.append((number, timestamp, filename))
            else:
                print(f"Skipped (no match): {filename}")

        # === GROUP AND SORT FILES ===
        from collections import defaultdict

        grouped = defaultdict(list)
        for number, timestamp, filename in file_info:
            grouped[number].append((timestamp, filename))

        # === RENAME AND COPY/MOVE ===
        for number, entries in grouped.items():
            entries.sort()  # Sort by timestamp (oldest first)
            for idx, (timestamp, filename) in enumerate(entries):
                extension = os.path.splitext(filename)[1]  # optional, use if files have extensions
                new_filename = f"File_{number}_{idx}.s2p"  # You can add + extension if needed
                src_path = os.path.join(source_folder, filename)
                dst_path = os.path.join(target_folder, new_filename)
                if copy_files:
                    shutil.copy2(src_path, dst_path)
                else:
                    shutil.move(src_path, dst_path)
                print(f"{'Copied' if copy_files else 'Moved'}: {filename} → {new_filename}")
