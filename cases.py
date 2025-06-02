from datetime import datetime, timedelta
from simple_model import Case, Comment, CaseState, Priority, Component, Change
from tools_and_resources import (
    case_store, webapp_dev, applog_dev, support_agent, api_dev, database_admin, security_analyst
)

# Create timeline
case_created = datetime.now() - timedelta(days=4)
investigation_start = case_created + timedelta(hours=2)
component_change = case_created + timedelta(days=1, hours=6)
resolution = case_created + timedelta(days=3)

# Historical resolved case (CASE-2025-001)
historical_case = Case(
    id="CASE-2025-001",
    title="WebApp Hangs When Clicking Run Job Button",
    description="Customer reports that clicking the 'run job' button causes the entire web application to hang and become unresponsive. This makes the app completely unusable for their business operations.",
    priority=Priority.HIGH,
    state=CaseState.RESOLVED,
    assignee=applog_dev,  # Final assignee after investigation
    component=Component.APPLOG,  # Final component after investigation
    created_at=case_created,
    updated_at=resolution,
    comments=[
        Comment(
            id="comment001",
            content="Initial report received from customer. WebApp freezes when 'run job' button is clicked. Assigning to WebApp development team for initial investigation.",
            author=support_agent.name,
            created_at=case_created.isoformat(),
            updated_at=case_created.isoformat()
        ),
        Comment(
            id="comment002", 
            content="Started investigation. Checking WebApp frontend code and button click handlers. Initial tests show button click triggers but app becomes unresponsive.",
            author=webapp_dev.name,
            created_at=investigation_start.isoformat(),
            updated_at=investigation_start.isoformat()
        ),
        Comment(
            id="comment003",
            content="WebApp frontend code appears correct. Button click successfully initiates job process. However, discovered that app hangs occur when job tries to write logs. Suspecting AppLog component issue. Reassigning to AppLog team.",
            author=webapp_dev.name,
            created_at=component_change.isoformat(),
            updated_at=component_change.isoformat()
        ),
        Comment(
            id="comment004",
            content="Investigation confirmed: AppLog component has a deadlock issue when multiple log entries are written simultaneously during job execution. This causes the entire application to hang waiting for log writes to complete.",
            author=applog_dev.name,
            created_at=(component_change + timedelta(hours=4)).isoformat(),
            updated_at=(component_change + timedelta(hours=4)).isoformat()
        ),
        Comment(
            id="comment005",
            content="Fix implemented: Updated AppLog component to use async logging with proper queue management. Deployed to production. Customer confirmed 'run job' button now works correctly without hanging.",
            author=applog_dev.name,
            created_at=resolution.isoformat(),
            updated_at=resolution.isoformat()
        )
    ],
    change_history=[
        Change(
            field="state",
            old_value="new",
            new_value="in_progress", 
            changed_at=investigation_start
        ),
        Change(
            field="assignee",
            old_value=webapp_dev.name,
            new_value=applog_dev.name,
            changed_at=component_change
        ),
        Change(
            field="component",
            old_value="webapp",
            new_value="applog",
            changed_at=component_change
        ),
        Change(
            field="state",
            old_value="in_progress",
            new_value="resolved",
            changed_at=resolution
        )
    ]
)

# Incoming case for Scenario 1 (CASE-2025-002)
incoming_case = Case(
    id="CASE-2025-002",
    title="WebApp Hangs When Clicking Run Job Button",
    description="Customer reports that clicking the 'run job' button causes the entire web application to hang and become unresponsive. This makes the app completely unusable for their business operations.",
    priority=Priority.HIGH,
    state=CaseState.NEW,
    assignee=webapp_dev,
    component=Component.WEBAPP,
    created_at=case_created,
    updated_at=case_created,
    comments=[],
    change_history=[]
)

