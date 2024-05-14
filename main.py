from comfy_client import ComfyClient
from utils import load_workflow


def main():
    print("Welcome to the program!")
    # comfy_client = ComfyClient(ip='877328s68c.vicp.fun', port=43592)
    comfy_client = ComfyClient(ip='192.168.0.21', port=8288)
    # workflow = load_workflow('./workflows/ImageStylization.json')
    # user_inputs = {'PortraitImage': './input/daisy_avatar.jpg',
    #                'StyleImage': './input/Starry-Night-canvas-Vincent-van-Gogh-New-1889.png',
    #                'PositivePrompt': 'a girl portrait stand in front a river'}
    workflow = load_workflow('./workflows/FaceSwap.json')
    user_inputs = {'SourceVideo': './input/test_3s.mp4',
                   'TargetFace': './input/annehathaway.png',
                   'FPS': 30}
    comfy_client.run_workflow(workflow, user_inputs)
    print("Done!")


if __name__ == '__main__':
    main()
