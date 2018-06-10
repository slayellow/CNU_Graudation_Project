from run import Run

def main():
    start = Run()
    object, path = start.load_path()
    start.run_model(object ,path)

if __name__ == '__main__':
    main()