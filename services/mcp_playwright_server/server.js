const { Server } = require('@modelcontextprotocol/sdk/server/index.js');
const { StdioServerTransport } = require('@modelcontextprotocol/sdk/server/stdio.js');
const { chromium } = require('playwright');

class PlaywrightMCPServer {
  constructor() {
    this.server = new Server(
      {
        name: 'playwright-server',
        version: '1.0.0',
      },
      {
        capabilities: {
          tools: {},
        },
      }
    );

    this.browser = null;
    this.page = null;

    this.setupTools();
  }

  setupTools() {
    // Navigate tool
    this.server.setRequestHandler('tools/call', async (request) => {
      const { name, arguments: args } = request.params;

      switch (name) {
        case 'browser_navigate':
          return await this.navigate(args.url);
        case 'browser_click':
          return await this.click(args.selector);
        case 'browser_fill':
          return await this.fill(args.selector, args.text);
        case 'browser_screenshot':
          return await this.screenshot(args.path);
        case 'browser_evaluate':
          return await this.evaluate(args.script);
        case 'browser_wait':
          return await this.waitFor(args.selector);
        default:
          throw new Error(`Unknown tool: ${name}`);
      }
    });

    this.server.setRequestHandler('tools/list', async () => {
      return {
        tools: [
          {
            name: 'browser_navigate',
            description: 'Navigate browser to URL',
            inputSchema: {
              type: 'object',
              properties: {
                url: { type: 'string', description: 'URL to navigate to' }
              },
              required: ['url']
            }
          },
          {
            name: 'browser_click',
            description: 'Click element by selector',
            inputSchema: {
              type: 'object',
              properties: {
                selector: { type: 'string', description: 'CSS selector' }
              },
              required: ['selector']
            }
          },
          {
            name: 'browser_fill',
            description: 'Fill input field',
            inputSchema: {
              type: 'object',
              properties: {
                selector: { type: 'string', description: 'CSS selector' },
                text: { type: 'string', description: 'Text to fill' }
              },
              required: ['selector', 'text']
            }
          },
          {
            name: 'browser_screenshot',
            description: 'Take page screenshot',
            inputSchema: {
              type: 'object',
              properties: {
                path: { type: 'string', description: 'Save path' }
              }
            }
          },
          {
            name: 'browser_evaluate',
            description: 'Execute JavaScript',
            inputSchema: {
              type: 'object',
              properties: {
                script: { type: 'string', description: 'JavaScript code' }
              },
              required: ['script']
            }
          },
          {
            name: 'browser_wait',
            description: 'Wait for element',
            inputSchema: {
              type: 'object',
              properties: {
                selector: { type: 'string', description: 'CSS selector' }
              },
              required: ['selector']
            }
          }
        ]
      };
    });
  }

  async ensurePage() {
    if (!this.browser) {
      this.browser = await chromium.launch({ headless: true });
    }
    if (!this.page) {
      this.page = await this.browser.newPage();
    }
  }

  async navigate(url) {
    await this.ensurePage();
    await this.page.goto(url);
    return { content: [{ type: 'text', text: `Navigated to ${url}` }] };
  }

  async click(selector) {
    await this.ensurePage();
    await this.page.click(selector);
    return { content: [{ type: 'text', text: `Clicked ${selector}` }] };
  }

  async fill(selector, text) {
    await this.ensurePage();
    await this.page.fill(selector, text);
    return { content: [{ type: 'text', text: `Filled ${selector} with "${text}"` }] };
  }

  async screenshot(path = '/tmp/screenshot.png') {
    await this.ensurePage();
    await this.page.screenshot({ path });
    return { content: [{ type: 'text', text: `Screenshot saved to ${path}` }] };
  }

  async evaluate(script) {
    await this.ensurePage();
    const result = await this.page.evaluate(script);
    return { content: [{ type: 'text', text: `Result: ${JSON.stringify(result)}` }] };
  }

  async waitFor(selector) {
    await this.ensurePage();
    await this.page.waitForSelector(selector);
    return { content: [{ type: 'text', text: `Found element: ${selector}` }] };
  }

  async run() {
    const transport = new StdioServerTransport();
    await this.server.connect(transport);
    console.error('Playwright MCP server running on stdio');
  }
}

const server = new PlaywrightMCPServer();
server.run().catch(console.error);
