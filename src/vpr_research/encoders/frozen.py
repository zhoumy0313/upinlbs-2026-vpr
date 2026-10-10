"""CosPlace inference adapter with explicit preprocessing and model identity."""
import hashlib
from pathlib import Path

import torch
from torchvision import transforms
import torchvision


class CosPlaceEncoder:
    dimension = 512

    def __init__(self, device="cuda", size_hw=(224, 224)):
        self.device = torch.device(device)
        self.size_hw = tuple(size_hw)
        self.model = torch.hub.load("gmberton/cosplace", "get_trained_model",
                                    backbone="ResNet18", fc_output_dim=self.dimension)
        self.model.requires_grad_(False)
        self.model.eval().to(self.device)
        # Matches the inspected official evaluator's operation order.
        self.transform = transforms.Compose([
            transforms.ToTensor(),
            transforms.Normalize([.485, .456, .406], [.229, .224, .225]),
            transforms.Resize(self.size_hw, antialias=True),
        ])

    def encode(self, images):
        tensors = torch.stack([self.transform(image.convert("RGB")) for image in images]).to(self.device)
        with torch.inference_mode():
            descriptors = self.model(tensors)
            norms = descriptors.norm(dim=1, keepdim=True)
            if not torch.isfinite(descriptors).all() or (norms <= 1e-12).any():
                raise ValueError("Nonfinite/zero visual descriptor")
            descriptors = descriptors / norms
        if descriptors.shape != (len(images), self.dimension):
            raise ValueError("Descriptor shape does not match image IDs")
        return descriptors.cpu().numpy()

    def fingerprint(self):
        # Hash actual loaded parameters rather than infer identity from a filename.
        digest = hashlib.sha256()
        for key, value in sorted(self.model.state_dict().items()):
            digest.update(key.encode())
            digest.update(str(value.dtype).encode())
            digest.update(str(tuple(value.shape)).encode())
            digest.update(value.detach().cpu().contiguous().numpy().tobytes())
        return {"method": "cosplace", "backbone": "ResNet18", "dimension": self.dimension,
                "pooling": "L2 -> GeM -> Flatten -> Linear -> L2", "dtype": "float32",
                "model_state_sha256": digest.hexdigest(), "eval_mode": not self.model.training,
                "all_parameters_frozen": all(not p.requires_grad for p in self.model.parameters()),
                "torch": torch.__version__, "torchvision": torchvision.__version__,
                "adapter_source_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                "preprocessing": {"RGB": True, "resize_hw": list(self.size_hw),
                                  "order": "ToTensor -> ImageNet Normalize -> tensor Resize",
                                  "mean": [.485, .456, .406], "std": [.229, .224, .225],
                                  "interpolation": "bilinear", "antialias": True,
                                  "descriptor_l2_normalization": True}}
