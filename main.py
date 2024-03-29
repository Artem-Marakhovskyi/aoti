import lexer
import syntax

def read_and_run_lexer(filename = None):
    return lexer.Lexer().analyze(get_file_content(filename))


def get_file_content(filename):
    file = open(filename)
    return ''.join(file.readlines())

# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    filename = 'lang_samples/for.alng'
    print(get_file_content(filename))
    for x in read_and_run_lexer(filename):
        print(x)
