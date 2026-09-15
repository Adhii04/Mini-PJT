from docx import Document
doc = Document(r'c:\Users\Eren\Documents\PJT\Comprehensive_Research_Papers_Analysis_Report.docx')
text_parts = []
for para in doc.paragraphs:
    if para.text.strip():
        text_parts.append(para.text)
full_text = '\n'.join(text_parts)
# look for papers 20-31 content
print(full_text[42000:55000])
