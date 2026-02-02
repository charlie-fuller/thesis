"""Thesis Load Testing with Locust

Run with:
  locust -f locustfile.py --host=http://localhost:8000

For headless mode:
  locust -f locustfile.py --host=http://localhost:8000 --headless --users 50 --spawn-rate 5 --run-time 10m
"""

import os
import random

from locust import HttpUser, between, events, task
from locust.runners import MasterRunner

# Test configuration
TEST_EMAIL = os.getenv("LOADTEST_EMAIL", "loadtest@thesis.ai")
TEST_PASSWORD = os.getenv("LOADTEST_PASSWORD", "loadtest-password")

# Sample messages for chat testing
SAMPLE_MESSAGES = [
    "What are the latest AI trends?",
    "Calculate the ROI for this project",
    "What are the security risks of implementing AI?",
    "How should we handle change management?",
    "@atlas What does Gartner say about enterprise AI?",
    "@capital Can you help me build a business case?",
    "@guardian What are the compliance considerations?",
    "@sage How do we address employee concerns about AI?",
    "What is the best approach for AI implementation?",
    "Summarize the key challenges we face",
]

# Sample search queries
SAMPLE_SEARCHES = [
    "artificial intelligence",
    "machine learning",
    "ROI analysis",
    "security compliance",
    "change management",
    "enterprise AI",
    "automation",
    "digital transformation",
]


class ThesisUser(HttpUser):
    """Simulates a typical Thesis user workflow.

    Tasks are weighted to represent realistic usage patterns:
    - Most common: listing/reading (weight 10)
    - Common: chat messages (weight 5)
    - Less common: search, document operations (weight 3)
    - Rare: create/update operations (weight 1)
    """

    wait_time = between(1, 5)  # Wait 1-5 seconds between tasks

    def on_start(self):
        """Login and get auth token at the start of the test."""
        self.token = None
        self.conversation_id = None
        self.login()

    def login(self):
        """Authenticate and store the JWT token."""
        response = self.client.post(
            "/api/auth/login",
            json={
                "email": TEST_EMAIL,
                "password": TEST_PASSWORD,
            },
        )

        if response.status_code == 200:
            data = response.json()
            self.token = data.get("access_token")
            self.headers = {"Authorization": f"Bearer {self.token}"}
        else:
            # If login fails, log it but continue
            print(f"Login failed: {response.status_code}")
            self.headers = {}

    @property
    def auth_headers(self):
        """Return authorization headers."""
        return self.headers if hasattr(self, "headers") else {}

    # ==================== Conversation Tasks ====================

    @task(10)
    def list_conversations(self):
        """List user's conversations."""
        self.client.get("/api/conversations", headers=self.auth_headers)

    @task(5)
    def send_chat_message(self):
        """Send a chat message and wait for response."""
        message = random.choice(SAMPLE_MESSAGES)

        response = self.client.post(
            "/api/chat/send",
            json={
                "message": message,
                "conversation_id": self.conversation_id,
                "stream": False,  # Non-streaming for load test
            },
            headers=self.auth_headers,
            timeout=30,
        )

        if response.status_code == 200:
            data = response.json()
            # Save conversation ID for future messages
            if "conversation_id" in data:
                self.conversation_id = data["conversation_id"]

    @task(3)
    def get_conversation_messages(self):
        """Get messages in a conversation."""
        if self.conversation_id:
            self.client.get(
                f"/api/conversations/{self.conversation_id}/messages",
                headers=self.auth_headers,
            )

    # ==================== Document Tasks ====================

    @task(3)
    def list_documents(self):
        """List knowledge base documents."""
        self.client.get("/api/documents", headers=self.auth_headers)

    @task(3)
    def search_documents(self):
        """Search knowledge base."""
        query = random.choice(SAMPLE_SEARCHES)
        self.client.get(
            f"/api/documents/search?q={query}",
            headers=self.auth_headers,
        )

    # ==================== Stakeholder Tasks ====================

    @task(5)
    def list_stakeholders(self):
        """List stakeholders."""
        self.client.get("/api/stakeholders", headers=self.auth_headers)

    @task(2)
    def get_stakeholder_insights(self):
        """Get stakeholder insights."""
        self.client.get("/api/stakeholders/insights", headers=self.auth_headers)

    # ==================== Opportunity Tasks ====================

    @task(5)
    def list_opportunities(self):
        """List opportunities."""
        self.client.get("/api/opportunities", headers=self.auth_headers)

    @task(2)
    def get_opportunity_metrics(self):
        """Get opportunity metrics."""
        self.client.get("/api/opportunities/metrics", headers=self.auth_headers)

    # ==================== Task Management ====================

    @task(5)
    def list_tasks(self):
        """List kanban tasks."""
        self.client.get("/api/tasks", headers=self.auth_headers)

    # ==================== Meeting Room Tasks ====================

    @task(3)
    def list_meeting_rooms(self):
        """List meeting rooms."""
        self.client.get("/api/meeting-rooms", headers=self.auth_headers)

    # ==================== Agent Tasks ====================

    @task(3)
    def list_agents(self):
        """List available agents."""
        self.client.get("/api/agents", headers=self.auth_headers)


