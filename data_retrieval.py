import argparse
import os

# The output directory where all the files are kept.
OUTPUT_DIR = "output_files"

def set_arguments() -> argparse.ArgumentParser:
    """This function will set the arguments are return a parser object.

    Returns:
        argparse.ArgumentParser: A parser object from which arguments can be
                                extracted.
    """

    parser = argparse.ArgumentParser(
        prog="Urdu Indexer",
        description="You can search for urdu terms from provided documents" +
        ", or search for documents.",
    )
    parser.add_argument(
        "--doc",
        metavar="DOCNAME",
        help="Pass a document name to get statistics for that document" +
        " or pass alongside --term to get positions for that term.",
        type=str
        )
    parser.add_argument(
        "--term",
        help="Pass a term to get statistics for that term" +
        " or pass alongside --doc to get positions for that term.",
        type=str
        )

    return parser

def get_ids(filename : str) -> dict[str, int]:
    """This function is used to read ids from the given filename.

    Args:
        filename (str): The filename containing the ids(either for doc or term).

    Returns:
        dict[str, int]: Resultant dictionary containing the following pair:
                        {term/doc : ID}
    """
    with open(os.path.join(OUTPUT_DIR, filename), encoding='utf-8') as _f:
        # Reading each line.
        id_list = {}
        for line in _f.readlines():
            # As the file structure is ID\tOBJECT, parsing in this format.
            # Removing all prevailing \n with replace.
            obj_id, obj = line.replace("\n", "").split("\t")
            # Setting the dictionary.
            id_list[obj] = int(obj_id)

    return id_list

def get_term_info(filename : str) -> dict[int, dict]:
    """This function is used to read term info from the given filename

    Args:
        filename (str): The filename containing term info.

    Returns:
        dict[int, dict]: The resultant object with the following key-value pair:
                        {
                            termID : {
                                "Offset" : file_offset,
                                "Total" : total_count,
                                "Total Docs" : doc_count
                            }
                        }
    """
    with open(os.path.join(OUTPUT_DIR, filename), encoding="utf-8") as _f:
        # Reading each line.
        term_info = {}
        for line in _f.readlines():
            # As the file file structure is ID\tOFFSET\tTOTAL\tTOTALDOC,
            # parsing in this format.
            # Removing all prevailing \n with strip
            term_id, line_offset, total_count, doc_count = line.strip().split('\t')
            # Setting the dictionary.
            term_info[int(term_id)] = {
                "Offset" : int(line_offset),
                "Total" : int(total_count),
                "Total Docs" : int(doc_count)
            }

    return term_info

def get_index_entry(filename : str, line_offset : int) -> dict[int, list]:
    """This function grabs the index entry from the inverted index file at that given offset.

    Args:
        filename (str): The file containing the inverted index.
        line_offset (int): The offset to start reading from

    Returns:
        dict[int, list]: The returning object in the following format:
                        {docid : [list of postings]}
    """
    index_entry = {}
    with open(os.path.join(OUTPUT_DIR, filename), encoding="utf-8") as _f:
        # Jumping to that offset.
        _f.seek(line_offset)
        # Reading the desired termID line.
        line = _f.readline()
        # Ignoring the first split on \t as that is termid.
        _, *postings = line.strip().split("\t")
        # Storing the first entry as is, as it is not delta encoded.
        p_docid, position = postings[0].split(":")
        index_entry[int(p_docid)] = [int(position)]
        # Previous docid for delta decoding, and previous posting for decoding as well.
        prev_docid = int(p_docid)
        prev_posting = int(position)
        for posting in postings[1:]:
            p_docid, position = posting.split(":")
            p_docid, position = int(p_docid), int(position)
            # Docid, hence position was delta encoded.
            if p_docid == 0:
                position += prev_posting
            # Setting the docid key if it doesn't already exist.
            p_docid += prev_docid
            index_entry.setdefault(p_docid , [])
            index_entry[p_docid].append(position)
            # Set previous for the current position and p_docid
            prev_docid, prev_posting = p_docid, position

    return index_entry

