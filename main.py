from utils.actions.prompt_to_image import prompt_to_image
from utils.actions.prompt_image_to_image import prompt_image_to_image
from utils.actions.load_workflow import load_workflow
import api.api_helpers as comfyui_api_helper
from api.open_websocket import open_websocket_connection
import sys


def main():
    print("Welcome to the program!")
    comfyui_api_helper.web_socket_helper = comfyui_api_helper.WebSocketHelper(ip='877328s68c.vicp.fun', port=43592)
    workflow = load_workflow('./workflows/FluffyIconAPI.json')
    input_path = './input/QQvedio.png'
    prompt_image_to_image(workflow, input_path, save_previews=True)
    print("Done!")


if __name__ == '__main__':
    main()

