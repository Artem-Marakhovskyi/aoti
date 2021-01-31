import io
import Scanner as s
import Parser as p
import sys

sample_file = sys.argv[1]
print('>>> Runinng sample file: ' + sample_file)
f_content = str.join('', open(sample_file).readlines())
print(f_content)
print('')
scanner = s.Scanner(f_content)
parser = p.Parser()
parser.Parse(scanner)


