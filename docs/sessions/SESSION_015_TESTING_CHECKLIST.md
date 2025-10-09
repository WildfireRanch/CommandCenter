# Session 015 - Comprehensive Testing Checklist

**Date:** October 6, 2025
**Purpose:** Verify all components of CommandCenter Phase 4 integration
**Status:** In Progress

---

## Phase 1: Infrastructure Verification ✅

### Vercel Configuration
- [x] Add `NEXT_PUBLIC_STUDIO_URL=https://studio.wildfireranch.us` to Vercel
- [ ] Verify environment variable is set (check Vercel dashboard)
- [ ] Trigger new deployment
- [ ] Wait for deployment to complete
- [ ] Note deployment URL: __________________

### CrewAI Studio Accessibility
- [ ] Access https://studio.wildfireranch.us in browser
- [ ] Verify page loads (not just "JavaScript required" message)
- [ ] See CrewAI logo and interface
- [ ] No error messages visible
- [ ] Screenshot saved: __________________

### Railway Deployment Status
- [ ] Check Railway logs for CrewAI Studio service
- [ ] Look for: "You can now view your Streamlit app"
- [ ] No error messages in logs
- [ ] Service status: Healthy
- [ ] Screenshot of logs: __________________

---

## Phase 2: Frontend Integration Testing

### Studio Page Access
- [ ] Visit frontend URL: __________________ /studio
- [ ] Page loads without errors
- [ ] See "Operator Studio" heading
- [ ] Green "Studio Connected" banner visible
- [ ] Banner shows correct URL: https://studio.wildfireranch.us

### UI Components
- [ ] "Open in New Tab" button present
- [ ] "Fullscreen" button present
- [ ] Quick Guide info box displays correctly
- [ ] Iframe loads CrewAI Studio content

### Functionality Tests
- [ ] Click "Open in New Tab" - Studio opens in new tab
- [ ] Click "Fullscreen" - Goes fullscreen, see exit button
- [ ] Click "Exit Fullscreen" - Returns to normal view
- [ ] Iframe content is interactive (can click inside)

### Responsive Design
- [ ] Resize browser window - Studio adapts
- [ ] Iframe maintains aspect ratio
- [ ] Buttons remain accessible

---

## Phase 3: CrewAI Studio Interface Testing

### Navigation
- [ ] Left sidebar visible
- [ ] CrewAI logo displays
- [ ] All 8 pages listed:
  - [ ] Crews
  - [ ] Tools
  - [ ] Agents
  - [ ] Tasks
  - [ ] Knowledge
  - [ ] Kickoff!
  - [ ] Results
  - [ ] Import/export

### Page Loading
- [ ] Click each page, verify it loads:
  - [ ] Crews page loads
  - [ ] Tools page loads
  - [ ] Agents page loads
  - [ ] Tasks page loads
  - [ ] Knowledge page loads
  - [ ] Kickoff! page loads
  - [ ] Results page loads
  - [ ] Import/export page loads

---

## Phase 4: Tools Configuration

### Available Tools Check
- [ ] Navigate to Tools page
- [ ] See list of available tools
- [ ] Check boxes are interactive
- [ ] Enable following tools:
  - [ ] DuckDuckGoSearchTool
  - [ ] CustomFileWriteTool
  - [ ] CustomCodeInterpreterTool

### Tool Status
- [ ] Enabled tools show checkmark
- [ ] Tool descriptions visible
- [ ] No error messages
- [ ] Configuration saves (refresh page, still checked)

---

## Phase 5: Agent Creation Test

### Create First Agent
**Agent Name:** Solar Data Analyst

**Configuration:**
```
Role: Solar Energy Data Analyst
Goal: Analyze solar production data and identify optimization opportunities
Backstory: You are an experienced renewable energy analyst with expertise in
           solar panel performance optimization. You have a keen eye for
           patterns in energy data and provide actionable insights.
```

### Steps
- [ ] Navigate to Agents page
- [ ] Click "Create agent" button
- [ ] Agent creation form appears
- [ ] Fill in Role field
- [ ] Fill in Goal field
- [ ] Fill in Backstory field
- [ ] Select tools:
  - [ ] DuckDuckGoSearchTool
  - [ ] CustomCodeInterpreterTool
- [ ] Select LLM: GPT-3.5-turbo (cost-effective for testing)
- [ ] Set verbose: True (for debugging)
- [ ] Set allow_delegation: False
- [ ] Click Save button
- [ ] Agent appears in list
- [ ] Agent details display correctly

### Verification
- [ ] Refresh page
- [ ] Agent still appears (database persistence working)
- [ ] Click Edit on agent
- [ ] All fields retained correctly
- [ ] Tools still selected

---

## Phase 6: Task Creation Test

### Create First Task
**Task Name:** Analyze Solar Data

**Configuration:**
```
Description: Analyze solar production data from the past 30 days. Identify
            any anomalies, patterns, or performance issues. Consider factors
            like time of day, weather patterns, and seasonal variations.

Expected Output: A JSON report with:
                - summary: Brief overview of findings
                - anomalies: List of detected anomalies with dates and descriptions
                - recommendations: List of optimization suggestions
                - confidence_score: 0-100 rating of analysis confidence
```

