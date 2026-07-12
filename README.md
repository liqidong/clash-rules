# Personal Clash routing rules

Small, auditable Mihomo rule providers for personal multi-device use. This
repository contains destination domains only. It must never contain proxy
nodes, server addresses, UUIDs, passwords, certificates, access tokens, or
rendered client profiles.

## Files and routing contract

- `rules/ai-reality.yaml`: OpenAI, Claude, and Gemini core destinations. Clients
  route this provider to `AI-Stable`, whose fresh-profile default is REALITY.
- `rules/streaming-hy2.yaml`: YouTube and Netflix destinations. Clients route
  this provider to `Streaming`, whose default is the HY2-first `General-Auto`.
- `rules/download-proxy.yaml`: overseas model, dataset, package, release, and
  container downloads. Clients route this provider to `Download`, whose
  default is the HY2-first `General-Auto`.
- `rules/download-direct.yaml`: regional endpoints that should avoid a detour
  through the Silicon Valley server. Clients route this provider to `DIRECT`.

The first release covers Hugging Face, GitHub, PyPI, PyTorch, Docker, GitHub
Container Registry, Kaggle, Conda/Anaconda, Civitai, and ModelScope.

## Release channels

- `main` receives proposed changes and is used for canary testing.
- `stable` is the only branch production client profiles should poll.

Changes are promoted to `stable` only after validation and a spare-client
canary. Roll back a bad rule with a normal revert; do not rewrite branch
history.

## Mihomo integration

```yaml
rule-providers:
  personal-ai-reality:
    type: http
    behavior: classical
    format: yaml
    url: https://raw.githubusercontent.com/liqidong/clash-rules/stable/rules/ai-reality.yaml
    path: ./ruleset/personal-ai-reality.yaml
    interval: 86400
    proxy: General-Auto
    size-limit: 65536

  personal-streaming:
    type: http
    behavior: classical
    format: yaml
    url: https://raw.githubusercontent.com/liqidong/clash-rules/stable/rules/streaming-hy2.yaml
    path: ./ruleset/personal-streaming-hy2.yaml
    interval: 86400
    proxy: General-Auto
    size-limit: 65536

  personal-download-proxy:
    type: http
    behavior: classical
    format: yaml
    url: https://raw.githubusercontent.com/liqidong/clash-rules/stable/rules/download-proxy.yaml
    path: ./ruleset/personal-download-proxy.yaml
    interval: 86400
    proxy: General-Auto
    size-limit: 65536

  personal-download-direct:
    type: http
    behavior: classical
    format: yaml
    url: https://raw.githubusercontent.com/liqidong/clash-rules/stable/rules/download-direct.yaml
    path: ./ruleset/personal-download-direct.yaml
    interval: 86400
    proxy: General-Auto
    size-limit: 65536
```

Keep a small local AI core before the providers so first import remains safe if
GitHub Raw is unavailable. Do not add a broad `googleapis.com` AI rule:

```yaml
rules:
  - DOMAIN-SUFFIX,openai.com,AI-Stable
  - DOMAIN-SUFFIX,anthropic.com,AI-Stable
  - DOMAIN-SUFFIX,generativelanguage.googleapis.com,AI-Stable
  - RULE-SET,personal-ai-reality,AI-Stable
  - RULE-SET,personal-download-direct,DIRECT
  - RULE-SET,personal-download-proxy,Download
  - RULE-SET,personal-streaming,Streaming
  - MATCH,Proxy
```

## Validation

```sh
python3 scripts/validate_rules.py
```

Validation rejects cross-file duplicate domains, malformed domains, files over
64 KiB, keyword rules, IP rules, secret/proxy material, and intentionally
over-broad shared CDN suffixes. Suffix approval is scoped to each rule file, so
an AI suffix cannot silently move into a download or streaming policy.
Dynamic redirect hosts must be observed in a canary connection log before they
are added.

## Endpoint references

- [Mihomo rule providers](https://wiki.metacubex.one/en/config/rule-providers/)
- [Hugging Face downloads](https://huggingface.co/docs/huggingface_hub/en/guides/download)
- [GitHub runner network endpoints](https://docs.github.com/en/actions/reference/runners/github-hosted-runners)
- [Docker Desktop allowlist](https://docs.docker.com/desktop/setup/allow-list/)
- [ModelScope model downloads](https://modelscope.cn/docs/models/download)
- [Kaggle CLI](https://github.com/Kaggle/kaggle-cli)
- [Anaconda firewall requirements](https://www.anaconda.com/docs/data-science/latest/environment-prep/k3s-prep)
- [Civitai download API](https://github.com/civitai/civitai/wiki/REST-API-Reference)
