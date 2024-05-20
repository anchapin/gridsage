import csv

# Input and output file names
input_file = 'input.csv'
output_file = 'output.csv'

with open(input_file, 'r', newline='') as infile, open(output_file, 'w', newline='') as outfile:
    reader = csv.reader(infile)
    writer = csv.writer(outfile, delimiter=';')

    for row in reader:
        # Join the row into a single string with semicolons
        joined_row = ';'.join(row)
        # Write the single string as a single-element list to keep it in one column
        writer.writerow([joined_row])

print(f"Conversion complete. Check the file {output_file} for the result.")