### Steps
- [ ] Navigate to Tasks page
- [ ] Click "Create task" button
- [ ] Task creation form appears
- [ ] Fill in Description field
- [ ] Fill in Expected Output field
- [ ] Assign Agent: Solar Data Analyst
- [ ] Context: None (first task)
- [ ] Click Save button
- [ ] Task appears in list
- [ ] Task details display correctly

### Verification
- [ ] Refresh page
- [ ] Task still appears (database persistence working)
- [ ] Click Edit on task
- [ ] All fields retained correctly
- [ ] Agent assignment correct

---

## Phase 7: Crew Creation Test

### Create First Crew
**Crew Name:** Solar Analysis Crew

**Configuration:**
```
Name: Solar Analysis Crew
Description: Analyzes solar production data and provides optimization recommendations
Process: Sequential
```

### Steps
- [ ] Navigate to Crews page
- [ ] Click "Create crew" button
- [ ] Crew creation form appears
- [ ] Fill in Name field
- [ ] Fill in Description field
- [ ] Select Process Type: Sequential
- [ ] Add Agents:
  - [ ] Select Solar Data Analyst
- [ ] Add Tasks:
  - [ ] Select Analyze Solar Data
- [ ] Click Save button
- [ ] Crew appears in list
- [ ] Crew details display correctly

### Verification
- [ ] Refresh page
- [ ] Crew still appears (database persistence working)
- [ ] Click to expand crew
- [ ] Agents listed correctly
- [ ] Tasks listed correctly
- [ ] Process type shows Sequential

---

## Phase 8: Knowledge Base Test (Optional)

### Add Knowledge Source
- [ ] Navigate to Knowledge page
- [ ] Click "Add Knowledge Source" button
- [ ] Select type: Text
- [ ] Enter sample text about solar energy
- [ ] Add description
- [ ] Click Save
- [ ] Knowledge source appears in list
- [ ] Refresh page
- [ ] Knowledge source persists

---

## Phase 9: Crew Execution Test

### Run the Crew
- [ ] Navigate to Kickoff! page
- [ ] Select crew: Solar Analysis Crew
- [ ] Crew details display
- [ ] See "Kickoff Crew" button
- [ ] Click "Kickoff Crew"
- [ ] Execution begins
- [ ] Status updates appear
- [ ] Can see agent thoughts (verbose mode)
- [ ] Tool usage displayed (if any)

### Monitor Execution
- [ ] Task 1 starts: Analyze Solar Data
- [ ] Agent processes task
- [ ] No errors displayed
- [ ] Execution completes or shows progress
- [ ] Final result displays

**Note:** First execution may take 1-2 minutes. If it times out or errors, document the error message for debugging.

### Expected Behaviors
**If successful:**
- Status: "Completed"
- Output appears (JSON or text)
- No error messages

**If it fails (common in first run):**
- Note error message
- Check: API key configuration
- Check: Task description clarity
- Check: Agent tool access

---

## Phase 10: Results Verification

### View Results
- [ ] Navigate to Results page
- [ ] See execution in list
- [ ] Timestamp correct
- [ ] Crew name: Solar Analysis Crew
- [ ] Status shows (Success or Failed)
- [ ] Click to view details
- [ ] Full execution log visible
- [ ] Agent output displayed
- [ ] Tool usage logged (if any)

### If Execution Failed
**Document error details:**
```
Error message: _________________________________
Stack trace: ___________________________________
Suspected cause: _______________________________
Resolution attempt: ____________________________
```

---

## Phase 11: Database Verification

### Connect to Database
```bash
# Get connection string from Railway dashboard
# Format: postgresql://postgres:PASSWORD@postgresdb-production-e5ae.up.railway.app:5432/commandcenter

railway link
railway run psql $DATABASE_URL
```

### Query Agent Data
```sql
-- List all agents
SELECT * FROM agents;

-- Should see: Solar Data Analyst
```

- [ ] Query executed successfully
- [ ] Agent "Solar Data Analyst" present
- [ ] All fields populated
- [ ] Created timestamp correct

### Query Task Data
```sql
-- List all tasks
SELECT * FROM tasks;

-- Should see: Analyze Solar Data
```

- [ ] Query executed successfully
- [ ] Task "Analyze Solar Data" present
- [ ] Description stored correctly
- [ ] Agent assignment correct

### Query Crew Data
```sql
-- List all crews
SELECT * FROM crews;

-- Should see: Solar Analysis Crew
```

- [ ] Query executed successfully
- [ ] Crew "Solar Analysis Crew" present
- [ ] Configuration stored correctly
- [ ] Process type: Sequential

### Query Execution Results
```sql
-- List crew runs
SELECT * FROM crew_runs ORDER BY created_at DESC LIMIT 5;
```

- [ ] Query executed successfully
- [ ] Recent execution visible
- [ ] Status recorded
- [ ] Output stored (if any)

