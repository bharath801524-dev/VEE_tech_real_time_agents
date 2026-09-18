import type { WSMessage, WSMessageType } from '../types';

type WSListener = (msg: WSMessage) => void;

class WebSocketService {
  private ws: WebSocket | null = null;
  private listeners: Map<WSMessageType | 'ALL', Set<WSListener>> = new Map();
  private reconnectTimer: ReturnType<typeof setTimeout> | null = null;
  private reconnectDelay = 2000;
  private url: string;
  public connected = false;

  constructor() {
    this.url = `ws://${window.location.hostname}:8000/ws/live`;
  }

  connect() {
    if (this.ws && (this.ws.readyState === WebSocket.OPEN || this.ws.readyState === WebSocket.CONNECTING)) return;
    try {
      this.ws = new WebSocket(this.url);
      this.ws.onopen = () => {
        this.connected = true;
        this.reconnectDelay = 2000;
        console.log('[WS] Connected to MindMesh backend');
        this.emit({ type: 'CONNECTED', data: null, timestamp: Date.now() });
      };
      this.ws.onmessage = (ev) => {
        try {
          const msg: WSMessage = JSON.parse(ev.data);
          this.emit(msg);
        } catch { /* ignore malformed */ }
      };
      this.ws.onclose = () => {
        this.connected = false;
        this.scheduleReconnect();
      };
      this.ws.onerror = () => {
        this.connected = false;
      };
    } catch { /* ignore */ }
  }

  private scheduleReconnect() {
    if (this.reconnectTimer) return;
    this.reconnectTimer = setTimeout(() => {
      this.reconnectTimer = null;
      this.reconnectDelay = Math.min(this.reconnectDelay * 1.5, 15000);
      this.connect();
    }, this.reconnectDelay);
  }

  private emit(msg: WSMessage) {
    // Fire type-specific listeners
    const typed = this.listeners.get(msg.type);
    typed?.forEach(fn => fn(msg));
    // Fire wildcard listeners
    const all = this.listeners.get('ALL');
    all?.forEach(fn => fn(msg));
  }

  on(type: WSMessageType | 'ALL', fn: WSListener) {
    if (!this.listeners.has(type)) this.listeners.set(type, new Set());
    this.listeners.get(type)!.add(fn);
    return () => this.off(type, fn);
  }

  off(type: WSMessageType | 'ALL', fn: WSListener) {
    this.listeners.get(type)?.delete(fn);
  }

  disconnect() {
    if (this.reconnectTimer) { clearTimeout(this.reconnectTimer); this.reconnectTimer = null; }
    this.ws?.close();
    this.ws = null;
    this.connected = false;
  }
}

export const wsService = new WebSocketService();
