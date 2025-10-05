/**
 * Quick test script to verify MCP server setup
 */

import axios from 'axios';

const RAILWAY_API_URL = process.env.RAILWAY_API_URL || 'https://api.wildfireranch.us';

async function testRailwayAPI() {
  console.log('Testing Railway API connection...\n');

  try {
    // Test 1: Health check
    console.log('1. Testing /health endpoint...');
    const health = await axios.get(`${RAILWAY_API_URL}/health`);
    console.log('✅ Health:', health.data.status);
    console.log('   Database:', health.data.checks.database_connected ? '✅' : '❌');
    console.log('   OpenAI:', health.data.checks.openai_configured ? '✅' : '❌');
    console.log('');

    // Test 2: Latest energy data
    console.log('2. Testing /energy/latest endpoint...');
    const energy = await axios.get(`${RAILWAY_API_URL}/energy/latest`);
    console.log('✅ Energy data:', energy.data.status);
    if (energy.data.data) {
      const data = energy.data.data;
      console.log(`   Battery: ${data.battery_soc || 'N/A'}%`);
      console.log(`   Solar: ${data.pv_power || 'N/A'}W`);
    }
    console.log('');

    // Test 3: List conversations
    console.log('3. Testing /conversations endpoint...');
    const convs = await axios.get(`${RAILWAY_API_URL}/conversations?limit=3`);
    console.log('✅ Conversations:', convs.data.count);
    console.log('');

    console.log('🎉 All tests passed! MCP server can connect to Railway API.');

  } catch (error) {
    if (error.response) {
      console.error('❌ API Error:', error.response.status, error.response.data);
    } else if (error.request) {
      console.error('❌ Network Error: Could not reach', RAILWAY_API_URL);
    } else {
      console.error('❌ Error:', error.message);
    }
    process.exit(1);
  }
}

testRailwayAPI();
