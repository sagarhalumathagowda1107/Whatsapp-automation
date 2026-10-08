import os
import uuid
import httpx
from typing import Dict, Any, Optional
from app.config import settings
from app.utils.logger import logger

class WhatsAppServiceError(Exception):
    def __init__(self, message: str, status_code: Optional[int] = None, response_data: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.status_code = status_code
        self.response_data = response_data

class WhatsAppService:
    """
    Isolated service wrapper for the Meta WhatsApp Business Cloud API.
    Uses official Meta endpoints only.
    """

    def __init__(self):
        self.base_url = settings.WHATSAPP_API_BASE_URL.rstrip('/')
        self.api_version = settings.WHATSAPP_API_VERSION
        self.phone_number_id = settings.WHATSAPP_PHONE_NUMBER_ID
        self.access_token = settings.WHATSAPP_ACCESS_TOKEN
        self.mock_mode = settings.WHATSAPP_MOCK_MODE or (self.access_token in ["mock_token", "your_meta_whatsapp_access_token", ""])

    @property
    def headers(self) -> Dict[str, str]:
        return {
            "Authorization": f"Bearer {self.access_token}"
        }

    async def upload_media(self, file_path: str, mime_type: str = "application/pdf") -> str:
        """
        Uploads a media file (e.g. PDF) to Meta WhatsApp Media Endpoint.
        Endpoint: POST /{api_version}/{phone_number_id}/media
        Returns Meta media_id string.
        """
        if self.mock_mode:
            mock_media_id = f"mock_media_{uuid.uuid4().hex[:12]}"
            logger.info(f"[MOCK] Uploaded media {file_path}, mock media_id: {mock_media_id}")
            return mock_media_id

        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found for media upload: {file_path}")

        url = f"{self.base_url}/{self.api_version}/{self.phone_number_id}/media"
        filename = os.path.basename(file_path)

        async with httpx.AsyncClient(timeout=60.0) as client:
            with open(file_path, "rb") as f:
                files = {
                    "file": (filename, f, mime_type)
                }
                data = {
                    "messaging_product": "whatsapp",
                    "type": mime_type
                }
                logger.info(f"Uploading media file '{filename}' to Meta Cloud API...")
                response = await client.post(url, headers=self.headers, data=data, files=files)

        if response.status_code not in [200, 201]:
            logger.error(f"Failed to upload media to Meta: {response.status_code} - {response.text}")
            raise WhatsAppServiceError(
                f"Media upload failed: {response.text}",
                status_code=response.status_code,
                response_data=response.json() if response.headers.get("content-type") == "application/json" else None
            )

        resp_data = response.json()
        media_id = resp_data.get("id")
        if not media_id:
            raise WhatsAppServiceError(f"Meta response missing media 'id': {resp_data}")
        
        logger.info(f"Successfully uploaded media to Meta. Media ID: {media_id}")
        return media_id

    async def send_document_message(
        self,
        to_phone: str,
        media_id: str,
        filename: str,
        caption: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Sends a PDF document message to a WhatsApp user using uploaded media ID.
        Endpoint: POST /{api_version}/{phone_number_id}/messages
        Returns response dict containing WhatsApp message ID.
        """
        if self.mock_mode:
            mock_msg_id = f"wamid.HBgL{uuid.uuid4().hex[:20]}"
            logger.info(f"[MOCK] Sent PDF document to {to_phone}. Message ID: {mock_msg_id}")
            return {
                "messaging_product": "whatsapp",
                "contacts": [{"input": to_phone, "wa_id": to_phone.lstrip("+")}],
                "messages": [{"id": mock_msg_id}]
            }

        url = f"{self.base_url}/{self.api_version}/{self.phone_number_id}/messages"
        payload = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": to_phone,
            "type": "document",
            "document": {
                "id": media_id,
                "filename": filename
            }
        }
        if caption:
            payload["document"]["caption"] = caption

        async with httpx.AsyncClient(timeout=30.0) as client:
            logger.info(f"Sending PDF document message to recipient {to_phone}...")
            response = await client.post(url, headers=self.headers, json=payload)

        if response.status_code not in [200, 201]:
            logger.error(f"Failed to send WhatsApp document message: {response.status_code} - {response.text}")
            raise WhatsAppServiceError(
                f"Send document message failed: {response.text}",
                status_code=response.status_code,
                response_data=response.json() if "application/json" in response.headers.get("content-type", "") else None
            )

        return response.json()

    async def send_text_message(self, to_phone: str, message_body: str) -> Dict[str, Any]:
        """Sends a plain text message to a WhatsApp user."""
        if self.mock_mode:
            mock_msg_id = f"wamid.HBgL{uuid.uuid4().hex[:20]}"
            logger.info(f"[MOCK] Sent text message to {to_phone}. Message ID: {mock_msg_id}")
            return {
                "messaging_product": "whatsapp",
                "contacts": [{"input": to_phone, "wa_id": to_phone.lstrip("+")}],
                "messages": [{"id": mock_msg_id}]
            }

        url = f"{self.base_url}/{self.api_version}/{self.phone_number_id}/messages"
        payload = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": to_phone,
            "type": "text",
            "text": {"preview_url": False, "body": message_body}
        }

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(url, headers=self.headers, json=payload)

        if response.status_code not in [200, 201]:
            raise WhatsAppServiceError(
                f"Send text message failed: {response.text}",
                status_code=response.status_code,
                response_data=response.json() if "application/json" in response.headers.get("content-type", "") else None
            )

        return response.json()

    async def send_template_message(
        self,
        to_phone: str,
        template_name: str,
        language_code: str = "en_US",
        components: Optional[list] = None
    ) -> Dict[str, Any]:
        """Sends an approved Meta WhatsApp template message."""
        if self.mock_mode:
            mock_msg_id = f"wamid.HBgL{uuid.uuid4().hex[:20]}"
            logger.info(f"[MOCK] Sent template '{template_name}' to {to_phone}. Message ID: {mock_msg_id}")
            return {
                "messaging_product": "whatsapp",
                "contacts": [{"input": to_phone, "wa_id": to_phone.lstrip("+")}],
                "messages": [{"id": mock_msg_id}]
            }

        url = f"{self.base_url}/{self.api_version}/{self.phone_number_id}/messages"
        payload = {
            "messaging_product": "whatsapp",
            "to": to_phone,
            "type": "template",
            "template": {
                "name": template_name,
                "language": {"code": language_code}
            }
        }
        if components:
            payload["template"]["components"] = components

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(url, headers=self.headers, json=payload)

        if response.status_code not in [200, 201]:
            raise WhatsAppServiceError(
                f"Send template message failed: {response.text}",
                status_code=response.status_code
            )

        return response.json()

whatsapp_service = WhatsAppService()
