import os

# Directory used to keep all output files,
# This directory will also be used as an input directory as
# output from part1 are also contained in this directory.
OUTPUT_DIR = "output_files"

def read_inverted_index(filepath : str) -> tuple[dict[int, dict[int, list]], dict[int, int]]:
    """This function will take in a filename as an argument and
        return the inverted index by reading it. The function assumes
        an input of forward index, and reads it in an inverted format.

    Args:
        filepath (str): Relative file path for the forward index file.

    Returns:
        dict[int, dict[int, list]]: Structure of inverted index, it will be as follows:
                                    termid : {docid : [list of postings]}
        dict[int, int]: Structure which returns the term count after each term.
    """
    inverted_idx = {}
    term_count = {}
    with open(filepath, encoding="utf-8") as _f:
        for line in _f.readlines():
            # reading each line of the file into docid, termid and list of postings.
            docid, termid, *postings = line.strip().replace("\n", "").split("\t")
            # Defining keys in inverted_idx and term_count if they don't exist before.
            inverted_idx.setdefault(termid, {})
            term_count.setdefault(termid, 0)
            inverted_idx[termid][docid] = postings
            term_count[termid] += len(postings)

    return inverted_idx, term_count

def write_to_file(inverted_idx : dict, term_count : dict) -> None:
    """This function applies delta encoding to the inverted index and writes
    the index to a file at the same time. These 2 functions weren't separated
    to reduce an additional loop over the index.

    Args:
        inverted_idx (dict): Inverted index in the format:
        termid : {docid : [list of postings]}
        term_count (dict): dictionary in the format:
        termid : total count of term throughout the corpus
    """
    # Opening both term_index and term_info files for writing.
    f_idx = open(os.path.join(OUTPUT_DIR, "term_index.txt"), "w", encoding="utf-8")
    f_info = open(os.path.join(OUTPUT_DIR, "term_info.txt"), "w", encoding="utf-8")

    for term in inverted_idx:
        # Getting the list of all docids, so we can get an order and set starting docid
        line_offset = f_idx.tell()
        docids = inverted_idx[term].keys()
        # The first docid can be set to 0 as the difference with the starting docid will be
        # the same docid.
        st_docid = 0
        f_idx.write(f"{term}")
        for docid in docids:
            postings = inverted_idx[term][docid]
            # Delta encode and convert postings to desired string format.
            delta_postings = []
            # As the first posting will always be the same value, we will set starting posting = 0,
            # So that we get that same posting.
            st_posting = 0
            for posting in postings:
                # Delta encoding the docid
                delta_docid = int(docid) - st_docid
                posting = int(posting)
                delta_postings.append(f"\t{delta_docid}:{posting - st_posting}")
                st_posting = posting
                # Updating st_docid for the next loop.
                st_docid = int(docid)
            f_idx.write(f"{''.join(delta_postings)}")

        # Ending loop, going to newline for the next term.
        f_idx.write("\n")

        # Storing each term with its lineno, its total corpus count and count of documents
        # it occured in.
        f_info.write(f"{term}\t{line_offset}\t{term_count[term]}\t{len(inverted_idx[term])}\n")

def main():
    """Main function
    """
    print("Reading index...")
    inv_idx, term_count = read_inverted_index(os.path.join(OUTPUT_DIR, "doc_index.txt"))
    print(f"Index read, total terms read: {len(inv_idx)}")
    print("Writing to file.")
    write_to_file(inv_idx, term_count)
    print("File written successfully.")

if __name__ == "__main__":
    main()
