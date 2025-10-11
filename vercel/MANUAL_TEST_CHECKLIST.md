# Manual Test Checklist: Agent Visualization Dashboard

## Test Results Summary
Date: 2025-10-11
Tester: Automated + Manual Verification

---

## Test 1: Empty Session State ✅

**Scenario**: Open chat with no messages
- [ ] Panel opens without errors
- [ ] Shows "Loading insights..." initially
- [ ] Shows empty state or minimal data
- [ ] No console errors

**Result**: PASS - `useSessionInsights` returns `null` for empty sessions

---

## Test 2: Rapid Panel Toggling ⚡

**Scenario**: Click "Insights" button 20+ times rapidly
- [ ] Panel animations remain smooth
- [ ] No visual glitches or flickering
- [ ] No console errors or warnings
- [ ] Memory usage remains stable

**How to test**:
```javascript
// In browser console:
for(let i=0; i<50; i++) {
  document.querySelector('[title="Toggle insights panel"]').click()
  await new Promise(r => setTimeout(r, 50))
}
```

**Expected**: Smooth animations, no crashes

---

## Test 3: Large Dataset Performance 📊

**Scenario**: Session with 100+ messages
- [ ] Insights calculate in < 500ms
- [ ] Panel scrolling is smooth (60fps)
- [ ] Charts render without lag
- [ ] Tab switching is instant

**How to test**:
```javascript
// Generate 100 messages
const msgs = []
for(let i=0; i<100; i++) {
  msgs.push({ role: i%2 ? 'assistant' : 'user', content: `Test ${i}`, timestamp: new Date().toISOString(), agent_role: 'Manager', context_tokens: 2000 })
}
// Monitor performance tab in DevTools
```

**Performance Targets**:
- Initial render: < 200ms
- Re-render on new message: < 50ms
- Scroll FPS: 60fps
- Memory: < 50MB for panel

---

## Test 4: Malformed Metadata 🛡️

**Scenario**: Messages with missing/invalid data
- [ ] Missing `context_tokens`: Shows 0 tokens
- [ ] Missing `agent_role`: Shows "Unknown" or fallback
- [ ] Negative `duration_ms`: Treats as 0
- [ ] Invalid `query_type`: Gracefully ignored
- [ ] Extreme values (999999 tokens): Displays correctly

**Test data**:
```javascript
const malformed = [
  { role: 'assistant', content: 'Test' }, // Missing everything
  { role: 'assistant', content: 'Test', context_tokens: -500 }, // Negative
  { role: 'assistant', content: 'Test', context_tokens: 999999 }, // Extreme
]
```

**Expected**: No crashes, sensible fallback values

---

## Test 5: Tab State Persistence 🔄

**Scenario**: Switch tabs and close/reopen panel
- [ ] Active tab is remembered when reopening panel
- [ ] Scroll position within tabs is preserved
- [ ] Data remains consistent across reopens

**Steps**:
1. Open panel
2. Switch to "Agents" tab
3. Scroll down
4. Close panel
5. Reopen panel
6. Verify "Agents" tab is still active
7. Verify scroll position maintained

**Expected**: Tab state persists

---

## Test 6: Responsive Breakpoints 📱

**Scenario**: Test on different screen sizes

### Mobile (< 640px)
- [ ] Panel goes full width
- [ ] Tabs show icons only or stacked
- [ ] Touch-friendly (44px+ tap targets)
- [ ] Backdrop blur overlay appears
- [ ] Swipe-to-close works

### Tablet (640-1024px)
- [ ] Panel is 384px wide (w-96)
- [ ] All content readable
- [ ] Charts scale appropriately

### Desktop (> 1024px)
- [ ] Panel is 280px wide (w-80)
- [ ] Smooth slide-in from right
- [ ] No horizontal overflow

**Test in DevTools responsive mode**: 375px, 768px, 1440px

---

## Test 7: Reduced Motion Accessibility ♿

**Scenario**: Users with motion sensitivity
- [ ] Animations respect `prefers-reduced-motion: reduce`
- [ ] Panel still functions without animations
- [ ] Transitions are instant or minimal

**How to test**:
1. Chrome DevTools → Rendering → Emulate CSS media
2. Select "prefers-reduced-motion: reduce"
3. Open panel
4. Verify animations are simplified

**Expected**: No sliding animations, instant appearance

---

## Test 8: Concurrent API Refresh 🔄

**Scenario**: Auto-refresh while user interacts with panel
- [ ] No flickering during refresh
- [ ] User interactions not interrupted
- [ ] Scroll position maintained during refresh
- [ ] No race conditions with multiple refreshes

**How to test**:
1. Set `refreshInterval: 1000` (1 second)
2. Open panel
3. Scroll through tabs
4. Watch for 10+ refresh cycles
5. Monitor network tab for request timing

**Expected**: Smooth updates, no visual jumps

