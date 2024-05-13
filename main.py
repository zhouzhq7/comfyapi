from utils.actions.prompt_to_image import prompt_to_image
from utils.actions.prompt_image_to_image import prompt_image_to_image
from utils.actions.prompt_image_to_video import prompt_image_to_video
from utils.actions.load_workflow import load_workflow
import utils.actions.prompt_helper as prompt_helper
from api.open_websocket import open_websocket_connection
import sys


def main():
    # print("Welcome to the program!")
    # prompt_helper.web_socket_helper = prompt_helper.WebSocketHelper(ip='877328s68c.vicp.fun', port=43592)
    prompt_helper.web_socket_helper = prompt_helper.WebSocketHelper(ip='192.168.0.21', port=8288)
    workflow = load_workflow('./workflows/ImageStylization.json')
    # input_path = './input/wechat.png'
    user_inputs = {'PortraitImage': './input/annehathaway.png',
                   'StyleImage': './input/Starry-Night-canvas-Vincent-van-Gogh-New-1889.png'}
    prompt_helper.prompt_helper(workflow, user_inputs)
    # prompt_image_to_image(workflow, input_path='./input/wechat.png')
    print("Done!")


if __name__ == '__main__':
    main()