class ChatHeavyUser(HttpUser):
    """User that focuses primarily on chat interactions.
    Use this to stress test the chat/AI endpoints.
    """

    wait_time = between(2, 8)  # Slightly longer waits for AI responses
    weight = 1  # Lower weight in mixed scenarios

    def on_start(self):
        """Login at start."""
        response = self.client.post(
            "/api/auth/login",
            json={
                "email": TEST_EMAIL,
                "password": TEST_PASSWORD,
            },
        )

        if response.status_code == 200:
            data = response.json()
            self.token = data.get("access_token")
            self.headers = {"Authorization": f"Bearer {self.token}"}
        else:
            self.headers = {}

        self.conversation_id = None

    @task(10)
    def send_message(self):
        """Send chat messages heavily."""
        message = random.choice(SAMPLE_MESSAGES)

        response = self.client.post(
            "/api/chat/send",
            json={
                "message": message,
                "conversation_id": self.conversation_id,
                "stream": False,
            },
            headers=self.headers,
            timeout=60,  # AI responses can take time
        )

        if response.status_code == 200:
            data = response.json()
            if "conversation_id" in data:
                self.conversation_id = data["conversation_id"]

    @task(3)
    def start_new_conversation(self):
        """Start fresh conversations."""
        self.conversation_id = None
        self.send_message()


class SearchHeavyUser(HttpUser):
    """User that focuses on search and document operations.
    Use this to stress test the RAG pipeline.
    """

    wait_time = between(0.5, 2)  # Fast searches
    weight = 1

    def on_start(self):
        """Login at start."""
        response = self.client.post(
            "/api/auth/login",
            json={
                "email": TEST_EMAIL,
                "password": TEST_PASSWORD,
            },
        )

        if response.status_code == 200:
            data = response.json()
            self.token = data.get("access_token")
            self.headers = {"Authorization": f"Bearer {self.token}"}
        else:
            self.headers = {}

    @task(10)
    def search_kb(self):
        """Search knowledge base heavily."""
        query = random.choice(SAMPLE_SEARCHES)
        self.client.get(
            f"/api/documents/search?q={query}",
            headers=self.headers,
        )

    @task(5)
    def list_documents(self):
        """List documents."""
        self.client.get("/api/documents", headers=self.headers)

    @task(3)
    def semantic_search(self):
        """Semantic similarity search."""
        query = random.choice(SAMPLE_SEARCHES)
        self.client.post(
            "/api/documents/semantic-search",
            json={"query": query, "limit": 10},
            headers=self.headers,
        )


# Event hooks for custom reporting
@events.test_start.add_listener
def on_test_start(environment, **kwargs):
    """Called when the test starts."""
    print("=" * 60)
    print("Thesis Load Test Starting")
    print("=" * 60)
    if isinstance(environment.runner, MasterRunner):
        print("Running in distributed mode (master)")
    else:
        print("Running in standalone mode")


@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    """Called when the test stops."""
    print("=" * 60)
    print("Thesis Load Test Complete")
    print("=" * 60)

    # Print summary statistics
    stats = environment.stats
    print(f"\nTotal requests: {stats.total.num_requests}")
    print(f"Total failures: {stats.total.num_failures}")
    print(f"Average response time: {stats.total.avg_response_time:.2f}ms")
    print(f"Requests/sec: {stats.total.current_rps:.2f}")


@events.request.add_listener
def on_request(request_type, name, response_time, response_length, response, **kwargs):
    """Called on each request - can be used for custom metrics."""
    # Log slow requests
    if response_time > 5000:  # 5 seconds
        print(f"SLOW REQUEST: {request_type} {name} - {response_time:.2f}ms")
