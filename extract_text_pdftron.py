"""Extract text from pdf using the PDFTron - PDFNet python lib.
NOTE:  checking the line's paragraph ID with line.GetParagraphID() is tricky:
the paragraph IDs are not unique, so cannot be used as keys
but can be used to identify which lines belong together in a paragraph
e.g. line's paragraph IDs: 0,0,0,1,1,1,1,1,2,2,3,3,3,3,4,4,4,5,5,5,5,5,5,5,5,0,0,0,0,0,7,7,7,7,7
"""
import sys
import datetime
import json
import os

from PDFNetPython3.PDFNetPython import PDFNet, PDFDoc, TextExtractor


def collect_line_words(line):
    """Generate word list from the given string"""
    line_text = []
    word = line.GetFirstWord()
    while word.IsValid():
        if word.GetStringLen() == 0:
            word = word.GetNextWord()
            continue
        word_string = word.GetString()
        line_text.append(word_string)
        word = word.GetNextWord()
    return line_text


def convert_bbox(bbox):
    """Return bbox coordinates in {x0, y0, x1, y1} dict"""
    return {"x0": bbox.GetX1(), "y0": bbox.GetY1(), "x1": bbox.GetX2(), "y1": bbox.GetY2()}


def generate_paragraph_item(paragraph_lines, page_id, cnt_paragraphs):
    """Return a paragraph dict item"""
    columns = list(zip(*paragraph_lines))
    par_id = f"{page_id}p{cnt_paragraphs}"
    return {par_id: {"text": "\n\n".join(columns[1]), "lines": list(columns[0])}}


def extract_raw_data(in_file):
    """Extract raw data from pdf and generate its paragraph / line dicts.
    """
    paragraphs_dict = {}
    lines_dict = {}
    PDFNet.Initialize()

    # we get either a locally available pdf path or a io.BytesIO object with loaded pdf bytes
    if isinstance(in_file, str):
        doc = PDFDoc(in_file)
    else:
        # get the memory buffer of the io.BytesIO object
        buffer = in_file.getbuffer()
        doc = PDFDoc(bytearray(buffer), len(buffer))

    # Sample code showing how to use high-level text extraction APIs.
    doc.InitSecurityHandler()
    cnt_page = 0
    page_iter = doc.GetPageIterator()
    while page_iter.HasNext():
        page = page_iter.Current()
        print("Page ID : ",cnt_page)

        page_id = f"p{cnt_page}"
        if page is None:
            print("page not found")

        txt = TextExtractor()
        txt.Begin(page)  # Read the page

        # For each line on the page...
        line = txt.GetFirstLine()
        current_paragraph_lines = []
        cnt_paragraphs = 0  # reset for each page
        cnt_lines = 0  # reset for each page
        cur_flow_id = -1
        cur_para_id = -1
        while line.IsValid():
            if line.GetNumWords() == 0:
                line = line.GetNextLine()
                continue
            # If we have a new 'flow' with the current line, save the prev. paragraph
            if cur_flow_id != line.GetFlowID():
                if cur_flow_id != -1:
                    if cur_para_id != -1:
                        paragraphs_dict.update(generate_paragraph_item(current_paragraph_lines,
                                                                       page_id, cnt_paragraphs))
                        current_paragraph_lines = []
                        cnt_paragraphs += 1
                        cur_para_id = -1
                    # end of flow
                cur_flow_id = line.GetFlowID()
                #print("<Flow id=\"" + str(cur_flow_id) + "\">")

            # If we have new paragraph with the current line, save the prev. paragraph
            if cur_para_id != line.GetParagraphID():
                if cur_para_id != -1:
                    paragraphs_dict.update(generate_paragraph_item(current_paragraph_lines,
                                                                   page_id, cnt_paragraphs))
                    current_paragraph_lines = []
                    cnt_paragraphs += 1
                cur_para_id = line.GetParagraphID()
                #print("<Par id=\"" + str(cur_para_id) + "\">")

            bbox = line.GetBBox()

            # For each word in the line...
            line_words_list = collect_line_words(line)
            joined_line_text = " ".join(line_words_list)
            line_id = f"{page_id}l{cnt_lines}"
            current_paragraph_lines.append(tuple((line_id, joined_line_text)))
            lines_dict.update({line_id: {"text": joined_line_text,
                                         "pos": convert_bbox(bbox)}})
            cnt_lines += 1
            line = line.GetNextLine()

        # at the end of the page, check if there is a not saved paragraph
        if current_paragraph_lines:
            paragraphs_dict.update(generate_paragraph_item(current_paragraph_lines,
                                                           page_id, cnt_paragraphs))

        txt.Destroy()
        page_iter.Next()
        cnt_page += 1
    doc.Close()

    return paragraphs_dict, lines_dict


if __name__ == "__main__":
    start = datetime.datetime.now()
    file_path = "/Users/nikolettatoth/Downloads/Noble_Investment.pdf"
    raw_paragraphs_dict, raw_lines_dict = extract_raw_data(file_path)

    # fine_paragraph_dict = fine_paragraphs(raw_paragraphs_dict)
    # fine_paragraph_dict_reduced = reduce_paragraph_length(fine_paragraph_dict, raw_lines_dict)

    pdf_name = os.path.basename(file_path)
    pdf_dict = {'pdf_name': pdf_name, 'paragraphs': raw_paragraphs_dict, 'lines': raw_lines_dict}
    result_data = {"pdf_dict": pdf_dict}

    with open(f"{pdf_name[:-4]}_pdftron.json", "w") as f:
        f.write(json.dumps(result_data, indent=4))
    print(datetime.datetime.now() - start)
