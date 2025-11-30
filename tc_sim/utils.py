import os

def prepare_output_file(file_path: str) -> (str, str, str):
    directory = os.path.dirname(file_path)
    file_name_with_extension = os.path.basename(file_path)
    file_name_without_extension = os.path.splitext(file_name_with_extension)[0]
    extension = os.path.splitext(file_name_with_extension)[1]
    if not os.path.exists(directory):
        os.makedirs(directory)
    if os.path.exists(file_path):
        os.remove(file_path)
    return directory, file_name_without_extension, extension
