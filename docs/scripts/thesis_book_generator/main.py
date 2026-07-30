# -*- coding: utf-8 -*-
import sys
from build_thesis import new_document, new_section, set_page_number_format, add_footer_page_number
import fm
import ch1
import ch2
import ch3
import ch4
import ch5
import ch67

OUT_PATH = sys.argv[1] if len(sys.argv) > 1 else 'AEGIS_Thesis_Book.docx'


def main():
    doc = new_document()
    front_section = doc.sections[0]
    set_page_number_format(front_section, 'lowerRoman', start=1)
    add_footer_page_number(front_section)

    fm.title_page(doc)
    fm.signature_title_page(doc)
    fm.certification_of_originality(doc)
    fm.certification_of_approval(doc)
    fm.acknowledgement(doc)
    fm.table_of_contents(doc)
    fm.list_of_figures(doc)
    fm.list_of_tables(doc)

    new_section(doc, 'decimal', start=1)

    ch1.abstract(doc)
    ch1.chapter1(doc)
    ch2.chapter2(doc)
    ch3.chapter3(doc)
    ch4.chapter4(doc)
    ch5.chapter5(doc)
    ch67.chapter6(doc)
    ch67.chapter7(doc)
    ch67.references_chapter(doc)

    doc.save(OUT_PATH)
    print(f"Saved: {OUT_PATH}")
    print(f"Total paragraphs (body only, excludes tables/headers/footers): {len(doc.paragraphs)}")


if __name__ == '__main__':
    main()
