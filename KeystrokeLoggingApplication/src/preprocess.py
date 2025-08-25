input_file = r'c:\Users\Admin\Desktop\Keystroke_analysis\KeystrokeLoggingApplication\src\Keystrokes_cleaned.csv'
output_file = r'c:\Users\Admin\Desktop\Keystroke_analysis\KeystrokeLoggingApplication\src\Keystrokes_cleaned_modified.csv'

with open(input_file, 'r', encoding='utf-8') as infile, open(output_file, 'w', encoding='utf-8') as outfile:
    for line in infile:
        if 'H.l,' in line:
            # Keep everything up to and including 'H.l'
            before = line.split('H.l,')[0] + 'H.l\n'
            outfile.write(before)
        else:
            outfile.write(line)