---

## Phase 12: Import/Export Test

### Export Configuration
- [ ] Navigate to Import/export page
- [ ] Click "Export" button
- [ ] Select items to export:
  - [ ] Agents
  - [ ] Tasks
  - [ ] Crews
- [ ] Click Download
- [ ] JSON file downloads
- [ ] Open file, verify structure
- [ ] Agents present in JSON
- [ ] Tasks present in JSON
- [ ] Crews present in JSON

### Backup Verification
- [ ] File size reasonable (>1KB)
- [ ] JSON is valid (use jsonlint.com or similar)
- [ ] Contains expected data
- [ ] Save file as backup: `crew_backup_2025-10-06.json`

---

## Phase 13: End-to-End Flow Test

### Complete Workflow
1. **Create Second Agent:**
   ```
   Role: Energy Optimization Specialist
   Goal: Provide specific recommendations to improve solar system efficiency
   Backstory: You are an expert in solar panel optimization with 15+ years
              of field experience. You translate data insights into actionable
              recommendations for system operators.
   ```
   - [ ] Agent created successfully

2. **Create Second Task:**
   ```
   Description: Based on the analysis results, provide 3-5 specific, actionable
               recommendations to optimize solar production. Each recommendation
               should include estimated impact and implementation difficulty.

   Expected Output: A markdown list of recommendations with:
                   - Recommendation description
                   - Estimated impact (High/Medium/Low)
                   - Implementation difficulty (Easy/Medium/Hard)
                   - Estimated cost range
   ```
   - [ ] Task created successfully
   - [ ] Context set to first task

3. **Update Crew:**
   - [ ] Edit "Solar Analysis Crew"
   - [ ] Add second agent: Energy Optimization Specialist
   - [ ] Add second task: (optimization recommendations)
   - [ ] Save changes

4. **Run Updated Crew:**
   - [ ] Go to Kickoff! page
   - [ ] Select Solar Analysis Crew
   - [ ] Kickoff
   - [ ] Both tasks execute
   - [ ] Task 2 uses output from Task 1 (context working)
   - [ ] Execution completes
   - [ ] Final recommendations generated

5. **Verify Results:**
   - [ ] Go to Results page
   - [ ] Latest execution shows both tasks
   - [ ] Task 1 output available
   - [ ] Task 2 output uses Task 1 data
   - [ ] Final result is cohesive

---

## Phase 14: Advanced Features Test

### Hierarchical Process Test
- [ ] Create crew with Hierarchical process
- [ ] Assign 3+ agents
- [ ] Add 4+ tasks
- [ ] Run crew
- [ ] Observe manager agent behavior
- [ ] Task delegation occurs
- [ ] Results synthesized by manager

### Knowledge Integration Test
- [ ] Add document to Knowledge Base
- [ ] Create task that requires knowledge
- [ ] Run crew
- [ ] Verify knowledge was used (check agent output)

### Custom Tool Test
- [ ] Enable additional tools
- [ ] Create agent with new tools
- [ ] Create task that uses tool
- [ ] Run crew
- [ ] Verify tool was invoked
- [ ] Check tool output

---

## Phase 15: Documentation & Summary

### Screenshots Collected
- [ ] CrewAI Studio homepage
- [ ] Agents page with created agent
- [ ] Tasks page with created task
- [ ] Crews page with created crew
- [ ] Kickoff! page during execution
- [ ] Results page with completed execution
- [ ] Frontend /studio page
- [ ] Database query results

### Test Results Summary
**Agents Created:** ____
**Tasks Created:** ____
**Crews Created:** ____
**Successful Executions:** ____
**Failed Executions:** ____

**Major Issues Found:**
1. ___________________________________
2. ___________________________________
3. ___________________________________

**Minor Issues Found:**
1. ___________________________________
2. ___________________________________

**Features Working Perfectly:**
1. ___________________________________
2. ___________________________________
3. ___________________________________

### Performance Notes
- **Average task execution time:** ____ seconds
- **Database query response time:** ____ ms
- **Frontend page load time:** ____ seconds
- **Studio page load time:** ____ seconds

---

## Final Status: Phase 4 Integration

### Success Criteria
- [ ] ✅ CrewAI Studio accessible at https://studio.wildfireranch.us
- [ ] ✅ Frontend /studio page loads Studio in iframe
- [ ] ✅ Can create agents in Studio
- [ ] ✅ Can create tasks in Studio
- [ ] ✅ Can create crews in Studio
- [ ] ✅ Can run crews successfully
- [ ] ✅ Data persists in PostgreSQL database
- [ ] ✅ All pages functional
- [ ] ✅ No critical errors

### Phase 4 Status: [ ] COMPLETE / [ ] NEEDS WORK

**Next Steps:**
_________________________________________
_________________________________________
_________________________________________

---

**Testing Completed:** __________ (Date/Time)
**Tester:** CommandCenter Development Team
**Session:** 015
**Overall Result:** [ ] PASS / [ ] FAIL / [ ] PARTIAL
