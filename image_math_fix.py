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

class ImageNaNFix:
    """이미지 텐서(B,H,W,C)에서 NaN/Inf를 0으로 대체하고 [0,1] clamp."""
    @classmethod
    def INPUT_TYPES(s):
        return {"required": {"image": ("IMAGE",)}}
    RETURN_TYPES = ("IMAGE",)
    FUNCTION = "execute"
    CATEGORY = "essentials/image"
    def execute(self, image):
        bad = torch.isnan(image) | torch.isinf(image)
        if bad.any():
            n = bad.sum().item()
            print(f"[ImageNaNFix] Fixing {n} NaN/Inf pixels")
            image = image.clone()
            image[bad] = 0.0
        return (torch.clamp(image, 0, 1),)

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
    """KSampler 출력 latent NaN/Inf → 원본 VAEEncode latent 값으로 대체."""
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
        s = samples["samples"].clone()
        f = fallback["samples"].to(device=s.device, dtype=s.dtype)
        if s.shape != f.shape:
            import torch.nn.functional as F
            f = F.interpolate(f, size=s.shape[-2:], mode="bilinear", align_corners=False)
        bad = torch.isnan(s) | torch.isinf(s)
        n_bad = bad.sum().item()
        if n_bad > 0:
            print(f"[LatentNaNFallback] Replacing {n_bad} NaN/Inf values in latent")
            s[bad] = f[bad]
            # fallback 후에도 NaN이 남아있으면 nan_to_num 최종 안전망
            remaining = (torch.isnan(s) | torch.isinf(s)).sum().item()
            if remaining > 0:
                print(f"[LatentNaNFallback] {remaining} values remain bad, applying nan_to_num")
                s = torch.nan_to_num(s, nan=0.0, posinf=1.0, neginf=0.0)
        result = {k: v for k, v in samples.items()}
        result["samples"] = s
        return (result,)

class ConditioningNaNFix:
    """Conditioning 텐서(positive/negative)의 NaN/Inf를 0으로 대체."""
    @classmethod
    def INPUT_TYPES(s):
        return {"required": {"conditioning": ("CONDITIONING",)}}
    RETURN_TYPES = ("CONDITIONING",)
    FUNCTION = "execute"
    CATEGORY = "essentials/conditioning"
    def execute(self, conditioning):
        fixed = []
        for cond_tensor, cond_meta in conditioning:
            if torch.is_tensor(cond_tensor):
                bad = torch.isnan(cond_tensor) | torch.isinf(cond_tensor)
                if bad.any():
                    n = bad.sum().item()
                    print(f"[ConditioningNaNFix] Fixed {n} NaN/Inf in conditioning tensor")
                    cond_tensor = torch.nan_to_num(cond_tensor, nan=0.0, posinf=1.0, neginf=-1.0)
            fixed_meta = {}
            for k, v in cond_meta.items():
                if torch.is_tensor(v):
                    bad = torch.isnan(v) | torch.isinf(v)
                    if bad.any():
                        print(f"[ConditioningNaNFix] Fixed NaN/Inf in meta[{k}]")
                        v = torch.nan_to_num(v, nan=0.0, posinf=1.0, neginf=-1.0)
                fixed_meta[k] = v
            fixed.append([cond_tensor, fixed_meta])
        return (fixed,)

NODE_CLASS_MAPPINGS = {
    "ImageMultiply": ImageMultiply,
    "ImageSubtract": ImageSubtract,
    "ImageNaNFix": ImageNaNFix,
    "LatentNaNFix": LatentNaNFix,
    "LatentNaNFallback": LatentNaNFallback,
    "ConditioningNaNFix": ConditioningNaNFix,
}
NODE_DISPLAY_NAME_MAPPINGS = {
    "ImageMultiply": "Image Multiply",
    "ImageSubtract": "Image Subtract",
    "ImageNaNFix": "Image NaN Fix",
    "LatentNaNFix": "Latent NaN Fix",
    "LatentNaNFallback": "Latent NaN Fallback",
    "ConditioningNaNFix": "Conditioning NaN Fix",
}
