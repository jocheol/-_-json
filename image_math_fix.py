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

class LatentNaNFix:
    @classmethod
    def INPUT_TYPES(s):
        return {"required": {"samples": ("LATENT",)}}
    RETURN_TYPES = ("LATENT",)
    FUNCTION = "execute"
    CATEGORY = "essentials/latent"
    def execute(self, samples):
        fixed = {k: torch.nan_to_num(v, nan=0.0, posinf=1.0, neginf=0.0)
                 if isinstance(v, torch.Tensor) else v
                 for k, v in samples.items()}
        return (fixed,)

class LatentNaNFallback:
    """KSampler 출력 latent에서 NaN/Inf를 원본 encoded latent(VAEEncode)로 대체.
    NaN 위치 → fallback 값 사용, 정상 위치 → sampler 값 유지."""
    @classmethod
    def INPUT_TYPES(s):
        return {"required": {
            "samples": ("LATENT",),
            "fallback": ("LATENT",),
        }}
    RETURN_TYPES = ("LATENT",)
    FUNCTION = "execute"
    CATEGORY = "essentials/latent"
    def execute(self, samples, fallback):
        s = samples["samples"]
        f = fallback["samples"]
        if s.shape != f.shape:
            import torch.nn.functional as F
            f = F.interpolate(f, size=s.shape[-2:], mode="bilinear", align_corners=False)
        bad = torch.isnan(s) | torch.isinf(s)
        fixed_s = torch.where(bad, f, s)
        result = {k: v for k, v in samples.items()}
        result["samples"] = fixed_s
        return (result,)

NODE_CLASS_MAPPINGS = {
    "ImageMultiply": ImageMultiply,
    "ImageSubtract": ImageSubtract,
    "LatentNaNFix": LatentNaNFix,
    "LatentNaNFallback": LatentNaNFallback,
}
NODE_DISPLAY_NAME_MAPPINGS = {
    "ImageMultiply": "Image Multiply",
    "ImageSubtract": "Image Subtract",
    "LatentNaNFix": "Latent NaN Fix",
    "LatentNaNFallback": "Latent NaN Fallback",
}
