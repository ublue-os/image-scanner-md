import httpx
from dataclasses import dataclass


_default_domain = "docker.io"
_official_repo_name = "library"


@dataclass
class ImageMeta:
    """Container image metadata"""

    name: str
    tags: list[str]
    labels: dict[str, str]

    @property
    def description(self):
        return self.labels.get("org.opencontainers.image.description", "")

    @property
    def title(self):
        return self.labels.get("org.opencontainers.image.title", "")

    @property
    def created(self):
        return self.labels.get("org.opencontainers.image.created", "")

    @property
    def logo(self):
        return self.labels.get("io.artifacthub.package.logo-url", "")


# https://stackoverflow.com/a/37867949
def normalize_image(name: str):
    domain = None
    path = None
    idx = name.find("/")

    if idx == -1:
        name = f"{_official_repo_name}/{name}"

    if not ("." in name[:idx] or ":" in name[:idx]) and name[:idx] != "localhost":
        domain = _default_domain
        path = name
    else:
        domain = name[:idx]
        path = name[idx + 1 :]

    return (domain, path)


class RegistryV2Image:
    _token = None
    api_version = "v2"

    def __init__(self, image: str):
        host, path = normalize_image(image)
        self.image = path
        self.host = host

    @property
    def url(self):
        return f"https://{self.host}/{self.api_version}"

    @property
    def token(self):
        if not self._token:
            self.login()
        return self._token

    def request(self, path: str, method: str = "get"):
        return httpx.request(
            method,
            f"{self.url}{path}",
            headers={"Authorization": f"Bearer {self.token}"},
            follow_redirects=True,
        )

    def tags(self):
        resp = self.request(f"/{self.image}/tags/list")
        return resp.json().get("tags", [])

    def manifest(self, tag: str = "latest"):
        r = self.request(f"/{self.image}/manifests/{tag}")
        return r.json()

    def config(self, tag: str = "latest"):
        resp = self.manifest(tag)
        config = resp.get("config")
        if not config:
            raise Exception("No metadata found")

        image_config = self.get_blob(config.get("digest"))
        return image_config.get("config")

    def meta(self, tag: str = "latest"):
        tags = self.tags()
        config = self.config(tag)
        return ImageMeta(name=self.image, tags=tags, labels=config.get("Labels", {}))

    def get_blob(self, blob: str):
        resp = self.request(f"/{self.image}/blobs/{blob}")
        return resp.json()

    def login(self):
        resp = httpx.get(
            f"https://ghcr.io/token?scope=repository%3A{self.image}%3Apull&service=ghcr.io"
        )
        resp.raise_for_status()
        self._token = resp.json().get("token")
