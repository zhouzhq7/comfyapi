import json
import os.path
import mimetypes
import urllib.parse
import urllib.request
from requests_toolbelt import MultipartEncoder


def upload_media(input_path, name, server_address, image_type="input", overwrite=True):
    mime_type, _ = mimetypes.guess_type(input_path)
    if mime_type is None:
        raise ValueError("Unsupported file type")

    with open(input_path, 'rb') as file:
        multipart_data = MultipartEncoder(
            fields={
                'image': (name, file, mime_type),
                'type': image_type,
                'overwrite': str(overwrite).lower()
            }
        )

        data = multipart_data
        headers = {'Content-Type': multipart_data.content_type}
        request = urllib.request.Request("http://{}/upload/image".format(server_address), data=data, headers=headers)
        with urllib.request.urlopen(request) as response:
            return response.read()


def upload_data(data_to_upload, server_address, image_type="input", overwrite=True):
    for data in data_to_upload:
        print(data)
        name = os.path.basename(data['filepath'])
        upload_media(data['filepath'], name, server_address, image_type, overwrite)


def queue_prompt(prompt, client_id, server_address):
    p = {"prompt": prompt, "client_id": client_id}
    headers = {'Content-Type': 'application/json'}
    data = json.dumps(p).encode('utf-8')
    req = urllib.request.Request("http://{}/prompt".format(server_address), data=data, headers=headers)
    return json.loads(urllib.request.urlopen(req).read())


def interrupt_prompt(server_address):
    req = urllib.request.Request("http://{}/interrupt".format(server_address), data={})
    return json.loads(urllib.request.urlopen(req).read())


def get_image(filename, subfolder, folder_type, server_address):
    data = {"filename": filename, "subfolder": subfolder, "type": folder_type}
    url_values = urllib.parse.urlencode(data)
    with urllib.request.urlopen("http://{}/view?{}".format(server_address, url_values)) as response:
        return response.read()


def get_history(prompt_id, server_address):
    with urllib.request.urlopen("http://{}/history/{}".format(server_address, prompt_id)) as response:
        return json.loads(response.read())


def get_node_info_by_class(node_class, server_address):
    with urllib.request.urlopen("http://{}/object_info/{}".format(server_address, node_class)) as response:
        return json.loads(response.read())


def clear_comfy_cache(server_address, unload_models=False, free_memory=False):
    clear_data = {
        "unload_models": unload_models,
        "free_memory": free_memory
    }
    data = json.dumps(clear_data).encode('utf-8')

    with urllib.request.urlopen("http://{}/free".format(server_address), data=data) as response:
        return response.read()