---

## Test 9: Zero Division Edge Cases 🔢

**Scenario**: Calculations with zero values
- [ ] 0 total queries: Shows 0%, not NaN
- [ ] 0 tokens: Shows 0, not Infinity
- [ ] 0 duration: Shows 0ms, not undefined
- [ ] All zero values: Panel displays empty state gracefully

**Test cases**:
```javascript
// Percentage calculation: 5 / 0 queries
const pct = agentContribution.query_count / (totalQueries || 1) * 100

// Token average: 0 / 0
const avg = totalTokens / (messages.length || 1)

// Hit rate: 0 / 0
const hitRate = cacheHits / (totalQueries || 1) * 100
```

**Expected**: All calculations return valid numbers (0, not NaN/Infinity)

---

## Test 10: Memory Leak Detection 🔍

**Scenario**: Long-running session (30+ minutes)
- [ ] Memory growth is linear with data, not exponential
- [ ] Intervals are cleaned up on unmount
- [ ] Event listeners removed on panel close
- [ ] No detached DOM nodes in memory

**How to test**:
1. Open Chrome DevTools → Memory
2. Take heap snapshot
3. Use panel for 5 minutes (open/close, switch tabs)
4. Take second snapshot
5. Compare snapshots for detached nodes

**Memory targets**:
- Initial: ~30MB
- After 100 messages: ~45MB
- Growth rate: < 150KB per message

**Tools**:
```javascript
// Monitor in console
console.log(performance.memory)

// Check active intervals
console.log(window.setInterval.toString())
```

---

## Integration Tests 🔗

### Test 11: Real-time Message Sync
**Scenario**: Send messages while panel is open
- [ ] New message appears in chat
- [ ] Panel updates automatically (within 5s refresh)
- [ ] Token count increases
- [ ] Agent contribution updates
- [ ] Cache metrics update

**Steps**:
1. Open panel with "Overview" tab visible
2. Send a message in chat
3. Wait 5 seconds (refresh interval)
4. Verify stats updated

---

### Test 12: API Failure Graceful Degradation
**Scenario**: Backend API is down
- [ ] Panel still opens
- [ ] Falls back to client-side calculation
- [ ] Shows computed insights from messages
- [ ] User doesn't notice the difference

**How to test**:
1. Block `/chat/sessions/:id/insights` in DevTools Network tab
2. Open panel
3. Verify it still shows data

---

### Test 13: Cross-Browser Compatibility
- [ ] Chrome/Edge (Chromium)
- [ ] Firefox
- [ ] Safari (WebKit)
- [ ] Mobile Safari (iOS)
- [ ] Mobile Chrome (Android)

**Known issues**:
- Framer Motion animations may vary
- Backdrop blur support varies

---

## Performance Benchmarks 🎯

| Metric | Target | Actual | Status |
|--------|--------|--------|--------|
| Initial render | < 200ms | TBD | ⏳ |
| Insights calculation (100 msgs) | < 100ms | TBD | ⏳ |
| Tab switch | < 50ms | TBD | ⏳ |
| Memory usage (baseline) | < 50MB | TBD | ⏳ |
| Memory per message | < 150KB | TBD | ⏳ |
| Animation FPS | 60fps | TBD | ⏳ |
| Bundle size increase | < 100KB | TBD | ⏳ |

---

## Accessibility Checklist ♿

- [ ] Keyboard navigation works (Tab, Enter, Escape)
- [ ] Screen reader announces panel state
- [ ] Focus trap when panel is open
- [ ] Color contrast ratios pass WCAG AA
- [ ] Touch targets are 44x44px minimum
- [ ] Reduced motion preference respected
- [ ] All interactive elements have labels

---

## Visual Regression Tests 👁️

Take screenshots at:
1. Panel closed
2. Panel open - Overview tab
3. Panel open - Agents tab
4. Panel open - Context tab
5. Panel open - Performance tab
6. Mobile view (375px)
7. Tablet view (768px)
8. Desktop view (1440px)

Compare against baseline for:
- Layout shifts
- Color consistency
- Font rendering
- Animation smoothness

---

## Security Tests 🔒

- [ ] XSS prevention: Escape user content in messages
- [ ] No sensitive data in console logs
- [ ] API keys not exposed in client
- [ ] CORS policies respected
- [ ] No injection vulnerabilities in calculations

---

## Next Steps

1. Run automated tests: `npm test -- ChatAgentPanel.edge-cases.test.tsx`
2. Perform manual browser tests using this checklist
3. Monitor production metrics after deployment
4. Set up Sentry/error tracking for real-world issues
5. Add performance monitoring with Web Vitals

---

## Notes

- All tests should pass before production deployment
- Performance targets are based on typical user devices (mid-range laptop, 4G mobile)
- Memory leak tests should run for extended periods (30+ min)
- Consider adding E2E tests with Playwright for critical flows
