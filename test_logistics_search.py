from logistics_search import IndexedRecord, search


class FakeEmbeddings:
    def create(self, **kwargs):
        class Item:
            embedding = [1.0, 0.0]

        class Response:
            data = [Item()]

        return Response()


class FakeClient:
    embeddings = FakeEmbeddings()


def test_exception_severity_breaks_similarity_tie():
    records = [
        IndexedRecord("normal", "routine delivery", [1.0, 0.0], 0),
        IndexedRecord("urgent", "carton seal opened", [1.0, 0.0], 5),
    ]
    result = search("delivery status", records, client=FakeClient(), limit=2)
    assert [item[0].shipment_id for item in result] == ["urgent", "normal"]
