import {SocketReconnect, JsonSocketReconnect, SubscriptionSocketReconnect} from 'src/socket/websocket';


const DISCONNECTED_RETRY_INTERVAL_MS = 1000;

const MockWebSocketManager = ()=>{
    let mockSocket;
    let mockSocket_callCount;

    class MockWebSocket {
        constructor() {
            //expect(mockSocket).toBe(undefined);  // We only ever want one socket connected under test conditions
            mockSocket = jasmine.createSpyObj('WebSocket', ['send', 'onopen', 'onclose', 'onmessage', 'close']);
            mockSocket_callCount++;
            return mockSocket;
        }
    }

    const setup = (SocketClass, kwargs={})=>{
        expect(mockSocket).toBe(undefined);
        mockSocket_callCount = 0;
        jasmine.clock().install();
        const socket = new SocketClass(Object.assign({
            WebSocket: MockWebSocket,
            disconnected_retry_interval_ms: DISCONNECTED_RETRY_INTERVAL_MS,
        }, kwargs));
        expect(mockSocket).not.toBe(undefined);
        spyOn(socket, 'onConnected').and.callThrough();
        spyOn(socket, 'onDisconnected').and.callThrough();
        spyOn(socket, 'onMessage'); // TODO: and.callThrough(); to allow testing of onMessage routing to listeners
        spyOn(socket, 'decodeMessages').and.callThrough();
        spyOn(socket, 'encodeMessages').and.callThrough();
        spyOn(socket, 'addOnMessageListener').and.callThrough();
        spyOn(socket, 'removeOnMessageListener').and.callThrough();
        return socket;
    };

    const teardown = ()=>{
        mockSocket = undefined;
        jasmine.clock().uninstall();
    };

    return {
        setup: setup,
        teardown: teardown,
        getMockSocket: ()=>mockSocket,
        getMockSocket_callCount: ()=>mockSocket_callCount,
    };
};


describe('SocketReconnect', function() {
    const mockSocketManager = MockWebSocketManager();
    const mockSocket = ()=>mockSocketManager.getMockSocket();
    const expectMockSocketCallCount = (count)=>expect(mockSocketManager.getMockSocket_callCount()).toBe(count);

    let socket;

    beforeEach(function() {
        socket = mockSocketManager.setup(SocketReconnect, {});
    });

    afterEach(function() {
        mockSocketManager.teardown();
        socket = undefined;
    });

    it('Should call onConnected on creation/connection',()=>{
        expect(socket.onConnected).not.toHaveBeenCalled();
        mockSocket().onopen();
        expect(socket.onConnected).toHaveBeenCalled();
    });

    it('Should call onMessage when a message is received/decoded',()=>{
        mockSocket().onopen();
        expect(socket.onMessage).not.toHaveBeenCalled();
        mockSocket().onmessage({data: 'Hello World\n'});
        expect(socket.decodeMessages).toHaveBeenCalled();
        expect(socket.onMessage).toHaveBeenCalledWith('Hello World');
    });

    it('Should call send when a message is sent (but not when disconnected)',()=>{
        expect(mockSocket().send).not.toHaveBeenCalled();
        socket.send('Hello World');
        expect(mockSocket().send).not.toHaveBeenCalled();
        mockSocket().onopen();
        socket.send('Hello World');
        expect(mockSocket().send).toHaveBeenCalledWith('Hello World\n');
        mockSocket().onclose();
        mockSocket().send.calls.reset();
        socket.send('Hello Again');
        expect(mockSocket().send).not.toHaveBeenCalled();
    });

    it('Should attempt to reconnect when disconnected',()=>{
        mockSocket().onopen();
        expect(socket.onDisconnected).not.toHaveBeenCalled();
        mockSocket().onclose();
        expect(socket.onDisconnected).toHaveBeenCalled();
        let previous_mockSocket = mockSocket();
        jasmine.clock().tick(DISCONNECTED_RETRY_INTERVAL_MS - 1);
        expect(mockSocket()).toBe(previous_mockSocket);
        expectMockSocketCallCount(1);
        jasmine.clock().tick(2);
        expectMockSocketCallCount(2);
        expect(mockSocket()).not.toBe(previous_mockSocket);
        jasmine.clock().tick(DISCONNECTED_RETRY_INTERVAL_MS);
        expectMockSocketCallCount(3);
        mockSocket().onopen();
        jasmine.clock().tick(DISCONNECTED_RETRY_INTERVAL_MS);
        expectMockSocketCallCount(3);
        jasmine.clock().tick(DISCONNECTED_RETRY_INTERVAL_MS);
        expectMockSocketCallCount(3);
    });

    it('Should attempt to reconnect even if first connection fails',()=>{
        expect(socket.onConnected).not.toHaveBeenCalled();
        expectMockSocketCallCount(1);
        jasmine.clock().tick(DISCONNECTED_RETRY_INTERVAL_MS + 1);
        expectMockSocketCallCount(2);
        jasmine.clock().tick(DISCONNECTED_RETRY_INTERVAL_MS + 1);
        expectMockSocketCallCount(3);
        mockSocket().onopen();
        expect(socket.onConnected).toHaveBeenCalled();
        jasmine.clock().tick(DISCONNECTED_RETRY_INTERVAL_MS + 1);
        expectMockSocketCallCount(3);
    });

    // TODO: Test addOnMessageListener/removeOnMessageListener
});