# Complex case with many comments for Scenario 2 (CASE-2025-003)
complex_case_created = datetime.now() - timedelta(days=7)
complex_case = Case(
    id="CASE-2025-003",
    title="Performance Issues and Intermittent 500 Errors in Production",
    description="Multiple customers reporting slow response times and intermittent 500 errors across different parts of the application. Issue seems to be affecting the entire platform with no clear pattern.",
    priority=Priority.VERY_HIGH,
    state=CaseState.IN_PROGRESS,
    assignee=webapp_dev,  # Final assignee after investigation
    component=Component.WEBAPP,  # Final component after investigation
    created_at=complex_case_created,
    updated_at=datetime.now(),
    comments=[
        Comment(
            id="comment_complex_001",
            content="Initial customer reports coming in about slow performance and 500 errors. Creating high priority case. Multiple customers affected across different browsers and devices.",
            author=support_agent.name,
            created_at=(complex_case_created).isoformat(),
            updated_at=(complex_case_created).isoformat()
        ),
        Comment(
            id="comment_complex_002", 
            content="Database team investigating performance issues. Initial analysis shows database queries are performing normally. Average response times are within acceptable ranges. No blocking queries detected.",
            author=database_admin.name,
            created_at=(complex_case_created + timedelta(hours=1)).isoformat(),
            updated_at=(complex_case_created + timedelta(hours=1)).isoformat()
        ),
        Comment(
            id="comment_complex_003",
            content="API team analysis: Backend endpoints are responding correctly with normal latency. 500 errors appear to be triggered by malformed requests coming from the frontend. Request payloads contain invalid JSON in some cases.",
            author=api_dev.name,
            created_at=(complex_case_created + timedelta(hours=3)).isoformat(),
            updated_at=(complex_case_created + timedelta(hours=3)).isoformat()
        ),
        Comment(
            id="comment_complex_004",
            content="Security team investigated potential DDoS or attack vectors. No malicious activity detected. Traffic patterns appear normal. The errors seem to be legitimate user interactions gone wrong.",
            author=security_analyst.name,
            created_at=(complex_case_created + timedelta(hours=5)).isoformat(),
            updated_at=(complex_case_created + timedelta(hours=5)).isoformat()
        ),
        Comment(
            id="comment_complex_005",
            content="AppLog analysis shows error patterns correlate with specific user actions: form submissions, file uploads, and search queries. Errors spike during peak usage hours. Frontend seems to be sending corrupted data.",
            author=applog_dev.name,
            created_at=(complex_case_created + timedelta(days=1)).isoformat(),
            updated_at=(complex_case_created + timedelta(days=1)).isoformat()
        ),
        Comment(
            id="comment_complex_006",
            content="WebApp team taking over investigation. Found significant memory leaks in React components. DOM nodes not being properly cleaned up, causing browser performance degradation over time.",
            author=webapp_dev.name,
            created_at=(complex_case_created + timedelta(days=1, hours=6)).isoformat(),
            updated_at=(complex_case_created + timedelta(days=1, hours=6)).isoformat()
        ),
        Comment(
            id="comment_complex_007",
            content="Database team confirming: After WebApp team's investigation, we can see the corrupted requests are causing our input validation to throw 500 errors. Backend is working correctly, issue is definitely frontend data corruption.",
            author=database_admin.name,
            created_at=(complex_case_created + timedelta(days=2)).isoformat(),
            updated_at=(complex_case_created + timedelta(days=2)).isoformat()
        ),
        Comment(
            id="comment_complex_008",
            content="WebApp team deep dive: Memory leaks causing JavaScript heap overflow after prolonged usage. This corrupts form data before submission. Implementing proper component lifecycle management and memory cleanup.",
            author=webapp_dev.name,
            created_at=(complex_case_created + timedelta(days=2, hours=8)).isoformat(),
            updated_at=(complex_case_created + timedelta(days=2, hours=8)).isoformat()
        ),
        Comment(
            id="comment_complex_009",
            content="API team confirming fix effectiveness: After WebApp team deployed memory leak fixes, we're no longer receiving malformed requests. 500 error rate dropped significantly.",
            author=api_dev.name,
            created_at=(complex_case_created + timedelta(days=3)).isoformat(),
            updated_at=(complex_case_created + timedelta(days=3)).isoformat()
        ),
        Comment(
            id="comment_complex_010",
            content="WebApp team final update: Deployed comprehensive fix including React component optimization, proper event listener cleanup, and improved state management. Performance monitoring shows normal memory usage patterns.",
            author=webapp_dev.name,
            created_at=(complex_case_created + timedelta(days=3, hours=4)).isoformat(),
            updated_at=(complex_case_created + timedelta(days=3, hours=4)).isoformat()
        ),
        Comment(
            id="comment_complex_011",
            content="AppLog monitoring confirms resolution: Error rates back to baseline 0.1%. No more corrupted request patterns detected. Frontend performance metrics show stable memory usage.",
            author=applog_dev.name,
            created_at=(complex_case_created + timedelta(days=4)).isoformat(),
            updated_at=(complex_case_created + timedelta(days=4)).isoformat()
        ),
        Comment(
            id="comment_complex_012",
            content="Support team update: Customer reports confirm resolution. No more performance complaints or 500 errors reported. Users experiencing normal application responsiveness. Case ready for closure.",
            author=support_agent.name,
            created_at=(complex_case_created + timedelta(days=4, hours=6)).isoformat(),
            updated_at=(complex_case_created + timedelta(days=4, hours=6)).isoformat()
        )
    ],
    change_history=[
        Change(
            field="priority",
            old_value="high",
            new_value="very_high",
            changed_at=complex_case_created + timedelta(hours=2)
        ),
        Change(
            field="assignee", 
            old_value=support_agent.name,
            new_value=database_admin.name,
            changed_at=complex_case_created + timedelta(hours=1)
        ),
        Change(
            field="assignee",
            old_value=database_admin.name,
            new_value=webapp_dev.name,
            changed_at=complex_case_created + timedelta(days=1, hours=6)
        ),
        Change(
            field="component",
            old_value="other",
            new_value="webapp", 
            changed_at=complex_case_created + timedelta(days=1, hours=6)
        )
    ]
)

# Permissions case for Scenario 3 (CASE-2025-004)
permissions_case = Case(
    id="CASE-2025-004",
    title="Cannot Create New Job - Permission Denied Error",
    description="Customer reports that when they try to create a new job using their regular user account, they get a 'Permission Denied' error. They need to be able to create jobs for their daily workflow but the system is blocking them.",
    priority=Priority.MEDIUM,
    state=CaseState.NEW,
    assignee=support_agent,
    component=Component.WEBAPP,
    created_at=datetime.now() - timedelta(hours=2),
    updated_at=datetime.now() - timedelta(hours=2),
    comments=[],
    change_history=[]
)

def load_all_cases():
    """Load all cases into the case store."""
    case_store[historical_case.id] = historical_case
    case_store[incoming_case.id] = incoming_case
    case_store[complex_case.id] = complex_case
    case_store[permissions_case.id] = permissions_case
    
    return {
        "historical_case": historical_case,
        "incoming_case": incoming_case, 
        "complex_case": complex_case,
        "permissions_case": permissions_case
    } 