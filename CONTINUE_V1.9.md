# 🚀 CONTINUE V1.9 - Deploy Migration & Build API Endpoints

**Copy and paste this into your next Claude Code session:**

---

I'm continuing CommandCenter V1.9 implementation - User Preferences System.

**Previous session:** Database migration prepared and tested (Session 036)
**This session:** Deploy migration to Railway + Build API endpoints

## 📚 Context (read these first)

1. **[docs/sessions/2025-10/session-036-v1.9-migration-ready.md](docs/sessions/2025-10/session-036-v1.9-migration-ready.md)** - What was built
2. **[docs/versions/v1.9/V1.9_MIGRATION_DEPLOYMENT_GUIDE.md](docs/versions/v1.9/V1.9_MIGRATION_DEPLOYMENT_GUIDE.md)** - Deployment instructions
3. **[docs/versions/v1.9/V1.9_TECHNICAL_SPECIFICATION.md](docs/versions/v1.9/V1.9_TECHNICAL_SPECIFICATION.md)** - API specs
4. **[docs/versions/v1.9/V1.9_quick_reference.md](docs/versions/v1.9/V1.9_quick_reference.md)** - Quick reference

## 🎯 Tasks

### Part 1: Deploy Migration (Railway CLI - Option 1)

1. **Pre-deployment check:**
   ```bash
   cd /workspaces/CommandCenter/railway
   python3 test_v19_migration.py  # Verify tests pass
   ```

2. **Deploy to Railway:**
   ```bash
   railway login
   railway link

   # DRY-RUN first (with ROLLBACK)
   railway run bash -c "cat src/database/migrations/006_v1.9_user_preferences.sql | \
     sed 's/COMMIT;/ROLLBACK;/' | \
     psql \$DATABASE_URL"

   # ACTUAL deployment
   railway run psql $DATABASE_URL -f src/database/migrations/006_v1.9_user_preferences.sql
   ```

3. **Validate:**
   ```bash
   railway run psql $DATABASE_URL -f validate_v19_migration.sql
   ```

Expected: 4 tables, 1 user, 1 pref, 2 miners, 2 HVAC zones

### Part 2: Build API Endpoints (Week 1, Day 3-4)

Create these files:

1. **`railway/src/api/models/v1_9.py`** - Pydantic models
   - UserPreferencesBase
   - MinerProfileBase
   - HVACZoneBase
   - (See V1.9_TECHNICAL_SPECIFICATION.md lines 436-483)

2. **`railway/src/api/routes/preferences.py`** - User preferences CRUD
   - GET /api/users/preferences
   - PUT /api/users/preferences
   - POST /api/users/preferences/reset

3. **`railway/src/api/routes/miners.py`** - Miner profiles CRUD
   - GET /api/miners (list)
   - POST /api/miners (create)
   - GET /api/miners/{id}
   - PUT /api/miners/{id}
   - DELETE /api/miners/{id}

4. **`railway/src/api/routes/hvac.py`** - HVAC zones CRUD
   - Same pattern as miners

5. **Update `railway/src/api/main.py`** - Register routes
   ```python
   from api.routes import preferences, miners, hvac
   app.include_router(preferences.router)
   app.include_router(miners.router)
   app.include_router(hvac.router)
   ```

## ⚠️ Key Reminders

**DO:**
- ✅ Create database backup before migration
- ✅ Use voltage (not SOC%) for all decisions
- ✅ Follow priority-based miner allocation (1=highest)
- ✅ Add comprehensive docstrings

**DON'T:**
- ❌ Skip backup or dry-run
- ❌ Use SOC% for decisions
- ❌ Hardcode thresholds
- ❌ Break V1.8 functionality

**Solar Shack Defaults:**
- Voltage: 45.0V = 0%, 56.0V = 100%
- Optimal: 50.0V (40%) to 54.5V (80%)
- Primary miner: Priority 1, starts 50.0V
- Dump load: Priority 3, starts 54.5V, needs excess solar

## ✅ Success Criteria

**Part 1 (Migration):**
- [ ] Migration deployed without errors
- [ ] 4 tables created with default data
- [ ] Validation script passes
- [ ] V1.8 features still work

**Part 2 (API):**
- [ ] Pydantic models created
- [ ] 3 route files created
- [ ] Routes registered in main.py
- [ ] Basic CRUD working
- [ ] Tested with curl/Postman

## 📝 Session Output

Create:
1. Session log: `docs/sessions/2025-10/session-037-v1.9-api-endpoints.md`
2. Update `docs/INDEX.md` with session 037
3. Continuation prompt for Week 1, Day 5 (Agent Integration)

---

**Status:** Week 1, Day 1-2 ✅ COMPLETE → Day 3-4 Starting Now

Let's deploy this migration and build those API endpoints! 🚀
