import * as vscode from 'vscode';
import { SidebarProvider } from './sidebarProvider';
import WebSocket from 'ws';

let ws: any = null;
const SERVER_URL = 'ws://localhost:3741/ws/vscode';

export function activate(context: vscode.ExtensionContext) {
  const sidebarProvider = new SidebarProvider(context.extensionUri);
  context.subscriptions.push(
    vscode.window.registerWebviewViewProvider('tobiSidebar', sidebarProvider)
  );

  connectWebSocket(sidebarProvider);

  context.subscriptions.push(
    vscode.workspace.onDidSaveTextDocument((doc) => {
      if (ws?.readyState === WebSocket.OPEN) {
        ws.send(JSON.stringify({
          type: 'event',
          event: 'file_saved',
          path: doc.uri.fsPath,
          content: doc.getText()
        }));
      }
    })
  );

  context.subscriptions.push(
    vscode.window.onDidChangeActiveTextEditor((editor) => {
      if (editor && ws?.readyState === WebSocket.OPEN) {
        ws.send(JSON.stringify({
          type: 'event',
          event: 'file_activated',
          path: editor.document.uri.fsPath,
        }));
      }
    })
  );

  context.subscriptions.push(
    vscode.window.onDidChangeTextEditorSelection((e) => {
      if (ws?.readyState === WebSocket.OPEN) {
        const selectedText = e.textEditor.document.getText(e.selections[0]);
        ws.send(JSON.stringify({
          type: 'event',
          event: 'selection_changed',
          path: e.textEditor.document.uri.fsPath,
          selection: selectedText,
          cursor: {
            line: e.selections[0].active.line,
            character: e.selections[0].active.character
          }
        }));
      }
    })
  );

  context.subscriptions.push(
    vscode.commands.registerCommand('tobi.auditContract', () => {
      const editor = vscode.window.activeTextEditor;
      if (editor) {
        const path = editor.document.uri.fsPath;
        if (ws?.readyState === WebSocket.OPEN) {
          ws.send(JSON.stringify({
            type: 'command',
            command: 'audit_contract',
            path: path
          }));
          vscode.window.showInformationMessage(`Tobi: Auditing ${path}`);
        } else {
          vscode.window.showErrorMessage('Tobi is not connected.');
        }
      }
    })
  );
}

function connectWebSocket(sidebarProvider: SidebarProvider) {
  ws = new WebSocket(SERVER_URL);
  
  ws.on('open', () => {
    console.log('Connected to Tobi backend');
  });

  ws.on('message', (data: any) => {
    try {
      const msg = JSON.parse(data.toString());
      if (msg.type === 'narration') {
        sidebarProvider.sendNarration(msg);
      } else if (msg.type === 'audit_finding') {
        sidebarProvider.sendAuditFinding(msg);
      }
    } catch (e) {
      console.error('Error parsing message from Tobi:', e);
    }
  });

  ws.on('close', () => {
    console.log('Tobi backend disconnected. Retrying in 5s...');
    setTimeout(() => connectWebSocket(sidebarProvider), 5000);
  });
  
  ws.on('error', (err: any) => {
    console.error('WebSocket error', err);
  });
  
  sidebarProvider.setWebSocket(ws);
}

export function deactivate() {
  if (ws) {
    ws.close();
  }
}
