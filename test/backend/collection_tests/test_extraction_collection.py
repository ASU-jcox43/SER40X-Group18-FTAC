from Backend.Logic.mongo_db.extraction_collection import (
    upsertExtraction,
    getExtraction,
    getAllExtractions
)


def test_upsert_extraction(monkeypatch):
    stored = {}

    class FakeCollection:
        def update_one(self, query, update, upsert=False):
            stored["query"] = query
            stored["data"] = update["$set"]

    monkeypatch.setattr(
        "Backend.Logic.mongo_db.extraction_collection.EXTRACTION_COLLECTION",
        FakeCollection()
    )

    test_doc = {
        "file": "test.txt",
        "source": "txt",
        "keyword_contexts": {"test": []}
    }

    upsertExtraction(test_doc)

    assert stored["query"]["_id"] == "test.txt"
    assert stored["data"]["file"] == "test.txt"


def test_get_extraction(monkeypatch):
    fake_result = {"_id": "test.txt", "file": "test.txt"}

    class FakeCollection:
        def find_one(self, query):
            assert query["_id"] == "test.txt"
            return fake_result

    monkeypatch.setattr(
        "Backend.Logic.mongo_db.extraction_collection.EXTRACTION_COLLECTION",
        FakeCollection()
    )

    result = getExtraction("test.txt")

    assert result == fake_result


def test_get_all_extractions(monkeypatch):
    fake_data = [
        {"file": "a.txt"},
        {"file": "b.txt"}
    ]

    class FakeCollection:
        def find(self, query, projection):
            return fake_data

    monkeypatch.setattr(
        "Backend.Logic.mongo_db.extraction_collection.EXTRACTION_COLLECTION",
        FakeCollection()
    )

    result = getAllExtractions()

    assert len(result) == 2
    assert result[0]["file"] == "a.txt"
    

def test_extract_document_writes_to_db(monkeypatch):
    captured = {}

    def fake_upsert(data):
        captured["data"] = data

    monkeypatch.setattr(
        "Backend.Logic.mongo_db.extraction_collection.upsertExtraction",
        fake_upsert
    )

    text = "A business license is required."

    from Backend.Logic.extraction.text_extraction import extractDocument
    extractDocument(text, "test.txt", "txt")

    assert captured["data"]["file"] == "test.txt"
    assert captured["data"]["source"] == "txt"
    assert "keyword_contexts" in captured["data"]
    
    
def test_upsert_overwrites(monkeypatch):
    calls = []

    class FakeCollection:
        def update_one(self, query, update, upsert=False):
            calls.append(update["$set"])

    monkeypatch.setattr(
        "Backend.Logic.mongo_db.extraction_collection.EXTRACTION_COLLECTION",
        FakeCollection()
    )

    doc1 = {"file": "same.txt", "source": "txt", "keyword_contexts": {}}
    doc2 = {"file": "same.txt", "source": "txt", "keyword_contexts": {"new": []}}

    upsertExtraction(doc1)
    upsertExtraction(doc2)

    assert calls[-1]["keyword_contexts"] == {"new": []}