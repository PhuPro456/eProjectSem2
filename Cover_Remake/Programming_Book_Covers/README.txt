Programming Book Covers

The 100 JPEG files are named by the matching book ID in the programming
catalog. book-001.jpg belongs to ID 1, and book-100.jpg belongs to ID 100.

To install in Paper & Pine, extract this ZIP and merge the FrontEnd folder
into the existing Flask project. The archive contains:

- FrontEnd/static/covers/book-001.jpg through book-100.jpg
- FrontEnd/database/books.json with local /static/covers/ paths
- cover-index.csv mapping each ID, title, and catalog ISBN to the cover source

The catalog's IDs and book information are preserved. Most artwork was
retrieved from Open Library by catalog ISBN. Other images come from publisher
or retailer listings. Some are from another format or regional printing
of the same title and edition. The source URL is listed for every image.
