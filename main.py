from run import Run
from logger import Logger

def main():
    log = Logger()
    start = Run()
    start.run_model(log)

if __name__ == '__main__':
    main()