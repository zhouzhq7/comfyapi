import json

import websocket
import uuid

import urllib.request
import urllib.parse
from requests_toolbelt import MultipartEncoder

from api.api_helpers import generate_image_by_prompt_and_image
from utils.helpers.randomize_seed import generate_random_15_digit_number


def upload_image(input_path, name, server_address, image_type="input", overwrite=False):
    with open(input_path, 'rb') as file:
        multipart_data = MultipartEncoder(
            fields={
                'image': (name, file, 'image/png'),
                'type': image_type,
                'overwrite': str(overwrite).lower()
            }
        )

        data = multipart_data
        headers = {'Content-Type': multipart_data.content_type}
        request = urllib.request.Request("http://{}/upload/image".format(server_address), data=data,
                                         headers=headers)
        with urllib.request.urlopen(request) as response:
            return response.read()


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


def prompt_image_to_image(workflow, input_path, positve_prompt='', negative_prompt='', save_previews=False):
    prompt = json.loads(workflow)
    id_to_class_type = {id: details['class_type'] for id, details in prompt.items()}
    k_sampler = [key for key, value in id_to_class_type.items() if value == 'KSamplerAdvanced'][0]
    prompt.get(k_sampler)['inputs']['seed'] = generate_random_15_digit_number()

    if positve_prompt != '':
        positive_input_id = prompt.get(k_sampler)['inputs']['positive'][0]
        prompt.get(positive_input_id)['inputs']['text_g'] = positve_prompt
        prompt.get(positive_input_id)['inputs']['text_l'] = positve_prompt

    if negative_prompt != '':
        negative_input_id = prompt.get(k_sampler)['inputs']['negative'][0]
        id_to_class_type.get(negative_input_id)['inputs']['text_g'] = negative_prompt
        id_to_class_type.get(negative_input_id)['inputs']['text_l'] = negative_prompt

    image_loader = [key for key, value in id_to_class_type.items() if value == 'LoadImage'][0]
    filename = input_path.split('/')[-1]
    prompt.get(image_loader)['inputs']['image'] = filename

    generate_image_by_prompt_and_image(prompt, './output/', input_path, filename, save_previews)


class ComfyAPIHelper:
    def __init__(self, ip, port):
        self.ip = ip
        self.port = port
        self.ws, self.server_addr, self.client_id = self.open_websocket_connection()
        pass

    def open_websocket_connection(self):
        server_address = f'{self.ip}:{self.port}'
        client_id = str(uuid.uuid4())

        ws = websocket.WebSocket()
        ws.connect("ws://{}/ws?clientId={}".format(server_address, client_id))
        return ws, server_address, client_id

    def generate_image_by_prompt_and_image(self, prompt, output_path, input_path, filename, save_previews=False):
        try:
            ws, server_address, client_id = self.open_websocket_connection()
            upload_image(input_path, filename, server_address)
            prompt_id = queue_prompt(prompt, client_id, server_address)['prompt_id']
            self.track_progress(prompt, ws, prompt_id)
            images = self.get_images(prompt_id, server_address, save_previews)
            save_image(images, output_path, save_previews)
        finally:
            ws.close()

    def track_progress(self, prompt, ws, prompt_id):
        node_ids = list(prompt.keys())
        finished_nodes = []

        while True:
            out = ws.recv()
            if isinstance(out, str):
                message = json.loads(out)
                if message['type'] == 'progress':
                    data = message['data']
                    current_step = data['value']
                    print('In K-Sampler -> Step: ', current_step, ' of: ', data['max'])
                if message['type'] == 'execution_cached':
                    data = message['data']
                    for itm in data['nodes']:
                        if itm not in finished_nodes:
                            finished_nodes.append(itm)
                            print('Progress: ', len(finished_nodes), '/', len(node_ids), ' Tasks done')
                if message['type'] == 'executing':
                    data = message['data']
                    if data['node'] not in finished_nodes:
                        finished_nodes.append(data['node'])
                        print('Progress: ', len(finished_nodes), '/', len(node_ids), ' Tasks done')

                    if data['node'] is None and data['prompt_id'] == prompt_id:
                        break  # Execution is done
            else:
                continue  # previews are binary data
        return

    def get_images(self, prompt_id, server_address, allow_preview=False):
        output_images = []

        history = get_history(prompt_id, server_address)[prompt_id]
        for node_id in history['outputs']:
            node_output = history['outputs'][node_id]
            output_data = {}
            if 'images' in node_output:
                for image in node_output['images']:
                    if allow_preview and image['type'] == 'temp':
                        preview_data = get_image(image['filename'], image['subfolder'], image['type'], server_address)
                        output_data['image_data'] = preview_data
                    if image['type'] == 'output':
                        image_data = get_image(image['filename'], image['subfolder'], image['type'], server_address)
                        output_data['image_data'] = image_data
            output_data['file_name'] = image['filename']
            output_data['type'] = image['type']
            output_images.append(output_data)

        return output_images