def get_doc_entry(filename : str, docid : int) -> dict[int, list]:
    """This function returns the document entry from the filename for the given docid.

    Args:
        filename (str): The filename containing the forward index.
        docid (int): The doc id to return information about.

    Returns:
        tuple[dict[int, list], int]: Resultant object in the format:
                         ({termid : [postings]},
                         total term count)
    """
    doc_entry = {}
    # used to keep total term count
    total_count = 0
    with open(os.path.join(OUTPUT_DIR, filename), encoding="utf-8") as _f:
        # Getting a list of every line in the file and making it an iterable for easier access.
        lines = iter(_f.readlines())
        # Looping over every line until desired docid is found.
        for line in lines:
            curr_docid, curr_termid, *curr_postings = line.strip().split("\t")
            curr_docid, curr_termid = int(curr_docid), int(curr_termid)
            if curr_docid == docid:
                doc_entry[curr_termid] = curr_postings
                total_count += len(curr_postings)
                break
        # Now iterating over every line until a different docid is reached.
        for line in lines:
            curr_docid, curr_termid, *curr_postings = line.strip().split("\t")
            curr_docid, curr_termid = int(curr_docid), int(curr_termid)
            if curr_docid != docid:
                break
            doc_entry[curr_termid] = curr_postings
            total_count += len(curr_postings)

        # By using this method, we will have to linearly search for the docid until it is found,
        # instead of linearly iterating over every docid regardless. However, in worst case,
        # this method will also iterate over every line regardless.

    return doc_entry, total_count

def handle_request(args: argparse.Namespace):
    """This function will handle the request by user, it will handle each scenario
    where docname is passed but term isn't, term is passed but docname isn't or both are
    passed.

    Args:
        args (argparse.Namespace): the arguments after being parsed, these will be used to access
                                   arguments.
    """
    termids = get_ids("termids.txt")
    docids = get_ids("docids.txt")
    term_info = get_term_info("term_info.txt")

    # Arguments
    doc = args.doc
    term = args.term
    # Case 1: Docname is passed but term isn't.
    if doc and not term:
        docid = docids[doc]
        # Getting the document entry from doc_index.txt file.
        doc_entry, term_count = get_doc_entry("doc_index.txt", docid)
        # Output for this case.
        print(f"DOCID: {docid}")
        print(f"Distinct Terms: {len(doc_entry)}")
        print(f"Total Terms: {term_count}")
    # Case 2: Term is passed but docname isn't.
    elif not doc and term:
        termid = termids[term]
        # Output for this case.
        print(f"Listing for term: {term}")
        print(f"TERMID: {termid}")
        print(f"Number of documents containing term: {term_info[termid]['Total Docs']}")
        print(f"Term frequency in corpus: {term_info[termid]['Total']}")
        print(f"Inverted list offset: {term_info[termid]['Offset']}")
    # Case 3: Both docname and term is passed.
    elif doc and term:
        termid = termids[term]
        docid = docids[doc]
        # The offset to seek at.
        offset = term_info[termid]["Offset"]
        # Getting the index entry for the term in term_index.
        index_entry = get_index_entry("term_index.txt", offset)
        # Output for this case.
        print(f"Inverted list for term: {term}")
        print(f"In document: {doc}")
        print(f"TERMID: {termid}")
        print(f"DOCID: {docid}")
        try:
            print(f"Term frequency in document: {len(index_entry[docid])}")
            print(f"Positions: {', '.join([str(obj) for obj in index_entry[docid]])}")
        except KeyError:
            print(f"Term does not exist in document: {docid}")
    # Case 4: No arguments passed.
    else:
        print("No arguments were passed, showing general statistics for the index.")
        print(f"Total documents: {len(docids)}")
        print(f"Total distinct terms: {len(termids)}")

def main():
    """Main function
    """
    parser = set_arguments()
    args = parser.parse_args()
    handle_request(args)

if __name__ == "__main__":
    main()
