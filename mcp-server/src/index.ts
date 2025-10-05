#!/usr/bin/env node

/**
 * CommandCenter MCP Server
 *
 * Exposes CommandCenter agent capabilities via Model Context Protocol.
 * Allows Claude Desktop to interact with your energy management system.
 */

import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import {
  CallToolRequestSchema,
  ListToolsRequestSchema,
  ListResourcesRequestSchema,
  ReadResourceRequestSchema,
} from "@modelcontextprotocol/sdk/types.js";
import axios from "axios";
import { z } from "zod";

// Configuration
const RAILWAY_API_URL = process.env.RAILWAY_API_URL || "https://api.wildfireranch.us";
const API_KEY = process.env.API_KEY || "";

// Axios instance with API key
const api = axios.create({
  baseURL: RAILWAY_API_URL,
  headers: {
    "Content-Type": "application/json",
    ...(API_KEY && { "x-api-key": API_KEY }),
  },
});

// ============================================================================
// Tool Schemas
// ============================================================================

const AskAgentSchema = z.object({
  message: z.string().describe("Question or command to send to the Solar Controller agent"),
  session_id: z.string().optional().describe("Optional session ID for multi-turn conversations"),
});

const GetEnergyDataSchema = z.object({
  type: z.enum(["latest", "recent", "stats"]).describe("Type of energy data to retrieve"),
  hours: z.number().optional().describe("Number of hours to look back (for recent/stats)"),
  limit: z.number().optional().describe("Maximum number of records (for recent)"),
});

const GetConversationSchema = z.object({
  conversation_id: z.string().optional().describe("Conversation ID to retrieve (omit to list recent)"),
  limit: z.number().optional().describe("Number of conversations to list (default: 10)"),
});

// ============================================================================
// MCP Server Setup
// ============================================================================

const server = new Server(
  {
    name: "commandcenter",
    version: "1.0.0",
  },
  {
    capabilities: {
      tools: {},
      resources: {},
    },
  }
);

// ============================================================================
// Tools Implementation
// ============================================================================

server.setRequestHandler(ListToolsRequestSchema, async () => {
  return {
    tools: [
      {
        name: "ask_agent",
        description: "Ask the Solar Controller agent a question about your energy system. Handles multi-turn conversations with memory.",
        inputSchema: {
          type: "object",
          properties: {
            message: {
              type: "string",
              description: "Question or command to send to the agent",
            },
            session_id: {
              type: "string",
              description: "Optional session ID for continuing a conversation",
            },
          },
          required: ["message"],
        },
      },
      {
        name: "get_energy_data",
        description: "Retrieve energy system data (latest snapshot, recent data, or statistics)",
        inputSchema: {
          type: "object",
          properties: {
            type: {
              type: "string",
              enum: ["latest", "recent", "stats"],
              description: "Type of data to retrieve",
            },
            hours: {
              type: "number",
              description: "Hours to look back (for recent/stats)",
            },
            limit: {
              type: "number",
              description: "Maximum records (for recent)",
            },
          },
          required: ["type"],
        },
      },
      {
        name: "get_conversations",
        description: "List recent conversations or get a specific conversation with all messages",
        inputSchema: {
          type: "object",
          properties: {
            conversation_id: {
              type: "string",
              description: "Specific conversation ID to retrieve (omit to list recent)",
            },
            limit: {
              type: "number",
              description: "Number of conversations to list (default: 10)",
            },
          },
        },
      },
    ],
  };
});

server.setRequestHandler(CallToolRequestSchema, async (request) => {
  const { name, arguments: args } = request.params;

  try {
    switch (name) {
      case "ask_agent": {
        const validated = AskAgentSchema.parse(args);
        const response = await api.post("/ask", {
          message: validated.message,
          session_id: validated.session_id,
        });

        return {
          content: [
            {
              type: "text",
              text: JSON.stringify(response.data, null, 2),
            },
          ],
        };
      }

      case "get_energy_data": {
        const validated = GetEnergyDataSchema.parse(args);
        let endpoint = "";
        let params: Record<string, any> = {};

        switch (validated.type) {
          case "latest":
            endpoint = "/energy/latest";
            break;
          case "recent":
            endpoint = "/energy/recent";
            if (validated.hours) params.hours = validated.hours;
            if (validated.limit) params.limit = validated.limit;
            break;
          case "stats":
            endpoint = "/energy/stats";
            if (validated.hours) params.hours = validated.hours;
            break;
        }

        const response = await api.get(endpoint, { params });

        return {
          content: [
            {
              type: "text",
              text: JSON.stringify(response.data, null, 2),
            },
          ],
        };
      }

      case "get_conversations": {
        const validated = GetConversationSchema.parse(args);

        if (validated.conversation_id) {
          // Get specific conversation
          const response = await api.get(`/conversations/${validated.conversation_id}`);
          return {
            content: [
              {
                type: "text",
                text: JSON.stringify(response.data, null, 2),
              },
            ],
          };
        } else {
          // List recent conversations
          const response = await api.get("/conversations", {
            params: { limit: validated.limit || 10 },
          });
          return {
            content: [
              {
                type: "text",
                text: JSON.stringify(response.data, null, 2),
              },
            ],
          };
        }
      }

      default:
        throw new Error(`Unknown tool: ${name}`);
    }
  } catch (error) {
    if (axios.isAxiosError(error)) {
      throw new Error(
        `API request failed: ${error.response?.data?.detail || error.message}`
      );
    }
    throw error;
  }
});

// ============================================================================
// Resources Implementation
// ============================================================================

server.setRequestHandler(ListResourcesRequestSchema, async () => {
  return {
    resources: [
      {
        uri: "commandcenter://energy/latest",
        name: "Latest Energy Data",
        description: "Most recent energy system snapshot",
        mimeType: "application/json",
      },
      {
        uri: "commandcenter://health",
        name: "System Health",
        description: "CommandCenter API health status",
        mimeType: "application/json",
      },
    ],
  };
});

server.setRequestHandler(ReadResourceRequestSchema, async (request) => {
  const uri = request.params.uri;

  try {
    if (uri === "commandcenter://energy/latest") {
      const response = await api.get("/energy/latest");
      return {
        contents: [
          {
            uri,
            mimeType: "application/json",
            text: JSON.stringify(response.data, null, 2),
          },
        ],
      };
    }

    if (uri === "commandcenter://health") {
      const response = await api.get("/health");
      return {
        contents: [
          {
            uri,
            mimeType: "application/json",
            text: JSON.stringify(response.data, null, 2),
          },
        ],
      };
    }

    throw new Error(`Unknown resource: ${uri}`);
  } catch (error) {
    if (axios.isAxiosError(error)) {
      throw new Error(
        `Failed to fetch resource: ${error.response?.data?.detail || error.message}`
      );
    }
    throw error;
  }
});

// ============================================================================
// Server Startup
// ============================================================================

async function main() {
  const transport = new StdioServerTransport();
  await server.connect(transport);

  // Log to stderr (stdout is used for MCP protocol)
  console.error("CommandCenter MCP Server running on stdio");
}

main().catch((error) => {
  console.error("Server error:", error);
  process.exit(1);
});
