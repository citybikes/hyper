import sys
import hyper.producer

def main():
    action = sys.argv[1]
    sys.exit(getattr(hyper, action).main())

if __name__ == "__main__":
    main()
