import logging
from typing import Optional

logger = logging.getLogger("Tobi.tools.vscode_bridge")

class VsCodeBridge:
    def __init__(self):
        self._ws: Optional[object] = None
        self._latest_context = {}

    def set_ws(self, ws):
        self._ws = ws

    def clear_ws(self):
        self._ws = None

    async def handle_message(self, data: dict):
        if data.get("type") == "event":
            if data.get("event") == "file_activated":
                self._latest_context["active_file"] = data.get("path")
            elif data.get("event") == "selection_changed":
                self._latest_context["selection"] = data.get("selection")
                self._latest_context["cursor"] = data.get("cursor")
            elif data.get("event") == "file_saved":
                logger.info(f"VS Code file saved: {data.get('path')}")
                
        elif data.get("type") == "command":
            if data.get("command") == "audit_contract":
                # Simulated audit flow as specified in instructions
                await self.send_message({
                    "type": "audit_finding",
                    "vulnerability_class": "Reentrancy",
                    "explanation": "External call made before state update. Recommend moving state updates above the external call or using a ReentrancyGuard.",
                    "severity": "High"
                })

    async def send_message(self, msg: dict):
        if self._ws:
            try:
                await self._ws.send_json(msg)
            except Exception as e:
                logger.error(f"Failed to send to VS Code: {e}")

vscode_bridge = VsCodeBridge()
