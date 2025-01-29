import sys
import citybikes.hyper.publisher
import citybikes.hyper.subscriber

def main():
    action = sys.argv[1]
    sys.exit(getattr(citybikes.hyper, action).main())

if __name__ == "__main__":
    main()
