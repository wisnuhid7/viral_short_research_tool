import { spawn } from 'child_process';
import { randomUUID } from 'crypto';

export interface WhopBountyPoster {
  id?: string;
  name?: string;
  username?: string;
}

export interface WhopHostingAccount {
  id?: string;
  title?: string;
  route?: string;
  logo_url?: string;
}

export interface WhopBounty {
  id: string;
  title: string;
  description: string;
  status: string;
  currency?: string;
  gross_reward_amount?: number;
  net_reward_amount?: number;
  budget_amount?: number;
  gross_paid_out_amount?: number;
  spots_remaining?: number | null;
  business_goal_type?: string | null;
  accepted_deliverable_types?: string[];
  allowed_country_codes?: string[];
  submissions_closed_at?: string | null;
  poster?: WhopBountyPoster;
  hosting_account?: WhopHostingAccount;
  created_at?: string;
  updated_at?: string;
}

interface BountiesListResponse {
  data: WhopBounty[];
  page_info?: {
    has_next_page?: boolean;
    start_cursor?: string;
    end_cursor?: string;
  };
}

/**
 * Executes a call to the Whop MCP Server via stdio proxy (mcp-remote)
 */
export async function fetchWhopBountiesFromMcp(first: number = 50): Promise<WhopBounty[]> {
  return new Promise((resolve, reject) => {
    const timeoutMs = 30000;
    const intentId = randomUUID();
    let isFinished = false;

    const child = spawn('npx', ['-y', 'mcp-remote', 'https://mcp.whop.com/mcp'], {
      stdio: ['pipe', 'pipe', 'pipe'],
    });

    const timer = setTimeout(() => {
      if (!isFinished) {
        isFinished = true;
        child.kill();
        reject(new Error(`Timeout (${timeoutMs}ms) saat menyinkronkan data dengan Whop MCP server`));
      }
    }, timeoutMs);

    let buffer = '';

    child.stdout.on('data', (chunk: Buffer) => {
      buffer += chunk.toString();
      const lines = buffer.split('\n');
      buffer = lines.pop() ?? '';

      for (const line of lines) {
        if (!line.trim()) continue;
        try {
          const msg = JSON.parse(line);

          // 1. Handshake: initialized
          if (msg.id === 1) {
            const callPayload = {
              jsonrpc: '2.0',
              id: 2,
              method: 'tools/call',
              params: {
                name: 'bounties_list',
                arguments: {
                  status: 'open',
                  first,
                  intent: 'Sinkronisasi campaign Whop Content Rewards',
                  intent_id: intentId,
                },
              },
            };
            child.stdin.write(JSON.stringify(callPayload) + '\n');
          }
          // 2. Result of tools/call
          else if (msg.id === 2) {
            clearTimeout(timer);
            isFinished = true;
            child.kill();

            if (msg.error) {
              reject(new Error(`Whop MCP RPC Error: ${msg.error.message || JSON.stringify(msg.error)}`));
              return;
            }

            if (!msg.result?.content?.[0]?.text) {
              reject(new Error('Format balasan dari Whop MCP tidak sesuai harapan (kosong).'));
              return;
            }

            try {
              const parsed: BountiesListResponse = JSON.parse(msg.result.content[0].text);
              resolve(parsed.data || []);
            } catch (jsonErr) {
              reject(new Error(`Gagal mem-parse JSON hasil bounties Whop: ${jsonErr}`));
            }
          }
        } catch {
          // Ignore non-JSON lines (e.g. logging)
        }
      }
    });

    child.stderr.on('data', () => {
      // Diagnostic stderr - keep silent unless debug
    });

    child.on('error', (err) => {
      if (!isFinished) {
        clearTimeout(timer);
        isFinished = true;
        reject(new Error(`Gagal menjalankan proses Whop MCP proxy: ${err.message}`));
      }
    });

    child.on('exit', (code) => {
      if (!isFinished) {
        clearTimeout(timer);
        isFinished = true;
        if (code !== 0) {
          reject(new Error(`Whop MCP proxy exited with code ${code}`));
        }
      }
    });

    // Send initialize request
    const initReq = {
      jsonrpc: '2.0',
      id: 1,
      method: 'initialize',
      params: {
        protocolVersion: '2024-11-05',
        capabilities: {},
        clientInfo: { name: 'viral-short-research-sync', version: '1.0.0' },
      },
    };

    child.stdin.write(JSON.stringify(initReq) + '\n');
  });
}
