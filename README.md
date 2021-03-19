# example_pdf_ocr_name_recognition

## install spacy model for ner:
```python
pip install spacy==3.0.5
python -m spacy download en_core_web_lg
```

## install tesseract for ocr:
```python
pip install pytesseract
brew install tesseract
```


## install pdftron + ocr tool:
Guide: https://www.pdftron.com/documentation/mac/get-started/python3/

1. Step 1
```python
pip install PDFNetPython3
```
2. Step 2 of installation guide: download Samples to test PDFNet
https://www.pdftron.com/downloads/PDFNetWrappers/PDFNetPython3.zip

Extract zip into the PDFNetPython3/ folder. Result should look like: PDFNetPython3/Samples

3. Run all samples: Find runall_python.sh in the samples folder and run it.
```python
cd PDFNetPython3/Samples
sh runall_python.sh
```

The output files from all tests are stored in Samples/TestFiles/output/.

4. Installing Additional Modules: OCR
https://www.pdftron.com/documentation/core/info/modules/#ocr-module
4.1 Download module: https://www.pdftron.com/documentation/python/info/modules/
4.2 Unzip the file and place as following:
- from OCRModuleMac/Samples/TestFiles/OCR/ put all the files into PDFNetPython3/Samples/TestFiles/OCR/
- all other remaining files from OCRModuleMac/ put into PDFNetPython3/
- after moving the files we will have *PDFNetPython3/Lib/OCRModule*, here copy the path of the OCRModule file
- to use the OCR module in your code, you have to add the copied file path as following:
```python
	PDFNet.Initialize()

    # The location of the OCR Module add here, e.g.
    PDFNet.AddResourceSearchPath("venv/lib/python3.7/site-packages/PDFNetPython3/Lib/")

	# Test if the model is available now
    if OCRModule.IsModuleAvailable():
        print("FINALY available")
    else:
        print("OCR module is not available")
```

5. OCR usage examples: https://www.pdftron.com/documentation/samples/py/OCRTest

