import pytest
import respx
from httpx import Response
from app.services.whatsapp_service import WhatsAppService, WhatsAppServiceError

@pytest.mark.asyncio
async def test_whatsapp_service_mock_mode():
    service = WhatsAppService()
    service.mock_mode = True

    media_id = await service.upload_media("dummy_path.pdf")
    assert media_id.startswith("mock_media_")

    res = await service.send_document_message(
        to_phone="+14155552671",
        media_id=media_id,
        filename="report.pdf",
        caption="Weekly Report"
    )
    assert "messages" in res
    assert res["messages"][0]["id"].startswith("wamid.")

@pytest.mark.asyncio
@respx.mock
async def test_whatsapp_service_real_http_mocked():
    service = WhatsAppService()
    service.mock_mode = False
    service.access_token = "valid_test_token"
    service.phone_number_id = "123456789"
    service.base_url = "https://graph.facebook.com"

    # Mock media upload endpoint
    respx.post("https://graph.facebook.com/v20.0/123456789/media").mock(
        return_value=Response(200, json={"id": "media_987654321"})
    )

    # Mock message send endpoint
    respx.post("https://graph.facebook.com/v20.0/123456789/messages").mock(
        return_value=Response(200, json={"messaging_product": "whatsapp", "messages": [{"id": "wamid.REAL_ID_123"}]})
    )

    # Test upload with dummy file created on disk
    import tempfile
    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
        tmp.write(b"%PDF-1.4 dummy pdf content")
        tmp_path = tmp.name

    try:
        media_id = await service.upload_media(tmp_path)
        assert media_id == "media_987654321"

        send_res = await service.send_document_message(
            to_phone="+14155552671",
            media_id=media_id,
            filename="report.pdf"
        )
        assert send_res["messages"][0]["id"] == "wamid.REAL_ID_123"
    finally:
        import os
        if os.path.exists(tmp_path):
            os.remove(tmp_path)
