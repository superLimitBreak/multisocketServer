//import 'core-js/fn/object/assign';


// Text Websocket + Auto-Reconnect ---------------------------------------------

export class SocketReconnect {

    constructor(kwargs) {
        Object.assign(this, {
            WebSocket: WebSocket,
            hostname: location.hostname,
            port: 9873,
            disconnected_retry_interval_ms: 5000,
            console: console,
        }, kwargs);
        this.onMessageListeners = new Set();
        this.retry_interval = null;
        this._socket_active = false;
        this._connect();
    }

    _connect() {
        if (this._socket_active) {return;}
        const socket = new this.WebSocket(`ws://${this.hostname}:${this.port}/`);
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
            this._send = (...args) => socket.send(this.encodeMessages(args));
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
            //AbstractSocketReconnect.prototype.onMessage.call(this, msg.data);
            for (let m of this.decodeMessages(msg.data)) {
                this.onMessage(m);
            }
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

    encodeMessages(msgs) {
        return msgs.join('\n')+'\n';
    }
    decodeMessages(msgs) {
        return msgs.split('\n').filter((x)=>{return x});
    }

    // Overrideable Methods -------
    onMessage(msg) {
        for (let listener of this.onMessageListeners) {
            listener(msg);
        }
    }
    onConnected() {}  //this.console.log('onConnected');
    onDisconnected() {}  //this.console.log('onDisconnected');

    addOnMessageListener(listener) {
        this.onMessageListeners.add(listener);
    }
    removeOnMessageListener(listener) {
        this.onMessageListeners.delete(listener);
    }
}


// Json ------------------------------------------------------------------------

export class JsonSocketReconnect extends SocketReconnect {
    encodeMessages(msgs) {
        return super.encodeMessages(msgs.map(JSON.stringify));
    }
    decodeMessages(msgs) {
        return super.decodeMessages(msgs).map(JSON.parse);
    }
}


// trigger Subscription system -------------------------------------------------

export class SubscriptionSocketReconnect extends JsonSocketReconnect {
    constructor(kwargs) {
        super(kwargs);
        Object.assign(this, {
            subscriptions: new Set(),
        }, kwargs);
    }

    decodeMessages(msgs) {
        return super.decodeMessages(msgs).reduce((accumulator, msg) => {
            if (msg && msg.action == 'message' && msg.data.length > 0) {
                accumulator = accumulator.concat(msg.data);
            }
            return accumulator;
        }, []);
    }

    onConnected() {
        if (this.subscriptions.size || this.subscriptions.length) {
            this.sendSubscriptions();
        }
    }

    _sendPayload(action, data) {
        if (!Array.isArray(data)) {data = [data];}
        this.send({action: action, data: data});
    }

    addSubscriptions(subscriptions) {
        // TODO: use set intersection
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
