import os
import json

# book formats
BOOK_FORMATS = {".pdf", ".epub", ".xml"}

def find_accepted_files_non_recursive(root_dir):
    matching_files = []
    
    for filename in os.listdir(root_dir):
        file_path = os.path.join(root_dir, filename)
        if os.path.isfile(file_path):
            ext = os.path.splitext(filename)[1].lower()
            if ext in BOOK_FORMATS:
                matching_files.append(file_path)

    return matching_files


if __name__ == "__main__":
    root_directory = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../"))
    
    # store file paths in a list
    files_list = find_accepted_files_non_recursive(root_directory)

    if files_list:
        
        # save file paths to a JSON file for chunking
        with open("found_files.json", "w") as f:
            json.dump(files_list, f, indent=4)
        print("\nFile paths saved to found_files.json")
        
    else:
        print("\nNo files found with the accepted formats.")