describe('JsonSocketReconnect', function() {
    const mockSocketManager = MockWebSocketManager();
    const mockSocket = ()=>mockSocketManager.getMockSocket();
    const expectMockSocketCallCount = (count)=>expect(mockSocketManager.getMockSocket_callCount()).toBe(count);

    let socket;

    beforeEach(function() {
        socket = mockSocketManager.setup(JsonSocketReconnect, {});
    });

    afterEach(function() {
        mockSocketManager.teardown();
        socket = undefined;
    });

    it('Should send json',()=>{
        mockSocket().onopen();
        socket.send({'Hello Json World': 1});
        expect(mockSocket().send).toHaveBeenCalledWith('{"Hello Json World":1}\n');
    });

    it('Should recieve json',()=>{
        mockSocket().onopen();
        mockSocket().onmessage({data: '{"Hello Json World":2}\n'});
        expect(socket.onMessage).toHaveBeenCalledWith({'Hello Json World': 2});
    });

    it('Should split mutiple messages and call onMessage mutiple times', ()=>{
        mockSocket().onopen();
        mockSocket().onmessage({data: '{"a":1}\n{"b":2}\n'});
        expect(socket.onMessage.calls.argsFor(0)).toEqual([{a:1}]);
        expect(socket.onMessage.calls.argsFor(1)).toEqual([{b:2}]);
    });

});


describe('SubscriptionSocketReconnect', function() {
    const mockSocketManager = MockWebSocketManager();
    const mockSocket = ()=>mockSocketManager.getMockSocket();

    let socket;

    beforeEach(function() {
        socket = mockSocketManager.setup(SubscriptionSocketReconnect, {
            subscriptions: ['subscription1', 'subscription2'],
        });
    });

    afterEach(function() {
        mockSocketManager.teardown();
        socket = undefined;
    });

    it('Should subscribe on connect/reconnect',()=>{
        expect(mockSocket().send).not.toHaveBeenCalled();
        mockSocket().onopen();
        expect(mockSocket().send).toHaveBeenCalledWith(JSON.stringify({
            action: 'subscribe', data: ['subscription1', 'subscription2'],
        })+'\n');
        mockSocket().onclose();
        mockSocket().send.calls.reset();
        mockSocket().onopen();
        expect(mockSocket().send).toHaveBeenCalledWith(JSON.stringify({
            action: 'subscribe', data: ['subscription1', 'subscription2'],
        })+'\n');
    });

    it('Should split message payloads and call onMessage',()=>{
        mockSocket().onopen();
        mockSocket().onmessage({data: JSON.stringify({
            action: 'message', data: [{a:1},{b:2}],
        })+'\n'});
        expect(socket.onMessage.calls.argsFor(0)).toEqual([{a:1}]);
        expect(socket.onMessage.calls.argsFor(1)).toEqual([{b:2}]);
    });

    it('Should encode message payloads',()=>{
        mockSocket().onopen();
        mockSocket().send.calls.reset();
        socket.sendMessages({a:1},{b:2});
        expect(mockSocket().send).toHaveBeenCalledWith(JSON.stringify({
            action: 'message', data: [{a:1}, {b:2}],
        })+'\n');
    });

    it('Should update subscriptions',()=>{
        mockSocket().onopen();
        mockSocket().send.calls.reset();
        socket.sendSubscriptions(new Set(['a']));
        expect(mockSocket().send).toHaveBeenCalledWith(JSON.stringify({
            action: 'subscribe', data: ['a'],
        })+'\n');
    });
});