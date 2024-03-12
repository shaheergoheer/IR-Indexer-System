import os
from html.parser import HTMLParser
import sys

# Constants
OUTPUT_DIR = "output_files" # Output directory.

class CustomHTMLParser(HTMLParser):
    '''
    A custom class to store html contents from the parsed object.
    Uses HTMLParser as parent class.
    '''
    def __init__(self, *, convert_charrefs: bool = ...) -> None:
        super().__init__(convert_charrefs=convert_charrefs)
        self.content : str = "" # HTML content for a file will be stored in this variable.

    def handle_data(self, data: str) -> str:
        # Overloading the handle_data function. This function will be called by
        # HTMLParser when it is processing html from given content.
        self.content += data
        self.content += '\n' # Adding the data to self.content for easy extraction.

def get_stopwords(inputfile : str) -> list:
    """Function to read the inputfile and return tokenized stopwords.
       This function assumes that the stopwords are separated by \n.

    Args:
        inputfile (str): stopwords file

    Returns:
        list: list of stopwords
    """

    # Extracting stopwords from provided text file.
    stopwords = []
    with open(inputfile, encoding="utf-8") as _f:
        stopwords.extend(_f.read().split("\n"))

    return stopwords

def main(argc : int, argv : list):
    """main function, it will handle the arguments that are passed through sys.

    Args:
        argc (int): count of passed arguments
        argv (list): list containing the passed arguments, first argument is filename.
    """
    if argc == 1:
        print("Error: No directory passed to search for documents in.")
        return

    folder = argv[1] # Input directory.

    # Data structures to store the data which will later be written to files.
    docids = dict()
    termids = dict()
    doc_index = dict()

    # Creating an output directory for output files.
    try:
        os.mkdir(OUTPUT_DIR)
    except FileExistsError:
        pass

    stopwords = get_stopwords("Urdu stopwords.txt")

    # pylint: disable=C0103
    # Enumerator objects to set IDS for documents and terms.
    doc_enum = 1
    term_enum = 1

    # Iterating over every file in the input folder
    for doc in os.listdir(folder):
        # Extracting the docname by splitting the extension away.
        docname = doc.rsplit(".", 1)[0]
        # If docname already is a key in docids, try will successfully run,
        # otherwise generate a KeyError, which will cause the except to trigger.
        try:
            docids[docname]
        except KeyError:
            docids[docname] = doc_enum
            doc_enum += 1

        # Opening the document.
        with open(os.path.join(folder, doc), encoding="utf-8") as f:
            content = f.read()
            # Instantiating a CustomHTMLParser object for each file,
            # and parsing it by feeding the content in.
            parser = CustomHTMLParser()
            parser.feed(content)
            # After feeding the content, parser's content attribute should have
            # all the text within the content.
            content = parser.content
            # Replacing \n with ' ' so that we can tokenize easily.
            content = content.replace("\n", " ")
            # Removing all english characters.
            content = ''.join([l for l in content if not (('a' <= l <= 'z') or ('A' <= l <= 'Z'))])
            # Tokenizing on spaces and \t as well.
            tokens = content.strip().replace("\t", " ").split(" ")
            for i, tok in enumerate(tokens):
                if tok in stopwords:
                    continue

                # If tok already is a key in termids, try will successfully run,
                # otherwise generate a KeyError, which will cause the except to trigger.
                try:
                    termids[tok]
                except KeyError:
                    termids[tok] = term_enum
                    term_enum += 1

                # Forming doc_index in the given way:-
                # docid : {termid : [list of postings]}
                doc_index.setdefault(docids[docname], dict())
                doc_index[docids[docname]].setdefault(termids[tok], list())
                doc_index[docids[docname]][termids[tok]].append(i)

    # Saving docids to a file.
    with open(os.path.join(OUTPUT_DIR, "docids.txt"), "w", encoding="utf-8") as f:
        for doc, dID in docids.items():
            f.write(f"{dID}\t{doc}\n")

    # Saving termids to a file.
    with open(os.path.join(OUTPUT_DIR, "termids.txt"), "w", encoding="utf-8") as f:
        for term, tID in termids.items():
            f.write(f"{tID}\t{term}\n")

    # Saving doc_index to a file.
    with open(os.path.join(OUTPUT_DIR, "doc_index.txt"), "w", encoding="utf-8") as f:
        for docid, val in doc_index.items():
            for termid, postings in val.items():
                f.write("{docid}\t{termid}\t{postings}\n".format(
                    **{
                    "docid" : docid,
                    "termid" : termid,
                    "postings" : '\t'.join([str(p) for p in postings])
                    }
                    ))

if __name__ == "__main__":
    args = sys.argv
    main(len(args), args)
