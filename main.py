from utils.actions.prompt_to_image import prompt_to_image
from utils.actions.prompt_image_to_image import prompt_image_to_image
from utils.actions.prompt_image_to_video import prompt_image_to_video
from utils.actions.load_workflow import load_workflow
import api.api_helpers as comfyui_api_helper
from api.open_websocket import open_websocket_connection
import sys


def main():
    print("Welcome to the program!")
    # comfyui_api_helper.web_socket_helper = comfyui_api_helper.WebSocketHelper(ip='877328s68c.vicp.fun', port=43592)
    comfyui_api_helper.web_socket_helper = comfyui_api_helper.WebSocketHelper(ip='127.0.0.1', port=8288)
    workflow = load_workflow('./workflows/PictureMe.json')
    # input_path = './input/wechat.png'
    input_path = r'./input/annehathaway.png'
    prompt_image_to_image(workflow, input_path=input_path, positive_prompt='Monet style portrait')
    print("Done!")


if __name__ == '__main__':
    main()

