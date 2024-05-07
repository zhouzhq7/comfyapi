import json
from PIL import Image
import io
import os

# Assuming the import paths are correct and the methods are defined elsewhere:
from api.websocket_api import queue_prompt, get_history, get_image, upload_image, clear_comfy_cache
from api.open_websocket import open_websocket_connection


class WebSocketHelper:
    def __init__(self, ip, port):
        self.ip = ip
        self.port = port
        self.ws, self.server_addr, self.client_id = open_websocket_connection(ip, port)


web_socket_helper: WebSocketHelper = None


def generate_image_by_prompt(prompt, output_path, save_previews=False):
    try:
        if web_socket_helper is None:
            print(f'web_socket is not initialize yet, return')
            return
        # ws, server_address, client_id = open_websocket_connection()
        prompt_id = queue_prompt(prompt, web_socket_helper.client_id, web_socket_helper.server_addr)['prompt_id']
        track_progress(prompt, web_socket_helper.ws, prompt_id)
        images = get_images(prompt_id, web_socket_helper.server_addr, save_previews)
        save_image(images, output_path, save_previews)
    finally:
        if web_socket_helper is None:
            print(f'web_socket is not initialize yet.')
            return
        web_socket_helper.ws.close()


def generate_image_by_prompt_and_image(prompt, output_path, input_path, filename, save_previews=False):
    try:
        upload_image(input_path, filename, web_socket_helper.server_addr)
        prompt_id = queue_prompt(prompt, web_socket_helper.client_id, web_socket_helper.server_addr)['prompt_id']
        track_progress(prompt, web_socket_helper.ws, prompt_id)
        images = get_images(prompt_id, web_socket_helper.server_addr, save_previews)
        save_image(images, output_path, save_previews)
    finally:
        if web_socket_helper is None:
            print(f'web_socket is not initialize yet.')
            return
        web_socket_helper.ws.close()


def save_image(images, output_path, save_previews):
    for itm in images:
        directory = os.path.join(output_path, 'temp/') if itm['type'] == 'temp' and save_previews else output_path
        os.makedirs(directory, exist_ok=True)
        try:
            image = Image.open(io.BytesIO(itm['image_data']))
            image.save(os.path.join(directory, itm['file_name']))
        except Exception as e:
            print(f"Failed to save image {itm['file_name']}: {e}")


def track_progress(prompt, ws, prompt_id):
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


def get_images(prompt_id, server_address, allow_preview=False):
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


def clear():
    clear_comfy_cache()
