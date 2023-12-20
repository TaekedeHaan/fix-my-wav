import pathlib
from typing import List

WAV_EXTENSION = '*.wav'
AUDIO_FORMAT_OFFSET = 20
AUDIO_FORMAT_FIELD_SIZE = 2
WAVE_FORMAT_EXTENSIBLE = 65534
WAVE_FORMAT_PCM = 1

def read_hex_value(file: pathlib.Path, offset: int, field_size: int):
    print(f"Opening {file.name} to read its contents")
    hex_data = []
    file_handle = open(file, 'rb')

    # Ignore the data before the specfied offset
    file_handle.seek(offset)
    
    # Read the spcified number of hex values starting at the offset 
    for _ in range(field_size):
        hex_byte = file_handle.read(1).hex()

        if not hex_byte: 
            print("The provided offset/size goes out of range. Please verify whether these values are correct. If so the file might be corrpted")
            break

        hex_data.append(hex_byte)

    print(f"Closing {file.name}")
    file_handle.close()

    if (len(hex_data) != AUDIO_FORMAT_FIELD_SIZE):
        print("The found hex data does not match the expected field size. File file might be empty or corrupted, skipping this file")
        return ''

    # Fix order and convert to hex value
    hex_data.reverse()
    return ''.join(hex_data).upper()

def set_hex_data(file: pathlib.Path, offset: int, field_size: int, hex_value: str):
    hex_data = [hex_value[i:i+2] for i in range(0, len(hex_value), 2)]
    
    if (len(hex_data) != AUDIO_FORMAT_FIELD_SIZE):
        print("The new hex data does not match the audio format field size. Can not modify the bad files")
        return False

    hex_data.reverse()

    print(f"Opening {file.name} to edit its contents")
    file_handle = open(file, 'r+b')
    file_handle.seek(offset)

    # Overwrite
    for hex_value in hex_data:
        file_handle.write(bytes((int(hex_value), )))

    print(f"Closing {file.name}")
    file_handle.close()
    return True


class Core:
    def __init__(self):
        self.base_path = pathlib.Path.home()
        self.files = []
        self.suspicious_files = []

        self.suspicious_hex_value = f"{WAVE_FORMAT_EXTENSIBLE:04X}"
        self.new_hex_value = f"{WAVE_FORMAT_PCM:04X}"


    def find_wav_files(self):
        if not pathlib.Path.is_dir(self.base_path):
            print("The provided base path {} does not exist")
            return False
    
        self.files = list(self.base_path.rglob(WAV_EXTENSION))
        return len(self.files) > 0

    def find_suspicious_wav_files(self):
        if not self.files:
            print("Can not look for suspicious files among files: the files are still empty")
            return False
        
        for file in self.files:
            if not self.is_wav_file_suspicious(file):
                continue

            self.suspicious_files.append(file)
            print(f"The wav file {file.name} contains the key {WAVE_FORMAT_EXTENSIBLE} at the specified location. Storing the file name...")

        return len(self.suspicious_files) > 0

    def is_wav_file_suspicious(self, file: pathlib.Path):
        hex_value = read_hex_value(file, AUDIO_FORMAT_OFFSET, AUDIO_FORMAT_FIELD_SIZE)
        if not hex_value: 
            print("Failed to read the hex value from the file")
            return False

        int_value = int(hex_value, 16)
        if int_value != WAVE_FORMAT_EXTENSIBLE:
            return False

        return True

    def fix_suspicious_wav_files(self):
        if not self.files:
            print("Can not fix suspicious files: first find some suspicious files!")
            return False

        print(f"Will replace {self.suspicious_hex_value} at offset {AUDIO_FORMAT_OFFSET} and field size {AUDIO_FORMAT_FIELD_SIZE} with {self.new_hex_value}")
        overall_success = True
        for wav_file in self.suspicious_files:
            # override hex data in file
            success = set_hex_data(wav_file, AUDIO_FORMAT_OFFSET, AUDIO_FORMAT_FIELD_SIZE, self.new_hex_value)
            if not success:
                print(f"Failed to fix {wav_file.name}")
                overall_success = False

            # verify whether problem was fixed
            is_still_suspisious = self.is_wav_file_suspicious(wav_file)
            if is_still_suspisious:
                print(f"Wav file {wav_file.name} is still suspicious after trying to apply fix")
                overall_success = False

        return overall_success

def main():
    core = Core()

    # set base path
    user_path = pathlib.Path.home()
    base_path = user_path / "Downloads" / "Various Artists - Ritmo Fantasía- Balearic Spanish Synth-Pop- Boogie and House (1982-1992) -Compiled by DJ Trujillo"
    core.base_path = base_path

    found_wav_files = core.find_wav_files()
    if not found_wav_files:
        print(f"Did not find any wav files at {base_path}, exitting")
        return

    print(f"Found {len(core.files)}, at {core.base_path}")

    found_suspicious_wav_files = core.find_suspicious_wav_files()
    if not found_suspicious_wav_files:
        print(f"Did not find any suspisous wav files at {core.base_path}, exitting")
        return

    print(f"Found {len(core.suspicious_files)} suspscious wav files")
    
    fixed_suspicious_wav_files = core.fix_suspicious_wav_files()
    if not fixed_suspicious_wav_files:
        print(f"Failed to fix the suspisous wav files at {core.base_path}, exitting")
        return

    print(f"Successfully fixed {len(core.suspicious_files)} suspicious wav files")

if __name__ == "__main__":
    main()