#!/usr/bin/env python3
"""Verify CUDA allocation, matrix multiplication and a torchvision operator."""
import json
import sys
import torch
import torchvision

assert sys.prefix != sys.base_prefix, "Use the isolated virtual environment"
assert not any("/opt/ros" in entry for entry in sys.path), "Clear inherited ROS PYTHONPATH"
assert torch.cuda.is_available(), "CUDA unavailable; select CPU instead"
torch.manual_seed(0)
cpu = torch.randn(64, 64)
gpu = cpu.cuda()
result = gpu @ gpu.T
torch.cuda.synchronize()
torch.testing.assert_close(result.cpu(), cpu @ cpu.T, atol=1e-4, rtol=1e-4)
boxes = torch.tensor([[0., 0., 1., 1.], [0., 0., 1., 1.]], device="cuda")
kept = torchvision.ops.nms(boxes, torch.tensor([.9, .8], device="cuda"), .5)
assert kept.tolist() == [0]
print(json.dumps({"python": sys.version, "prefix": sys.prefix, "torch": torch.__version__,
                  "torchvision": torchvision.__version__, "cuda_runtime": torch.version.cuda,
                  "cuda_available": True, "gpu": torch.cuda.get_device_name(0),
                  "capability": list(torch.cuda.get_device_capability(0)),
                  "total_vram_bytes": torch.cuda.get_device_properties(0).total_memory,
                  "cuda_matmul_cpu_agreement": True, "torchvision_cuda_nms": True,
                  "sys_path": sys.path}, indent=2))
