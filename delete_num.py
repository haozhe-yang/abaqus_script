import os
import re

def remove_lines_starting_with_numbers(input_file, output_file):
    with open(input_file, 'r') as infile, open(output_file, 'w') as outfile:
        for line in infile:
            if not re.match(r'^\s*\d', line):
                outfile.write(line)

def process_multiple_files(file_list, output_folder):
    for file_name in file_list:
        input_file_path = os.path.join(input_folder, file_name)
        # Generate the output file name by prefixing "cleaned_" to the original file name
        output_file_name = 'cleaned_' + os.path.basename(file_name)
        output_file_path = os.path.join(output_folder, output_file_name)

        remove_lines_starting_with_numbers(input_file_path, output_file_path)
        print(f"Processed {input_file_path}, saved as {output_file_path}.")

# List of files with full paths specified
file_list = ['a.txt', 'b.txt', 'c.txt']
# Input and output folder paths
input_folder = r"D:\Git\\"  # Make sure the path is correct here
output_folder = r"D:\Git\\"

# Ensure the output folder exists
if not os.path.exists(output_folder):
    os.makedirs(output_folder)

# Process each file in the list
process_multiple_files(file_list, output_folder)