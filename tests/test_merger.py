import os
import sys
from io import BytesIO

import pytest

import PyPDF2
from PyPDF2 import PdfMerger, PdfReader
from PyPDF2.generic import Destination

from . import get_pdf_from_url

TESTS_ROOT = os.path.abspath(os.path.dirname(__file__))
PROJECT_ROOT = os.path.dirname(TESTS_ROOT)
RESOURCE_ROOT = os.path.join(PROJECT_ROOT, "resources")

sys.path.append(PROJECT_ROOT)


def test_merge():
    pdf_path = os.path.join(RESOURCE_ROOT, "crazyones.pdf")
    outline = os.path.join(RESOURCE_ROOT, "pdflatex-outline.pdf")
    pdf_forms = os.path.join(RESOURCE_ROOT, "pdflatex-forms.pdf")
    pdf_pw = os.path.join(RESOURCE_ROOT, "libreoffice-writer-password.pdf")

    merger = PyPDF2.PdfMerger()

    # string path:
    merger.append(pdf_path)
    merger.append(outline)
    merger.append(pdf_path, pages=PyPDF2.pagerange.PageRange(slice(0, 0)))
    merger.append(pdf_forms)
    merger.merge(0, pdf_path, import_bookmarks=False)

    # Merging an encrypted file
    reader = PyPDF2.PdfReader(pdf_pw)
    reader.decrypt("openpassword")
    merger.append(reader)

    # PdfReader object:
    merger.append(PyPDF2.PdfReader(pdf_path), bookmark="foo")

    # File handle
    with open(pdf_path, "rb") as fh:
        merger.append(fh)

    bookmark = merger.add_bookmark("A bookmark", 0)
    bm2 = merger.add_bookmark("deeper", 0, parent=bookmark, italic=True, bold=True)
    merger.add_bookmark("Let's see", 2, bm2, (255, 255, 0), True, True, "/FitBV", 12)
    merger.add_bookmark(
        "The XYZ fit", 0, bookmark, (255, 0, 15), True, True, "/XYZ", 10, 20, 3
    )
    merger.add_bookmark(
        "The FitH fit", 0, bookmark, (255, 0, 15), True, True, "/FitH", 10
    )
    merger.add_bookmark(
        "The FitV fit", 0, bookmark, (255, 0, 15), True, True, "/FitV", 10
    )
    merger.add_bookmark(
        "The FitR fit", 0, bookmark, (255, 0, 15), True, True, "/FitR", 10, 20, 30, 40
    )
    merger.add_bookmark("The FitB fit", 0, bookmark, (255, 0, 15), True, True, "/FitB")
    merger.add_bookmark(
        "The FitBH fit", 0, bookmark, (255, 0, 15), True, True, "/FitBH", 10
    )
    merger.add_bookmark(
        "The FitBV fit", 0, bookmark, (255, 0, 15), True, True, "/FitBV", 10
    )

    found_bm = merger.find_bookmark("nothing here")
    assert found_bm is None

    found_bm = merger.find_bookmark("foo")
    assert found_bm == [9]

    merger.add_metadata({"author": "Martin Thoma"})
    merger.add_named_destination("title", 0)
    merger.set_page_layout("/SinglePage")
    merger.set_page_mode("/UseThumbs")

    tmp_path = "dont_commit_merged.pdf"
    merger.write(tmp_path)
    merger.close()

    # Check if bookmarks are correct
    reader = PyPDF2.PdfReader(tmp_path)
    assert [
        el.title for el in reader._get_outlines() if isinstance(el, Destination)
    ] == [
        "A bookmark",
        "Foo",
        "Bar",
        "Baz",
        "Foo",
        "Bar",
        "Baz",
        "Foo",
        "Bar",
        "Baz",
        "foo",
    ]

    # TODO: There seem to be no destinations for those links?

    # Clean up
    os.remove(tmp_path)


def test_merge_page_exception():
    merger = PyPDF2.PdfMerger()
    pdf_path = os.path.join(RESOURCE_ROOT, "crazyones.pdf")
    with pytest.raises(TypeError) as exc:
        merger.merge(0, pdf_path, pages="a:b")
    assert exc.value.args[0] == '"pages" must be a tuple of (start, stop[, step])'
    merger.close()


def test_merge_page_tuple():
    merger = PyPDF2.PdfMerger()
    pdf_path = os.path.join(RESOURCE_ROOT, "crazyones.pdf")
    merger.merge(0, pdf_path, pages=(0, 1))
    merger.close()


def test_merge_write_closed_fh():
    merger = PyPDF2.PdfMerger()
    pdf_path = os.path.join(RESOURCE_ROOT, "crazyones.pdf")
    merger.append(pdf_path)

    err_closed = "close() was called and thus the writer cannot be used anymore"

    merger.close()
    with pytest.raises(RuntimeError) as exc:
        merger.write("stream.pdf")
    assert exc.value.args[0] == err_closed

    with pytest.raises(RuntimeError) as exc:
        merger.add_metadata({"author": "Martin Thoma"})
    assert exc.value.args[0] == err_closed

    with pytest.raises(RuntimeError) as exc:
        merger.set_page_layout("/SinglePage")
    assert exc.value.args[0] == err_closed

    with pytest.raises(RuntimeError) as exc:
        merger.set_page_mode("/UseNone")
    assert exc.value.args[0] == err_closed

    with pytest.raises(RuntimeError) as exc:
        merger._write_bookmarks()
    assert exc.value.args[0] == err_closed

    with pytest.raises(RuntimeError) as exc:
        merger.add_bookmark("A bookmark", 0)
    assert exc.value.args[0] == err_closed

    with pytest.raises(RuntimeError) as exc:
        merger._write_dests()
    assert exc.value.args[0] == err_closed


