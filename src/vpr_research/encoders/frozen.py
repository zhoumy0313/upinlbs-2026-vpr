"""Frozen source-pinned image-only encoders; no online label fields."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys

import torch
from torchvision import transforms
import torchvision

ROOT = Path(__file__).resolve().parents[3]


def sha256(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


class FrozenEncoder:
    def _source(self, method):
        self.method = method
        self.source = json.loads((ROOT / "configs/model_sources.json").read_text())[method]
        folder = ROOT / self.source["local_directory"]
        commit = subprocess.check_output(["git", "-C", str(folder), "rev-parse", "HEAD"], text=True).strip()
        if commit != self.source["commit"]:
            raise ValueError("Model source commit differs from pinned configuration")
        if subprocess.check_output(["git", "-C", str(folder), "status", "--porcelain"], text=True).strip():
            raise ValueError("Model source has unrecorded modifications")
        checkpoint = ROOT / self.source["checkpoint"]
        if sha256(checkpoint) != self.source["checkpoint_sha256"]:
            raise ValueError("Checkpoint differs from recorded identity; retain and investigate")
        self.source_python_sha256 = {str(p.relative_to(folder)): sha256(p)
                                     for p in sorted(folder.rglob("*.py")) if ".git" not in p.parts}
        return folder, checkpoint

    def _freeze(self, device, size_hw):
        # Keep the declared float32 path consistent across extraction batch sizes.
        torch.backends.cuda.matmul.allow_tf32 = False
        torch.backends.cudnn.allow_tf32 = False
        torch.backends.cudnn.benchmark = False
        self.device = torch.device(device)
        self.size_hw = tuple(size_hw)
        self.model.requires_grad_(False)
        self.model.eval().to(self.device)
        self.transform = transforms.Compose([
            transforms.ToTensor(),
            transforms.Normalize([.485, .456, .406], [.229, .224, .225]),
            transforms.Resize(self.size_hw, antialias=True),
        ])

    def prepare(self, images):
        if not images:
            raise ValueError("An image batch cannot be empty")
        return torch.stack([self.transform(image.convert("RGB")) for image in images])

    def encode_tensor(self, tensors):
        with torch.inference_mode():
            descriptors = self._forward(tensors.to(self.device))
            if descriptors.shape != (len(tensors), self.dimension):
                raise ValueError("Descriptor shape does not match image count")
            norms = descriptors.norm(dim=1, keepdim=True)
            if not torch.isfinite(descriptors).all() or (norms <= 1e-12).any():
                raise ValueError("Nonfinite/zero visual descriptor")
            return descriptors / norms

    def encode(self, images):
        return self.encode_tensor(self.prepare(images)).cpu().numpy()

    def fingerprint(self):
        digest = hashlib.sha256()
        for key, value in sorted(self.model.state_dict().items()):
            digest.update(key.encode())
            digest.update(str(value.dtype).encode())
            digest.update(str(tuple(value.shape)).encode())
            digest.update(value.detach().cpu().contiguous().numpy().tobytes())
        return {"method": self.method, "backbone": self.backbone, "dimension": self.dimension,
                "pooling": self.pooling, "dtype": "float32", "source": self.source,
                "source_python_sha256": self.source_python_sha256,
                "model_state_sha256": digest.hexdigest(), "eval_mode": not self.model.training,
                "all_parameters_frozen": all(not p.requires_grad for p in self.model.parameters()),
                "torch": torch.__version__, "torchvision": torchvision.__version__,
                "numerics": {"cuda_matmul_tf32": torch.backends.cuda.matmul.allow_tf32,
                             "cudnn_tf32": torch.backends.cudnn.allow_tf32,
                             "cudnn_benchmark": torch.backends.cudnn.benchmark},
                "adapter_source_sha256": sha256(__file__),
                "preprocessing": {"RGB": True, "resize_hw": list(self.size_hw),
                                  "order": "ToTensor -> ImageNet Normalize -> tensor Resize",
                                  "mean": [.485, .456, .406], "std": [.229, .224, .225],
                                  "interpolation": "bilinear", "antialias": True,
                                  "descriptor_l2_normalization": True,
                                  "setting": "protocol full-image low-resolution warp; not original paper reproduction"}}


class CosPlaceEncoder(FrozenEncoder):
    dimension = 512
    backbone = "ResNet18"
    pooling = "L2 -> GeM -> Flatten -> Linear -> L2"

    def __init__(self, device="cuda", size_hw=(224, 224)):
        folder, _ = self._source("cosplace")
        self.model = torch.hub.load(str(folder), "get_trained_model", source="local",
                                    backbone=self.backbone, fc_output_dim=self.dimension)
        self._freeze(device, size_hw)

    def _forward(self, tensor):
        return self.model(tensor)


class DinoV2Encoder(FrozenEncoder):
    dimension = 384
    backbone = "dinov2_vits14"
    pooling = "final LayerNorm CLS -> descriptor L2; no registers"

    def __init__(self, device="cuda", size_hw=(224, 224)):
        folder, checkpoint = self._source("dinov2")
        sys.path.insert(0, str(folder))
        from dinov2.hub.backbones import dinov2_vits14
        self.model = dinov2_vits14(pretrained=False)
        self.model.load_state_dict(torch.load(checkpoint, map_location="cpu", weights_only=True), strict=True)
        if self.model.num_register_tokens != 0 or self.model.embed_dim != self.dimension:
            raise ValueError("Wrong DINOv2 architecture")
        if any(int(size) % 14 for size in size_hw):
            raise ValueError("DINOv2 size must be divisible by patch size14")
        self._freeze(device, size_hw)

    def _forward(self, tensor):
        return self.model.forward_features(tensor)["x_norm_clstoken"]


class EigenPlacesEncoder(FrozenEncoder):
    dimension = 512
    backbone = "ResNet50"
    pooling = "L2 -> GeM -> Flatten -> Linear -> L2"

    def __init__(self, device="cuda", size_hw=(224, 224)):
        folder, checkpoint = self._source("eigenplaces")
        sys.path.insert(0, str(folder))
        from eigenplaces_model import eigenplaces_network
        from unittest.mock import patch
        # The official constructor downloads an unrelated CosPlace initializer.
        # Every backbone/aggregation tensor is replaced by the complete EigenPlaces
        # checkpoint below, strictly. Preserve official modules and forward code.
        backbone = torch.nn.Sequential(*list(torchvision.models.resnet50(weights=None).children())[:-2])
        with patch.object(eigenplaces_network, "_get_backbone", return_value=(backbone, 2048)):
            self.model = eigenplaces_network.GeoLocalizationNet_(self.backbone, self.dimension)
        state = torch.load(checkpoint, map_location="cpu", weights_only=True)
        self.model.load_state_dict(state, strict=True)
        for key, value in self.model.state_dict().items():
            if not torch.equal(value, state[key]):
                raise ValueError("Loaded EigenPlaces state differs from the complete checkpoint")
        self._freeze(device, size_hw)

    def _forward(self, tensor):
        return self.model(tensor)


def create_encoder(method, device, size_hw=(224, 224)):
    return {"cosplace": CosPlaceEncoder, "dinov2": DinoV2Encoder,
            "eigenplaces": EigenPlacesEncoder}[method](device, size_hw)
