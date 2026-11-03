from app.services.retrieval_service import RetrievalService

def test_hybrid_search_results():
    service = RetrievalService.get_instance()
    results = service.search(query="pricing plans and discounts", top_k=3)
    assert len(results) > 0
    assert results[0].rrf_score > 0
    assert results[0].text is not None

def test_retrieval_category_filtering():
    service = RetrievalService.get_instance()
    results = service.search(query="Salesforce HubSpot", top_k=5, category="Integrations")
    if results:
        for r in results:
            assert r.category == "Integrations"
