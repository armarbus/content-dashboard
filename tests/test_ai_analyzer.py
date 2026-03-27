from processor.ai_analyzer import build_prompt_content, parse_ai_response, extract_hook_text

def test_extract_hook_text_from_caption():
    caption = "Stop met alleen bulken. Bouw een hybrid physique. #fitness #hybrid"
    hook = extract_hook_text(caption)
    assert hook.startswith("Stop met alleen bulken")
    assert "#" not in hook

def test_extract_hook_text_from_hashtag_caption():
    caption = "#fitness #hybrid stop met bulken"
    hook = extract_hook_text(caption)
    assert hook == ""  # Falls back to AI

def test_extract_hook_text_empty():
    assert extract_hook_text("") == ""
    assert extract_hook_text(None) == ""

def test_parse_ai_response_valid():
    raw = '{"hook": "Stop met bulken", "hook_type": "tegenstelling", "theme": "hybrid", "ai_why": "Werkt goed.", "ai_your_version": "Jouw versie hier."}'
    result = parse_ai_response(raw)
    assert result["hook"] == "Stop met bulken"
    assert result["hook_type"] == "tegenstelling"
    assert result["theme"] == "hybrid"

def test_parse_ai_response_invalid_json():
    result = parse_ai_response("niet geldig json {{{")
    assert result["hook"] == "Geen tekst beschikbaar"
    assert result["hook_type"] == "anders"

def test_build_prompt_has_brand_context():
    content = build_prompt_content(caption="Test caption", handle="williamdurnik")
    assert "hybrid" in content.lower()
    assert "williamdurnik" in content
