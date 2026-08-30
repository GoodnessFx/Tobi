"use strict";
var __createBinding = (this && this.__createBinding) || (Object.create ? (function(o, m, k, k2) {
    if (k2 === undefined) k2 = k;
    var desc = Object.getOwnPropertyDescriptor(m, k);
    if (!desc || ("get" in desc ? !m.__esModule : desc.writable || desc.configurable)) {
      desc = { enumerable: true, get: function() { return m[k]; } };
    }
    Object.defineProperty(o, k2, desc);
}) : (function(o, m, k, k2) {
    if (k2 === undefined) k2 = k;
    o[k2] = m[k];
}));
var __setModuleDefault = (this && this.__setModuleDefault) || (Object.create ? (function(o, v) {
    Object.defineProperty(o, "default", { enumerable: true, value: v });
}) : function(o, v) {
    o["default"] = v;
});
var __importStar = (this && this.__importStar) || (function () {
    var ownKeys = function(o) {
        ownKeys = Object.getOwnPropertyNames || function (o) {
            var ar = [];
            for (var k in o) if (Object.prototype.hasOwnProperty.call(o, k)) ar[ar.length] = k;
            return ar;
        };
        return ownKeys(o);
    };
    return function (mod) {
        if (mod && mod.__esModule) return mod;
        var result = {};
        if (mod != null) for (var k = ownKeys(mod), i = 0; i < k.length; i++) if (k[i] !== "default") __createBinding(result, mod, k[i]);
        __setModuleDefault(result, mod);
        return result;
    };
})();
var __importDefault = (this && this.__importDefault) || function (mod) {
    return (mod && mod.__esModule) ? mod : { "default": mod };
};
Object.defineProperty(exports, "__esModule", { value: true });
exports.activate = activate;
exports.deactivate = deactivate;
const vscode = __importStar(require("vscode"));
const sidebarProvider_1 = require("./sidebarProvider");
const ws_1 = __importDefault(require("ws"));
let ws = null;
const SERVER_URL = 'ws://localhost:3741/ws/vscode';
function activate(context) {
    const sidebarProvider = new sidebarProvider_1.SidebarProvider(context.extensionUri);
    context.subscriptions.push(vscode.window.registerWebviewViewProvider('tobiSidebar', sidebarProvider));
    connectWebSocket(sidebarProvider);
    context.subscriptions.push(vscode.workspace.onDidSaveTextDocument((doc) => {
        if (ws?.readyState === ws_1.default.OPEN) {
            ws.send(JSON.stringify({
                type: 'event',
                event: 'file_saved',
                path: doc.uri.fsPath,
                content: doc.getText()
            }));
        }
    }));
    context.subscriptions.push(vscode.window.onDidChangeActiveTextEditor((editor) => {
        if (editor && ws?.readyState === ws_1.default.OPEN) {
            ws.send(JSON.stringify({
                type: 'event',
                event: 'file_activated',
                path: editor.document.uri.fsPath,
            }));
        }
    }));
    context.subscriptions.push(vscode.window.onDidChangeTextEditorSelection((e) => {
        if (ws?.readyState === ws_1.default.OPEN) {
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
    }));
    context.subscriptions.push(vscode.commands.registerCommand('tobi.auditContract', () => {
        const editor = vscode.window.activeTextEditor;
        if (editor) {
            const path = editor.document.uri.fsPath;
            if (ws?.readyState === ws_1.default.OPEN) {
                ws.send(JSON.stringify({
                    type: 'command',
                    command: 'audit_contract',
                    path: path
                }));
                vscode.window.showInformationMessage(`Tobi: Auditing ${path}`);
            }
            else {
                vscode.window.showErrorMessage('Tobi is not connected.');
            }
        }
    }));
}
function connectWebSocket(sidebarProvider) {
    ws = new ws_1.default(SERVER_URL);
    ws.on('open', () => {
        console.log('Connected to Tobi backend');
    });
    ws.on('message', (data) => {
        try {
            const msg = JSON.parse(data.toString());
            if (msg.type === 'narration') {
                sidebarProvider.sendNarration(msg);
            }
            else if (msg.type === 'audit_finding') {
                sidebarProvider.sendAuditFinding(msg);
            }
        }
        catch (e) {
            console.error('Error parsing message from Tobi:', e);
        }
    });
    ws.on('close', () => {
        console.log('Tobi backend disconnected. Retrying in 5s...');
        setTimeout(() => connectWebSocket(sidebarProvider), 5000);
    });
    ws.on('error', (err) => {
        console.error('WebSocket error', err);
    });
    sidebarProvider.setWebSocket(ws);
}
function deactivate() {
    if (ws) {
        ws.close();
    }
}
//# sourceMappingURL=extension.js.map