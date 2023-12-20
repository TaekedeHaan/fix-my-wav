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
        print(hex_value.encode())

    print(f"Closing {file.name}")
    file_handle.close()
    return True

def main():
    user_path = pathlib.Path.home()
    base_path = user_path / "Downloads" / "Various Artists - Ritmo Fantasía- Balearic Spanish Synth-Pop- Boogie and House (1982-1992) -Compiled by DJ Trujillo"

    pathlib.Path.is_dir(base_path)

    wav_files = list(base_path.rglob(WAV_EXTENSION))
    if not wav_files:
        print(f"Did not find any wav files at {base_path}, exitting")
        return

    print(f"Found {len(wav_files)}, at {base_path}")

    suspicious_wav_files = []
    for wav_file in wav_files:
        hex_value = read_hex_value(wav_file, AUDIO_FORMAT_OFFSET, AUDIO_FORMAT_FIELD_SIZE)
        if not hex_value: continue
        
        int_value = int(hex_value, 16)
        if int_value != WAVE_FORMAT_EXTENSIBLE:
            print(f"The wav file {wav_file.name} does not contain the key {int_value} at the specified location")
            continue

        print(f"The wav file {wav_file.name} contains the key {int_value} at the specified location. Storing the file name...")
        suspicious_wav_files.append(wav_file)

    if not suspicious_wav_files:
        print(f"Did not find any suspisous wav files at {base_path}, exitting")
        return

    print(f"Found {len(suspicious_wav_files)} suspscious wav files")
    new_hex_value = f"{WAVE_FORMAT_PCM:04X}"
    

    print(f"Will replace {hex_value} at offset {AUDIO_FORMAT_OFFSET} and field size {AUDIO_FORMAT_FIELD_SIZE} with {new_hex_value}")
    for wav_file in suspicious_wav_files:
        success = set_hex_data(wav_file, AUDIO_FORMAT_OFFSET, AUDIO_FORMAT_FIELD_SIZE, new_hex_value)
        break


if __name__ == "__main__":
    main()