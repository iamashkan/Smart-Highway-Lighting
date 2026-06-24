from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from typing import Any, Callable

from .config import MqttConfig


MessageCallback = Callable[[str, dict[str, Any]], None]


@dataclass
class MqttBridge:
    config: MqttConfig
    callbacks: dict[str, MessageCallback] = field(default_factory=dict)
    connected: bool = False
    _client: Any = None

    def connect(self) -> bool:
        if not self.config.enabled:
            return False
        try:
            import paho.mqtt.client as mqtt  # type: ignore
        except ImportError:
            print("paho-mqtt is not installed; continuing in offline MQTT simulation mode.")
            return False

        self._client = mqtt.Client(client_id=f"{self.config.client_id}-{int(time.time())}")
        self._client.on_message = self._on_message
        try:
            self._client.connect(self.config.host, self.config.port, self.config.keepalive)
            self._client.loop_start()
            self.connected = True
        except OSError as exc:
            print(f"MQTT broker unavailable at {self.config.host}:{self.config.port}: {exc}")
            self.connected = False
        return self.connected

    def _on_message(self, client: Any, userdata: Any, message: Any) -> None:
        try:
            payload = json.loads(message.payload.decode("utf-8"))
        except json.JSONDecodeError:
            payload = {"raw": message.payload.decode("utf-8", errors="replace")}
        for pattern, callback in self.callbacks.items():
            if self._topic_matches(pattern, message.topic):
                callback(message.topic, payload)

    def subscribe_json(self, topic: str, callback: MessageCallback) -> None:
        self.callbacks[topic] = callback
        if self.connected and self._client is not None:
            self._client.subscribe(topic)

    def publish_json(self, topic: str, payload: dict[str, Any], retain: bool = False) -> None:
        if self.connected and self._client is not None:
            self._client.publish(topic, json.dumps(payload), retain=retain)

    def stop(self) -> None:
        if self._client is not None:
            self._client.loop_stop()
            self._client.disconnect()
        self.connected = False

    @staticmethod
    def _topic_matches(pattern: str, topic: str) -> bool:
        pattern_parts = pattern.split("/")
        topic_parts = topic.split("/")
        if len(pattern_parts) != len(topic_parts):
            return False
        return all(p == "+" or p == t for p, t in zip(pattern_parts, topic_parts))


def topic(base: str, *parts: str) -> str:
    return "/".join([base.strip("/"), *[part.strip("/") for part in parts]])
