from inksvglib.SvgPageSplitter import SvgPageSplitter


if __name__ == '__main__':
    splitter=SvgPageSplitter()
    res=splitter.fromCommandline()
    print(res)
    exit(0)

