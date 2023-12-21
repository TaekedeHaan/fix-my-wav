import pathlib
import logging

logger = logging.getLogger(__name__)


def read_hex_value(file: pathlib.Path, offset: int, field_size: int):
    maybe_file_handle = try_open_file(file, "rb")
    if maybe_file_handle is None:
        return ""

    file_handle = maybe_file_handle

    hex_data: list[str] = []

    # Ignore the data before the specified offset
    file_handle.seek(offset)

    # Read the specified number of hex values starting at the offset
    for _ in range(field_size):
        hex_byte = file_handle.read(1).hex()

        if not hex_byte:
            logger.error(
                "The provided offset/size goes out of range. Please verify whether these values are correct. If so the file might be corrupted"
            )
            break

        hex_data.append(hex_byte)

    file_handle.close()

    if len(hex_data) != field_size:
        logger.error(
            f"The found hex data does of length {len(hex_data)} not match the expected field size {field_size}. File file might be empty or corrupted, skipping this file"
        )
        return ""

    # Fix order and convert to hex value
    hex_data.reverse()
    return "".join(hex_data).upper()


def set_hex_data(file: pathlib.Path, offset: int, field_size: int, hex_value: str):
    hex_data = [hex_value[i : i + 2] for i in range(0, len(hex_value), 2)]

    if len(hex_data) != field_size:
        logger.error(
            f"The new hex data of length {len(hex_data)} does not match the audio format field size {field_size}. Refusing to set the hex data"
        )
        return False

    hex_data.reverse()

    # try to open file
    maybe_file_handle = try_open_file(file, "r+b")
    if maybe_file_handle is None:
        return ""

    file_handle = maybe_file_handle
    file_handle.seek(offset)

    # Overwrite
    for hex_value in hex_data:
        file_handle.write(bytes((int(hex_value),)))

    file_handle.close()
    return True


def try_open_file(file: pathlib.Path, mode: str):
    try:
        return open(file, mode)
    except PermissionError as e:
        logger.warning(
            f"Failed to open file {file.name}: the permission was denied. Caught the following exception:\n{e}"
        )
        return None
    except Exception as e:
        logger.warning(
            f"Failed to open file {file.name}. Caught the following exception:\n{e}"
        )
        return None
