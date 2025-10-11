#!/usr/bin/env python3
"""
Create Context Document in Production Database

Creates a system specifications document marked as context file.
Based on V1.5_MASTER_REFERENCE.md specifications.
"""
import psycopg2
import os
import sys

CONTEXT_CONTENT = """# CommandCenter System Specifications

## Hardware Configuration

### Inverter
**SolArk 15K Hybrid Inverter**
- Model: 15K-2P-N
- Continuous Power: 15,000W (15kW)
- Surge Power: 20,000W (20kW)
- Type: Hybrid inverter/charger with built-in solar MPPT
- Location: http://192.168.1.23 (local network)

### Battery Bank
**48V LiFePO4 (Lithium Iron Phosphate)**
- Total Capacity: 48 kWh
- Nominal Voltage: 51.2V (48V system)
- Chemistry: LiFePO4 (safer, longer life than Li-ion)
- Configuration: Custom bank with BMS
- Operating Range: 40V - 58.4V

### Solar Array
**14.6 kW Photovoltaic System**
- Total Capacity: 14.6 kW DC
- Panel Count: 36 panels
- Panel Wattage: 405W each
- Configuration: Optimized for SolArk MPPT input
- Orientation: South-facing (optimal)

### Bitcoin Mining Equipment
**Antminer S19 Fleet**
- Miner Count: 5 units
- Model: Antminer S19
- Power per Unit: 3,250W (3.25kW)
- Total Fleet Power: 16,250W (16.25kW)
- Control Method: Shelly Plug S smart outlets

## System Capabilities

### Monitoring Capabilities
- Real-time battery State of Charge (SOC) monitoring
- Real-time solar production (PV power) tracking
- Real-time load consumption measurement
- Grid import/export tracking
- Historical data analysis via PostgreSQL + TimescaleDB

### Control Capabilities
- Bitcoin miner on/off control (via Shelly smart plugs)
- Energy planning and optimization recommendations
- Battery charge/discharge monitoring

### Limitations (What System CANNOT Do)
- CANNOT control SolArk inverter settings (read-only API access)
- CANNOT modify battery charge parameters (managed by SolArk BMS)
- CANNOT control individual household appliances (except miners via Shelly)
- CANNOT access real-time weather data (future enhancement)
- CANNOT modify grid import/export settings

## Operating Policies

### Battery Management Policies
- **Critical Minimum SOC:** 30% (NEVER go below this threshold)
- **Safe Minimum SOC:** 40% (recommended operating floor)
- **Safe Maximum SOC:** 80% (daily cycling ceiling for battery longevity)
- **Absolute Maximum:** 100% (occasional full charge is acceptable)

**Rationale:** These thresholds protect battery health and ensure emergency reserve.

### Grid Usage Policy
- **Primary Policy:** Minimize grid import
- **Grid Import:** Only when battery < 40% SOC AND no solar production
- **Grid Export:** Acceptable when battery full (100%) AND excess solar
- **Emergency Mode:** Import from grid only in critical situations (battery < 30%)

### Bitcoin Miner Operation Policy
- **Priority:** Run only with excess solar power
- **Minimum Battery SOC for Operation:** 50%
- **Scheduling:** Optimize for peak solar production hours
- **Load Management:** Miners are first loads shed when battery drops below 50%

**Rationale:** Miners are flexible loads that maximize use of free solar energy.

## System Location and Context
- **Installation:** Wildfire Ranch (off-grid residential)
- **System Type:** Solar + battery + grid backup hybrid
- **Primary Goal:** Energy independence with Bitcoin mining using excess solar
- **Secondary Goal:** Minimize operating costs and maximize solar utilization

## API and Integration Details
- **Backend API:** https://api.wildfireranch.us (FastAPI + CrewAI agents)
- **Dashboard:** https://dashboard.wildfireranch.us (Streamlit multi-page app)
- **Database:** Railway PostgreSQL 15 + pgvector + TimescaleDB
- **Deployment:** Railway (auto-deploy from GitHub main branch)
"""

def main():
    try:
        conn = psycopg2.connect(os.environ['DATABASE_URL'])
        cur = conn.cursor()

        print("=" * 70)
        print("CREATE CONTEXT DOCUMENT")
        print("=" * 70)

        # Check if document already exists
        cur.execute("""
        SELECT id FROM kb_documents
        WHERE title = 'CommandCenter System Specifications'
        AND is_context_file = TRUE
        """)

        existing = cur.fetchone()
        if existing:
            print(f"\n⚠️  Document already exists (ID: {existing[0]})")
            print("Updating content...")

            cur.execute("""
            UPDATE kb_documents
            SET full_content = %s,
                token_count = %s,
                last_synced = NOW(),
                updated_at = NOW()
            WHERE id = %s
            """, (CONTEXT_CONTENT, len(CONTEXT_CONTENT.split()), existing[0]))

            print(f"✅ Updated existing document (ID: {existing[0]})")

        else:
            print("\nCreating new context document...")

            cur.execute("""
            INSERT INTO kb_documents (
                title, full_content, is_context_file,
                folder, folder_path, mime_type, token_count, last_synced
            )
            VALUES (%s, %s, TRUE, 'CONTEXT', '/CONTEXT/', 'text/plain', %s, NOW())
            RETURNING id
            """, ("CommandCenter System Specifications", CONTEXT_CONTENT, len(CONTEXT_CONTENT.split())))

            doc_id = cur.fetchone()[0]
            print(f"✅ Created new context document (ID: {doc_id})")

        conn.commit()

        # Verify
        cur.execute("""
        SELECT COUNT(*) FROM kb_documents WHERE is_context_file = TRUE
        """)
        count = cur.fetchone()[0]
        print(f"\n📊 Total context files in database: {count}")

        cur.close()
        conn.close()

        return 0

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())
