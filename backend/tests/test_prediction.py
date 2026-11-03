from app.services.prediction_service import PredictionService

def test_prediction_output_structure(sample_lead_dict):
    service = PredictionService.get_instance()
    res = service.predict(sample_lead_dict)
    
    assert 0.0 <= res.probability <= 1.0
    assert isinstance(res.is_high_confidence, bool)
    assert len(res.feature_contributions) > 0
    assert res.model_version is not None

def test_prediction_metadata():
    service = PredictionService.get_instance()
    meta = service.get_model_metadata()
    assert "model_type" in meta
    assert "metrics" in meta
