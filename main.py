import re
import json

import pytesseract
from pdf2image import convert_from_path
import en_core_web_lg
import nltk
import spacy
from PDFNetPython3.PDFNetPython import PDFNet, OCRModule, PDFDoc, OCROptions

from extract_text_pdftron import extract_raw_data

nlp = en_core_web_lg.load()

PDFNet.Initialize()
# add OCRModule path
PDFNet.AddResourceSearchPath("venv/lib/python3.7/site-packages/PDFNetPython3/Lib/")
if OCRModule.IsModuleAvailable():
    print("OCR module is available")
else:
    print("OCR module is not available")


def save_json(output_path, json_obj):
    with open(output_path, "w") as o_file:
        o_file.write(json.dumps(json_obj))


def spacy_ner(text_dict):
    collected_ners = []

    for item_id, item_text in text_dict.items():
        doc = nlp(item_text)

        for ent in doc.ents:
            if ent.label_ in ["ORG", "PERSON"]:
                collected_ners.append((ent.text,ent.label_,spacy.explain(ent.label_)))
    return collected_ners


def nltk_ner(text_dict):
    collected_ners_nltk = []

    for item_id, item_text in text_dict.items():
        for sent in nltk.sent_tokenize(item_text):
            ne_chunks = nltk.ne_chunk(nltk.pos_tag(nltk.word_tokenize(sent)))

            for chunk in ne_chunks:
                if hasattr(chunk, 'label') and chunk.label() in ["ORGANIZATION", "PERSON"]:
                    print(chunk.label(), ' '.join(c[0] for c in chunk))
                    collected_ners_nltk.append((chunk.label(), ' '.join(c[0] for c in chunk)))

    return collected_ners_nltk


def concat_raw_par_lines(par):
    """ Concatenate and clean (i.g. remove multiple new line chars, white space chars)
    the lines of raw paragraph.
    A raw paragraph looks like this:

    This is a nice example par-
    agraph which has   multiple
    whitespace characters. It
    can also ends with "broken"
    sentence at the end of the

    After concatenation: This is a nice example paragraph which has multiple whitespace characters.
    It can also ends with "broken" sentence at the end of the
    """

    broken = False

    # check if a word is cut into two parts at the end of the PARAGRAPH
    # it ends with - char and zero or more whitespace chars (new line, space, tab, ..)
    if re.search(r'-\s*$', par):
        broken = True

    # Remove all the line breaks and new line chars from the lines (everywhere) of LINES
    # if a line has '-' plus some whitespace chars, replace with nothing
    # (lines always end with at least one new line c)
    par = re.sub(r'-\s+', "", par)

    # replace multiple whitespace chars with one space, these wont remove WORD\nWORD
    par = re.sub(r'\s{2,}', " ", par)

    # In case of broken word at the end of PARAGRAPH (e.g. some- ), keep the '-' chars at the end,
    # so we will know later that this par. is broken.
    if broken:
        par = ''.join([par, '-'])
        broken = False

    # If the paragraph ends with " " (it should because of prev. operations), remove it.
    # Need this form for the paragraph concat later.
    par = re.sub(r'\s+$', "", par)

    # change all the newline chars into one space " " e.g.: WORD\nWORD -> WORD WORD
    par = re.sub(r'\r\n|\r|\n', " ", par)  # replace newline char with one space
    return par


def ocr_pdftron_example(pdf_path):
    """Convert a scanned pdf to a searchable pdf from which text can be extracted"""
    doc = PDFDoc(pdf_path)

    # Set English as the language of choice
    opts = OCROptions()
    opts.AddLang("eng")

    # we could ignore zones on the pages, e.g header/footer
    # ignore_zones = RectCollection()
    # ignore_zones.AddRect(Rect(424, 163, 493, 730))
    # opts.AddIgnoreZonesForPage(ignore_zones, 1)

    # Run OCR on the PDF with options
    OCRModule.ProcessPDF(doc, opts)

    output_file = pdf_path.split(".pdf")[0] + "_pdftronOCR.pdf"
    doc.Save(output_file, 0)

    return output_file


def ocr_tesseract_example(path):
    """Extract text using tesseract OCR"""
    pdf_text = {}
    pages = convert_from_path(path, 500)

    for pageNum, imgBlob in enumerate(pages):
        print("tesseract - get text from page: ", pageNum)
        text = pytesseract.image_to_string(imgBlob, lang='eng')
        pdf_text.update({pageNum: concat_raw_par_lines(text)})

    return pdf_text


def pdftron_ocr_spacy_ner_example(pdf_path):
    # Note: pdftron ocr is used here to create a text layer over the scanned pdf.
    ocr_file_path = ocr_pdftron_example(pdf_path)

    raw_paragraphs_dict, raw_lines_dict = extract_raw_data(ocr_file_path)
    page_par_dict = {}
    for par_id, par in raw_paragraphs_dict.items():
        page_par_dict.update({par_id: concat_raw_par_lines(par["text"])})

    pdfdict_path = ocr_file_path.split(".pdf")[0] + "_pdfdict.json"
    save_json(pdfdict_path, page_par_dict)

    ner_path = ocr_file_path.split(".pdf")[0] + "_ner.json"
    spacy_ner_result = spacy_ner(page_par_dict)
    save_json(ner_path, spacy_ner_result)


def tesseract_ocr_spacy_ner_example(pdf_path):
    ocr_pdf_text = ocr_tesseract_example(pdf_path)

    pdfdict_path = pdf_path.split(".pdf")[0] + "_tesseract_pagedict.json"
    save_json(pdfdict_path, ocr_pdf_text)

    ner_path = pdf_path.split(".pdf")[0] + "_tesseract_ner.json"
    spacy_ner_result = spacy_ner(ocr_pdf_text)
    save_json(ner_path, spacy_ner_result)


if __name__=="__main__":
    pdf1 = "test_files/DOK_484258C_20210303.pdf"
    pdf2 = "test_files/test_pdf.pdf"
    # OCR PDFTron - pdf conversion + PDFMINER TEXT EXTRACTION + NER
    # -------------------------------------------------------------
    pdftron_ocr_spacy_ner_example(pdf1)

    # OCR tesseract - pdf text extraction with tesseract + NER
    # -------------------------------------------------------------
    tesseract_ocr_spacy_ner_example(pdf1)



