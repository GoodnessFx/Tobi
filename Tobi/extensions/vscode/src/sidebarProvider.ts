import * as vscode from 'vscode';
import * as WebSocket from 'ws';

export class SidebarProvider implements vscode.WebviewViewProvider {
  _view?: vscode.WebviewView;
  _ws?: WebSocket;

  constructor(private readonly _extensionUri: vscode.Uri) {}

  public resolveWebviewView(webviewView: vscode.WebviewView) {
    this._view = webviewView;
    webviewView.webview.options = {
      enableScripts: true,
      localResourceRoots: [this._extensionUri],
    };

    webviewView.webview.html = this._getHtmlForWebview();

    webviewView.webview.onDidReceiveMessage(async (data) => {
      switch (data.type) {
        case 'onInfo': {
          if (!data.value) {
            return;
          }
          vscode.window.showInformationMessage(data.value);
          break;
        }
        case 'onError': {
          if (!data.value) {
            return;
          }
          vscode.window.showErrorMessage(data.value);
          break;
        }
        case 'action': {
          if (this._ws && this._ws.readyState === WebSocket.OPEN) {
            this._ws.send(JSON.stringify({
              type: 'action',
              action: data.action,
              payload: data.payload
            }));
          }
          break;
        }
      }
    });
  }

  public setWebSocket(ws: WebSocket | null) {
    this._ws = ws || undefined;
  }

  public sendNarration(msg: any) {
    if (this._view) {
      this._view.webview.postMessage({ type: 'narration', data: msg });
    }
  }

  public sendAuditFinding(msg: any) {
    if (this._view) {
      this._view.webview.postMessage({ type: 'audit_finding', data: msg });
    }
  }

  private _getHtmlForWebview() {
    return `<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Tobi Companion</title>
  <style>
    body { font-family: var(--vscode-font-family); padding: 10px; color: var(--vscode-editor-foreground); }
    .card { background: var(--vscode-editorWidget-background); padding: 10px; margin-bottom: 10px; border-radius: 4px; border: 1px solid var(--vscode-widget-border); }
    .title { font-weight: bold; margin-bottom: 5px; }
    .tradeoff { color: var(--vscode-editorWarning-foreground); font-size: 0.9em; margin-bottom: 8px; }
    button { background: var(--vscode-button-background); color: var(--vscode-button-foreground); border: none; padding: 6px 12px; border-radius: 2px; cursor: pointer; margin-right: 5px; }
    button:hover { background: var(--vscode-button-hoverBackground); }
    button.secondary { background: var(--vscode-button-secondaryBackground); color: var(--vscode-button-secondaryForeground); }
    button.secondary:hover { background: var(--vscode-button-secondaryHoverBackground); }
  </style>
</head>
<body>
  <div id="content">Waiting for Tobi...</div>

  <script>
    const vscode = acquireVsCodeApi();
    const content = document.getElementById('content');
    
    window.addEventListener('message', event => {
      const message = event.data;
      
      if (message.type === 'narration') {
        const d = message.data;
        content.innerHTML = \`
          <div class="card">
            <div class="title">Suggested Change</div>
            <p>\${d.explanation}</p>
            <div class="tradeoff"><strong>Tradeoff:</strong> \${d.tradeoff}</div>
            <button onclick="sendAction('build_it', '\${d.id}')">Build It</button>
            <button class="secondary" onclick="sendAction('explain_more', '\${d.id}')">Explain More</button>
          </div>
        \` + content.innerHTML;
      } else if (message.type === 'audit_finding') {
        const d = message.data;
        content.innerHTML = \`
          <div class="card">
            <div class="title">Audit: \${d.vulnerability_class}</div>
            <p>\${d.explanation}</p>
            <div class="tradeoff">\${d.severity}</div>
          </div>
        \` + content.innerHTML;
      }
    });

    function sendAction(action, id) {
      vscode.postMessage({ type: 'action', action, payload: { id } });
    }
  </script>
</body>
</html>`;
  }
}
