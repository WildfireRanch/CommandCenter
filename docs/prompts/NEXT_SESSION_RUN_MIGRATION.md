# Next Session: Complete Database Health Dashboard Setup

**Context:** Session 031 completed the Database Health Dashboard implementation. One small migration needs to run to complete the setup.

---

## 📋 Your Prompt for Next Session

Copy/paste this to Claude Code:

```
Please complete the Database Health Dashboard setup by running the database migration.

Instructions are in: docs/prompts/RUN_HEALTH_MONITORING_MIGRATION.md

You have Railway access to CommandCenterProject production environment.

Background:
- All code is implemented and deployed
- Health status endpoint is working: https://api.wildfireranch.us/health/monitoring/status
- We need to create the monitoring.health_snapshots table for historical data

Please:
1. Read the RAILWAY_ACCESS_GUIDE at the project root
2. Follow RUN_HEALTH_MONITORING_MIGRATION.md to execute the SQL
3. Verify the history endpoint works after migration
4. Confirm first health snapshot is collected

Session 031 summary: docs/sessions/SESSION_031_SUMMARY.md
```

---

## 🎯 Expected Outcome

After running this prompt, Claude Code will:

1. ✅ Read Railway access guide
2. ✅ Connect to Railway PostgreSQL database
3. ✅ Execute the migration SQL
4. ✅ Verify table was created
5. ✅ Test history endpoint
6. ✅ Wait and confirm first snapshot collected

**Time Required:** ~10 minutes (including waiting for first snapshot)

---

## ✅ Success Indicators

You'll know it worked when:

- History endpoint returns: `{"status": "success", "hours": 1, "data": [...]}`
- Backend logs show: `"Health snapshot #1 stored"`
- Dashboard charts start populating with data

---

## 📚 Reference Files

- **Migration SQL:** `railway/src/database/migrations/004_health_monitoring.sql`
- **Detailed Instructions:** `docs/prompts/RUN_HEALTH_MONITORING_MIGRATION.md`
- **Railway Guide:** `RAILWAY_ACCESS_GUIDE` (project root)
- **Session Summary:** `docs/sessions/SESSION_031_SUMMARY.md`
