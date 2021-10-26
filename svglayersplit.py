from inksvglib.SvgHierachicalSplitter import SvgHierachicalSplitter


if __name__ == '__main__':
    splitter=SvgHierachicalSplitter()
    res=splitter.fromCommandline()
    print(res)
    exit(0)
