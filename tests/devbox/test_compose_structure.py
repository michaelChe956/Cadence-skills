# -*- coding: utf-8 -*-
"""devbox/compose.yaml 与 stack/catalog 的结构化契约校验。"""
from pathlib import Path

import yaml

REPO = Path(__file__).resolve().parents[2]
COMPOSE = REPO / "devbox" / "compose.yaml"
CATALOG = REPO / "devbox" / "stack" / "catalog"
MW = ("mysql", "redis", "rabbitmq", "minio")


def test_yaml_parses_and_services_is_last_top_key():
    text = COMPOSE.read_text(encoding="utf-8")
    doc = yaml.safe_load(text)
    assert list(doc.keys())[-1] == "services"
    assert doc["name"] == "cadence"


def test_all_ports_bind_loopback_only():
    doc = yaml.safe_load(COMPOSE.read_text(encoding="utf-8"))
    for svc, spec in doc["services"].items():
        for port in spec.get("ports", []):
            assert str(port).startswith("127.0.0.1:"), f"{svc} 端口未仅绑 127.0.0.1：{port}"


def test_all_volumes_are_external():
    doc = yaml.safe_load(COMPOSE.read_text(encoding="utf-8"))
    assert doc["volumes"], "缺少顶层卷声明"
    for name, spec in doc["volumes"].items():
        assert spec.get("external") is True, f"卷 {name} 未声明 external:true"


def test_profiles_matrix():
    doc = yaml.safe_load(COMPOSE.read_text(encoding="utf-8"))
    assert doc["services"]["rabbitmq"]["profiles"] == ["mq"]
    assert doc["services"]["minio"]["profiles"] == ["storage"]
    for service in ("mysql", "redis", "devbox"):
        assert "profiles" not in doc["services"][service], f"{service} 不应挂 profile"


def test_image_pins_and_devbox_mounts():
    doc = yaml.safe_load(COMPOSE.read_text(encoding="utf-8"))
    services = doc["services"]
    assert services["mysql"]["image"].startswith("mysql:8.4")
    assert services["redis"]["image"].startswith("redis:7")
    assert services["rabbitmq"]["image"].startswith("rabbitmq:3")
    assert services["minio"]["image"].startswith("minio/minio:RELEASE.")
    assert "${CADENCE_DEVBOX_IMAGE:" in services["devbox"]["image"]

    volumes = services["devbox"]["volumes"]
    assert "/var/run/docker.sock:/var/run/docker.sock" in volumes
    assert ".:/cadence/stack" in volumes
    assert "../cadence-box.yaml:/cadence/auth.yaml:ro" in volumes
    assert any(volume.startswith("${CADENCE_WORKSPACE") and volume.endswith(":/workspace") for volume in volumes)
    for mount in (
        "cadence-claude:/home/dev/.claude", "cadence-codex:/home/dev/.codex",
        "cadence-pi:/home/dev/.pi/agent", "cadence-kimi:/home/dev/.kimi-code",
        "cadence-agents:/home/dev/.agents", "cadence-omp:/home/dev/.omp",
        "cadence-m2:/home/dev/.m2", "cadence-npm:/home/dev/.npm",
        "cadence-npm-global:/home/dev/.npm-global", "cadence-uv:/home/dev/.cache/uv",
        "cadence-pip:/home/dev/.cache/pip", "cadence-gradle:/home/dev/.gradle",
    ):
        assert mount in volumes, f"devbox 缺挂载 {mount}"
    for service in MW:
        assert any(volume.startswith(f"cadence-{service}-data:") for volume in services[service]["volumes"])


def test_middleware_healthchecks_present():
    doc = yaml.safe_load(COMPOSE.read_text(encoding="utf-8"))
    for service in MW:
        assert "healthcheck" in doc["services"][service], f"{service} 缺 healthcheck"


def test_catalog_layout_and_parseable_fragments():
    profiles = {"mysql": "default", "redis": "default", "rabbitmq": "mq", "minio": "storage"}
    for service in MW:
        directory = CATALOG / service
        assert (directory / "profile").read_text(encoding="utf-8").strip() == profiles[service]
        conn = (directory / "conn.txt").read_text(encoding="utf-8")
        assert f"{service}:" in conn.replace("://", "#")
        fragment = (directory / "service.fragment.yaml").read_text(encoding="utf-8")
        assert fragment.splitlines()[0].startswith(f"  {service}:")
        yaml.safe_load("services:\n" + fragment)
    assert "[mysqld]" in (CATALOG / "mysql" / "conf" / "my.cnf").read_text(encoding="utf-8")
    assert "appendonly" in (CATALOG / "redis" / "conf" / "redis.conf").read_text(encoding="utf-8")


def test_no_sock_override_replaces_volumes_without_socket():
    text = (REPO / "devbox" / "stack" / "docker-compose.no-sock.yml").read_text(encoding="utf-8")
    assert "/var/run/docker.sock" not in text
    assert "!override" in text
    assert "cadence-claude:/home/dev/.claude" in text
