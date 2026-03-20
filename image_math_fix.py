import torch

class ImageMultiply:
    @classmethod
    def INPUT_TYPES(s):
        return {"required": {"image": ("IMAGE",), "value": ("FLOAT", {"default": 1.0, "min": 0.0, "max": 10.0, "step": 0.01})}}
    RETURN_TYPES = ("IMAGE",)
    FUNCTION = "execute"
    CATEGORY = "essentials/image"
    def execute(self, image, value):
        return (torch.clamp(image * value, 0, 1),)

class ImageSubtract:
    @classmethod
    def INPUT_TYPES(s):
        return {"required": {"image1": ("IMAGE",), "image2": ("IMAGE",)}}
    RETURN_TYPES = ("IMAGE",)
    FUNCTION = "execute"
    CATEGORY = "essentials/image"
    def execute(self, image1, image2):
        return (torch.clamp(image1 - image2, 0, 1),)

NODE_CLASS_MAPPINGS = {"ImageMultiply": ImageMultiply, "ImageSubtract": ImageSubtract}
NODE_DISPLAY_NAME_MAPPINGS = {"ImageMultiply": "Image Multiply", "ImageSubtract": "Image Subtract"}