def test_trim_outline_list():
    url = "https://corpora.tika.apache.org/base/docs/govdocs1/995/995175.pdf"
    name = "tika-995175.pdf"
    reader = PdfReader(BytesIO(get_pdf_from_url(url, name=name)))
    merger = PdfMerger()
    merger.append(reader)
    merger.write("tmp-merger-do-not-commit.pdf")

    # cleanup
    os.remove("tmp-merger-do-not-commit.pdf")


def test_zoom():
    url = "https://corpora.tika.apache.org/base/docs/govdocs1/994/994759.pdf"
    name = "tika-994759.pdf"
    reader = PdfReader(BytesIO(get_pdf_from_url(url, name=name)))
    merger = PdfMerger()
    merger.append(reader)
    merger.write("tmp-merger-do-not-commit.pdf")

    # cleanup
    os.remove("tmp-merger-do-not-commit.pdf")


def test_zoom_xyz_no_left():
    url = "https://corpora.tika.apache.org/base/docs/govdocs1/933/933322.pdf"
    name = "tika-933322.pdf"
    reader = PdfReader(BytesIO(get_pdf_from_url(url, name=name)))
    merger = PdfMerger()
    merger.append(reader)
    merger.write("tmp-merger-do-not-commit.pdf")

    # cleanup
    os.remove("tmp-merger-do-not-commit.pdf")


def test_bookmark():
    url = "https://corpora.tika.apache.org/base/docs/govdocs1/997/997511.pdf"
    name = "tika-997511.pdf"
    reader = PdfReader(BytesIO(get_pdf_from_url(url, name=name)))
    merger = PdfMerger()
    merger.append(reader)
    merger.write("tmp-merger-do-not-commit.pdf")

    # cleanup
    os.remove("tmp-merger-do-not-commit.pdf")


def test_trim_outline():
    url = "https://corpora.tika.apache.org/base/docs/govdocs1/982/982336.pdf"
    name = "tika-982336.pdf"
    reader = PdfReader(BytesIO(get_pdf_from_url(url, name=name)))
    merger = PdfMerger()
    merger.append(reader)
    merger.write("tmp-merger-do-not-commit.pdf")

    # cleanup
    os.remove("tmp-merger-do-not-commit.pdf")


def test1():
    url = "https://corpora.tika.apache.org/base/docs/govdocs1/923/923621.pdf"
    name = "tika-923621.pdf"
    reader = PdfReader(BytesIO(get_pdf_from_url(url, name=name)))
    merger = PdfMerger()
    merger.append(reader)
    merger.write("tmp-merger-do-not-commit.pdf")

    # cleanup
    os.remove("tmp-merger-do-not-commit.pdf")


def test_sweep_recursion1():
    # TODO: This test looks like an infinite loop.
    url = "https://corpora.tika.apache.org/base/docs/govdocs1/924/924546.pdf"
    name = "tika-924546.pdf"
    reader = PdfReader(BytesIO(get_pdf_from_url(url, name=name)))
    merger = PdfMerger()
    merger.append(reader)
    merger.write("tmp-merger-do-not-commit.pdf")

    reader2 = PdfReader("tmp-merger-do-not-commit.pdf")
    reader2.pages

    # cleanup
    os.remove("tmp-merger-do-not-commit.pdf")


@pytest.mark.parametrize(
    ("url", "name"),
    [
        (
            # TODO: This test looks like an infinite loop.
            "https://corpora.tika.apache.org/base/docs/govdocs1/924/924794.pdf",
            "tika-924794.pdf",
        ),
        (
            "https://corpora.tika.apache.org/base/docs/govdocs1/924/924546.pdf",
            "tika-924546.pdf",
        ),
    ],
)
def test_sweep_recursion2(url, name):
    reader = PdfReader(BytesIO(get_pdf_from_url(url, name=name)))
    merger = PdfMerger()
    merger.append(reader)
    merger.write("tmp-merger-do-not-commit.pdf")

    reader2 = PdfReader("tmp-merger-do-not-commit.pdf")
    reader2.pages

    # cleanup
    os.remove("tmp-merger-do-not-commit.pdf")


def test_sweep_indirect_list_newobj_is_None():
    url = "https://corpora.tika.apache.org/base/docs/govdocs1/906/906769.pdf"
    name = "tika-906769.pdf"
    reader = PdfReader(BytesIO(get_pdf_from_url(url, name=name)))
    merger = PdfMerger()
    merger.append(reader)
    with pytest.warns(UserWarning, match="Object 21 0 not defined."):
        merger.write("tmp-merger-do-not-commit.pdf")

    reader2 = PdfReader("tmp-merger-do-not-commit.pdf")
    reader2.pages

    # cleanup
    os.remove("tmp-merger-do-not-commit.pdf")
