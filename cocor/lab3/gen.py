import os
import sys

atg_file = sys.argv[1]
sample_file = sys.argv[2]
print('.atg file: ' + atg_file)
print('sample file: ' + sample_file)
os.system('python ../Coco.py ' + atg_file + ' > output.txt')
print('>>> Generated Parser + Scanner')
gen_result = open('output.txt').readlines()
for x in gen_result:
    print(x.replace('\n', ' ').replace('\r', ''))
print('')

os.system('python run.py ' + sample_file)
