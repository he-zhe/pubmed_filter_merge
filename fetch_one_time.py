from app.pubmed_filter import fetch_and_filter
import sys

if __name__ == "__main__":
    if len(sys.argv) > 1:
        fetch_and_filter(int(sys.argv[-1]))
    else:
        fetch_and_filter()
