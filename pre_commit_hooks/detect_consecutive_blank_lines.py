import argparse

def main(argv) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument('filenames', nargs='*')
    args = parser.parse_args(argv)

    retcode = 0
    for filename in args.filenames:
        with open(filename, 'rb') as inputfile:
            print(f'{filename}')

    return retcode
