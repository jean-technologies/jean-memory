import { JeanClient } from './index';

// Mock global fetch
const mockFetch = jest.fn();
global.fetch = mockFetch;

describe('JeanClient (Node.js SDK)', () => {

  beforeEach(() => {
    mockFetch.mockClear();
  });

  const mockApiKey = 'jean_sk_12345';
  const mockUserToken = 'header.' + btoa(JSON.stringify({ sub: 'user_123', email: 'test@example.com' })) + '.signature';
  const mockInvalidToken = 'invalid_token';

  it('should initialize without errors with a valid API key', () => {
    expect(() => new JeanClient({ apiKey: mockApiKey })).not.toThrow();
  });

  it('should throw an error if API key is missing or invalid', () => {
    expect(() => new JeanClient({ apiKey: '' })).toThrow('API key is required');
    expect(() => new JeanClient({ apiKey: 'invalid_key' })).toThrow('Invalid API key format');
  });

  describe('_getUserIdFromToken', () => {
    const client = new JeanClient({ apiKey: mockApiKey });
    
    it('should correctly extract user_id from a valid JWT', () => {
      expect((client as any)._getUserIdFromToken(mockUserToken)).toBe('user_123');
    });

    it('should return the token itself if it is not a valid JWT', () => {
      expect((client as any)._getUserIdFromToken(mockInvalidToken)).toBe('invalid_token');
    });

    it('should handle JWTs without a sub claim by falling back to the full token', () => {
        const noSubToken = 'header.' + btoa(JSON.stringify({ email: 'test@example.com' })) + '.signature';
        expect((client as any)._getUserIdFromToken(noSubToken)).toBe(noSubToken);
    });
  });

  describe('_makeMcpRequest', () => {
    it('should make a fetch call with the correct MCP payload and headers', async () => {
      const client = new JeanClient({ apiKey: mockApiKey });

      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({ result: { content: [{ text: 'response' }] } }),
      });

      await (client as any)._makeMcpRequest('user_123', 'test_tool', { arg1: 'value1' });

      expect(mockFetch).toHaveBeenCalledTimes(1);
      const [url, options] = mockFetch.mock.calls[0];
      
      expect(url).toBe('https://jean-memory-api-virginia.onrender.com/mcp/node-sdk/messages/user_123');
      expect(options.method).toBe('POST');
      expect(options.headers['X-API-Key']).toBe(mockApiKey);
      expect(options.headers['X-User-Id']).toBe('user_123');
      
      const body = JSON.parse(options.body);
      expect(body.jsonrpc).toBe('2.0');
      expect(body.method).toBe('tools/call');
      expect(body.params.name).toBe('test_tool');
      expect(body.params.arguments).toEqual({ arg1: 'value1' });
    });
  });
  
  describe('getContext', () => {
    it('should call _makeMcpRequest with the correct arguments for the jean_memory tool', async () => {
        const client = new JeanClient({ apiKey: mockApiKey });
        const makeRequestSpy = jest.spyOn(client as any, '_makeMcpRequest');
        makeRequestSpy.mockResolvedValue({ result: { content: [{ text: 'mock context' }] } });

        await client.getContext({
            user_token: mockUserToken,
            message: 'hello world',
        });

        expect(makeRequestSpy).toHaveBeenCalledWith('user_123', 'jean_memory', {
            user_message: 'hello world',
            is_new_conversation: false,
            needs_context: true,
            speed: 'balanced',
            format: 'enhanced'
        });
    });
  });

  describe('Tools', () => {
    it('tools.add_memory should call _makeMcpRequest with correct arguments', async () => {
        const client = new JeanClient({ apiKey: mockApiKey });
        const makeRequestSpy = jest.spyOn(client as any, '_makeMcpRequest');
        makeRequestSpy.mockResolvedValue({ result: { success: true } });

        await client.tools.add_memory({
            user_token: mockUserToken,
            content: 'new memory'
        });

        expect(makeRequestSpy).toHaveBeenCalledWith('user_123', 'add_memories', {
            text: 'new memory'
        });
    });

    it('tools.search_memory should call _makeMcpRequest with correct arguments', async () => {
        const client = new JeanClient({ apiKey: mockApiKey });
        const makeRequestSpy = jest.spyOn(client as any, '_makeMcpRequest');
        makeRequestSpy.mockResolvedValue({ result: { results: [] } });

        await client.tools.search_memory({
            user_token: mockUserToken,
            query: 'find memory'
        });

        expect(makeRequestSpy).toHaveBeenCalledWith('user_123', 'search_memory', {
            query: 'find memory',
            limit: 10
        });
    });
  });
});
