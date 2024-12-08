import base64
import json
import asyncio
import aiohttp


API_KEY = "EBRGzBmtUldOtpuqWx7fs1DxcUs1"
BASE_URL = "https://app.docupanda.io"


async def send_request(url, method='GET', payload=None):
    headers = {
        "accept": "application/json",
        "content-type": "application/json",
        "X-API-Key": API_KEY
    }
    async with aiohttp.ClientSession() as session:
        async with session.request(method, url, json=payload, headers=headers) as response:
            return await response.json()


async def post_document(file_path, file_name):
    with open(file_path, 'rb') as f:
        encoded_file = base64.b64encode(f.read()).decode()
    payload = {"document": {"file": {"contents": encoded_file, "filename": file_name}}}
    response = await send_request(f"{BASE_URL}/document", 'POST', payload)
    if 'documentId' in response:
        return response['documentId']
    raise ValueError(f"Document upload failed: {response}")


async def wait_for_status(url):
    while True:
        response = await send_request(url)
        status = response.get('status')
        if status == "completed":
            return
        if status == "failed":
            raise ValueError(f"Document processing failed: {response}")
        await asyncio.sleep(2)


async def standardize_document(document_id, schema_id):
    payload = {"documentIds": [document_id], "schemaId": schema_id, "forceRecompute": True}
    response = await send_request(f"{BASE_URL}/standardize/batch", 'POST', payload)
    if "standardizationIds" in response:
        return response["standardizationIds"][0]
    raise ValueError(f"Standardization failed: {response}")


async def wait_for_standardization(standardization_id):
    url = f"{BASE_URL}/standardization/{standardization_id}"
    for _ in range(10):
        response = await send_request(url)
        if response.get('standardizationId'):
            return response
        print("Still processing, retrying...")
        await asyncio.sleep(5)
    raise TimeoutError("Standardization not completed in time.")


async def process_document(file_path):
    try:
        document_id = await post_document(file_path, "receipt.png")
        print(f"Document ID: {document_id}")
        await wait_for_status(f"{BASE_URL}/document/{document_id}")

        schema_id = '587d920b'
        standardization_id = await standardize_document(document_id, schema_id)
        print(f"Standardization ID: {standardization_id}")

        result = await wait_for_standardization(standardization_id)
        json_file_path = r'C:\Users\Python\recipt_reading\result.json'
        with open(json_file_path, 'w', encoding='utf-8') as json_file:
            json.dump(result, json_file, ensure_ascii=False, indent=4)
        print(f"Result saved to {json_file_path}")

    except Exception as e:
        print(f"Error: {str(e)}")


if __name__ == "__main__":
    asyncio.run(process_document(r'C:\Users\Python\recipt_reading\receipt_2.jpg'))