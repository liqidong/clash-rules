# Changelog

## Unreleased

- Route Hugging Face downloads redirected through `us.aws.cdn.hf.co` to the
  dedicated download group.
- Add PyTorch's current R2 wheel content host, observed from the official CPU
  wheel index during canary validation.

## 2026-07-12

- Add initial overseas download rules for model hubs, code releases, Python
  packages, container registries, Kaggle, Conda, and Civitai.
- Add direct rules for ModelScope China and its documented Alibaba Cloud
  endpoints.
- Add dependency-free validation and GitHub Actions CI.
