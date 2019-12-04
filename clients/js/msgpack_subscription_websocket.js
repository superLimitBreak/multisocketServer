import { encode, decode } from "@msgpack/msgpack";


export class SocketReconnect {

    constructor(kwargs) {
        Object.assign(this, {
            'WebSocket': WebSocket,
            'url': `ws://${location.hostname}:9873`,
            'disconnected_retry_interval_ms': 5000,
            'console': console,
            'encode': (msg) => msg,
            'decode': (data) => data,
        }, kwargs);
        this.onMessageListeners = new Set();
        this.onConnectedListeners = new Set();
        this.onDisconnectedListeners = new Set();
        this.retry_interval = null;
        this._socket_active = false;
        this._connect();
    }

    _connect() {
        if (this._socket_active) {return;}
        const socket = new this.WebSocket(this.url);
        socket.binaryType = 'arraybuffer';
        this._socket_active = true;

        const retry_connect = () => {
            if (!this.retry_interval) {
                this.retry_interval = setInterval(()=>this._connect(), this.disconnected_retry_interval_ms);
            }
        };

        socket.onopen = () => {
            if (this.retry_interval) {
                clearInterval(this.retry_interval);
                this.retry_interval = null;
            }
            this._send = (...msgs) => {for (const msg of msgs) {socket.send(this.encode(msg));}}
            this.onConnected();
        };
        socket.onclose = () => {
            socket.onclose = () => {};  // https://stackoverflow.com/a/4818541/3356840
            socket.close();
            this._socket_active = false;
            this._send = this._send_while_disconnected;
            this.onDisconnected();
            retry_connect();
        };
        socket.onmessage = (msg) => {
            this.onMessage(this.decode(msg.data));
        };

        retry_connect();
    }

    send(...args) {
        return this._send(...args);
    }
    _send(...args) {
        this.console.error('Send Failed: Socket has not been initalised', args);
    }
    _send_while_disconnected(...args) {
        this.console.warn('Send Failed: Currently disconnected', args);
    }

    addOnMessageListener(listener) {this.onMessageListeners.add(listener);}
    removeOnMessageListener(listener) {this.onMessageListeners.delete(listener);}
    onMessage(msg) {
        for (const listener of this.onMessageListeners) {
            listener(msg);
        }
    }

    addOnConnectedListener(listener) {this.onConnectedListeners.add(listener);}
    removeOnConnectedListener(listener) {this.onConnectedListeners.delete(listener);}
    onConnected() {
        for (const listener of this.onConnectedListeners) {
            listener();
        }
    }

    addOnDisconnectedListener(listener) {this.onDisconnectedListeners.add(listener);}
    removeOnDisconnectedListener(listener) {this.onDisconnectedListeners.delete(listener);}
    onDisconnected() {
        for (const listener of this.onDisconnectedListeners) {
            listener();
        }
    }
}



// trigger Subscription system -------------------------------------------------

export class SubscriptionSocketReconnect {
    constructor(kwargs) {
        kwargs = kwargs || {};
        Object.assign(this, {
            'subscriptions': new Set(),
        }, kwargs);
        Object.assign(kwargs, {
            'encode': encode,
            'decode': decode,
        }, kwargs);
        this.socket = new SocketReconnect(kwargs);
        this.socket.addOnConnectedListener(this.onConnected.bind(this));
        this.socket.addOnMessageListener(this.onMessage.bind(this));

        this.onMessageListeners = new Set();
    }

    onConnected() {
        if (this.subscriptions.size || this.subscriptions.length) {
            this.sendSubscriptions();
        }
    }

    addOnMessageListener(listener) {this.onMessageListeners.add(listener);}
    removeOnMessageListener(listener) {this.onMessageListeners.delete(listener);}
    onMessage(msg) {
        if (msg && msg.action == 'message' && msg.data.length > 0) {
            for (const m of msg.data) {
                for (const listener of this.onMessageListeners) {
                    listener(m);
                }
            }
        }
    }

    _sendPayload(action, data) {
        if (!Array.isArray(data)) {data = [data];}
        this.socket.send({action: action, data: data});
    }

    addSubscriptions(subscriptions) {
        for (let subscription of subscriptions) {
            this.subscriptions.add(subscription);
        }
        this.sendSubscriptions();
    }

    sendSubscriptions(subscriptions) {
        if (subscriptions != undefined) {
            this.subscriptions = new Set(subscriptions);
        }
        this._sendPayload('subscribe', Array.from(this.subscriptions));
    }

    sendMessages(...msgs) {
        this._sendPayload('message', Array.from(msgs));
    }

}
