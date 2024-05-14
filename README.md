# comfyapi

### Usage Example
Simple example shows how to use ComfyClient
```python
comfy_client = ComfyClient(ip='127.0.0.1', port=8288)
workflow = load_workflow('./workflows/ImageStylization.json')
user_inputs = {'PortraitImage': './input/daisy_avatar.jpg',
               'StyleImage': './input/Starry-Night-canvas-Vincent-van-Gogh-New-1889.png',
               'PositivePrompt': 'a girl portrait stand in front a river'}
comfy_client.run_workflow(workflow, user_inputs)
```

### ComfyUI Node Title for Input
Title of node for user input should follow certain format,

**[Input]-KeyWord**, such as [Input]-StyleImage
![sample_comfy.png](imgs%2Fsample_comfy.png)