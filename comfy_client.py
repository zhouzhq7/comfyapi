import json
from PIL import Image
import io
import os
import websocket  # NOTE: websocket-client (https://github.com/websocket-client/websocket-client)
import uuid

from api.websocket_api import queue_prompt, get_history, get_image, upload_data, clear_comfy_cache


class ComfyClient:
    def __init__(self, ip, port):
        self.ip = ip
        self.port = port
        self.ws, self.server_addr, self.client_id = open_websocket_connection(self.ip, self.port)

    def run_workflow(self, workflow, user_inputs, output_path='./output', save_previews=False):
        prompt, data_to_upload = prepare_inputs(workflow, user_inputs)
        self.post_to_comfy_server(prompt, data_to_upload, output_path=output_path, save_previews=save_previews)
        pass

    def post_to_comfy_server(self, prompt, data_to_upload, output_path='./output', save_previews=False):
        if len(data_to_upload) > 0:
            upload_data(data_to_upload, self.server_addr)
        prompt_id = queue_prompt(prompt, self.client_id, self.server_addr)['prompt_id']
        output_prompt_id = track_progress(prompt, self.ws, prompt_id)
        output_images, output_videos = get_outputs(output_prompt_id, self.server_addr, save_previews)
        if len(output_images):
            save_image(output_images, output_path, save_previews)
        if len(output_videos):
            save_video(output_videos, output_path, save_previews)


def open_websocket_connection(ip='127.0.0.1', port=8288):
    server_address = f'{ip}:{port}'
    client_id = str(uuid.uuid4())

    ws = websocket.WebSocket()
    ws.connect("ws://{}/ws?clientId={}".format(server_address, client_id))
    return ws, server_address, client_id


def prepare_inputs(workflow, user_inputs):
    prompt = json.loads(workflow)
    id_to_class_title = {id: details['_meta']['title'] for id, details in prompt.items()}
    input_nodes = [key for key, value in id_to_class_title.items() if value.startswith('[Input]')]
    data_to_upload = []
    for input_node in input_nodes:
        input_key = id_to_class_title.get(input_node).split('-')[1]
        if input_key in user_inputs:
            if prompt.get(input_node)['class_type'] == 'LoadImage':
                prompt.get(input_node)['inputs']['image'] = user_inputs.get(input_key).split('/')[-1]
                data_to_upload.append({'filepath': user_inputs.get(input_key), 'type': 'image'})
            elif prompt.get(input_node)['class_type'] == 'VHS_LoadVideo':
                prompt.get(input_node)['inputs']['video'] = user_inputs.get(input_key).split('/')[-1]
                data_to_upload.append({'filepath': user_inputs.get(input_key), 'type': 'video'})
            else:
                if 'string' in prompt.get(input_node)['inputs']:
                    prompt.get(input_node)['inputs']['string'] = user_inputs.get(input_key)
                elif 'value' in prompt.get(input_node)['inputs']:
                    prompt.get(input_node)['inputs']['value'] = user_inputs.get(input_key)
                else:
                    class_type = input_node['class_type']
                    raise TypeError(f'Input type {class_type} is not a valid input for this workflow')
        else:
            raise ValueError(f'Input key {input_key} not found in user inputs')

    return prompt, data_to_upload


def save_image(images, output_path, save_previews):
    for itm in images:
        directory = os.path.join(output_path, 'temp/') if itm['type'] == 'temp' and save_previews else output_path
        os.makedirs(directory, exist_ok=True)
        try:
            image = Image.open(io.BytesIO(itm['image_data']))
            image.save(os.path.join(directory, itm['file_name']))
        except Exception as e:
            print(f"Failed to save image {itm['file_name']}: {e}")


def save_video(videos, output_path, save_previews):
    for itm in videos:
        directory = os.path.join(output_path, 'temp/') if itm['type'] == 'temp' and save_previews else output_path
        os.makedirs(directory, exist_ok=True)
        try:
            with open(os.path.join(directory, itm['file_name']), 'wb') as f:
                f.write(itm['video_data'])
        except Exception as e:
            print(f"Failed to save image {itm['file_name']}: {e}")


def track_progress(prompt, ws, prompt_id):
    node_ids = list(prompt.keys())
    finished_nodes = []
    finished = True
    has_unfinished_batch = False
    final_prompt_id = prompt_id
    while True:
        out = ws.recv()
        if isinstance(out, str):
            message = json.loads(out)
            # print(message)
            data = message['data']
            if 'output' in data:
                if 'unfinished_batch' in message['data']['output'] and \
                        message['data']['output']['unfinished_batch'][0] is True:
                    print('Has unfinished batch, continue...')
                    finished = False
                    has_unfinished_batch = True
                else:
                    if has_unfinished_batch:
                        final_prompt_id = data['prompt_id']
                        print(f'Finished, final prompt id {final_prompt_id}, original prompt id {prompt_id}.')
                    finished = True
            if message['type'] == 'progress':
                current_step = data['value']
                print('In K-Sampler -> Step: ', current_step, ' of: ', data['max'])
            if message['type'] == 'execution_cached':
                for itm in data['nodes']:
                    if itm not in finished_nodes:
                        finished_nodes.append(itm)
                        print('Progress: ', len(finished_nodes), '/', len(node_ids), ' Tasks done')
            if message['type'] == 'executing':
                if data['node'] not in finished_nodes:
                    finished_nodes.append(data['node'])
                    print('Progress: ', len(finished_nodes), '/', len(node_ids), ' Tasks done')

                # if data['node'] is None and data['prompt_id'] == prompt_id and not unfinished:
                if has_unfinished_batch:
                    if data['node'] is None and finished:
                        break  # Execution is done
                else:
                    if data['node'] is None and data['prompt_id'] == prompt_id and finished:
                        break
        else:
            continue  # previews are binary data
    return final_prompt_id


def get_outputs(prompt_id, server_address, allow_preview=False):
    output_images = []
    output_videos = []
    history = get_history(prompt_id, server_address)[prompt_id]
    for node_id in history['outputs']:
        node_output = history['outputs'][node_id]
        if 'images' in node_output:
            output_data = {}
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
        if 'gifs' in node_output:
            output_data = {}
            for video in node_output['gifs']:
                if allow_preview and video['type'] == 'temp':
                    preview_data = get_image(video['filename'], video['subfolder'], video['type'], server_address)
                    output_data['video_data'] = preview_data
                if video['type'] == 'output':
                    video_data = get_image(video['filename'], video['subfolder'], video['type'], server_address)
                    output_data['video_data'] = video_data
                    output_data['file_name'] = video['filename']
                    output_data['type'] = video['type']
                    output_videos.append(output_data)

    return output_images, output_videos

