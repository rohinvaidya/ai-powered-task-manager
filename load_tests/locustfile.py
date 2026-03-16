"""
Locust load test for the AI Task Manager API.

Run with:
    pip install locust
    locust -f load_tests/locustfile.py --host=http://localhost:8000

Then open http://localhost:8089 to control the test.

For headless CI runs:
    locust -f load_tests/locustfile.py --host=http://localhost:8000 \
        --headless -u 50 -r 10 --run-time 60s \
        --csv=load_tests/results
"""
import random
import uuid
from locust import HttpUser, SequentialTaskSet, between, task


class TaskManagerFlow(SequentialTaskSet):
    """
    Realistic user flow:
    1. Register (once per user)
    2. Login → get token
    3. Create a project
    4. Create several tasks
    5. Update task status
    6. Fetch analytics
    7. List tasks with filters
    """

    token: str = ""
    project_id: str = ""
    task_ids: list[str] = []

    def on_start(self):
        self.task_ids = []
        self._register_and_login()
        self._create_project()

    def _register_and_login(self):
        uid = uuid.uuid4().hex[:8]
        email = f"loadtest_{uid}@example.com"
        password = "loadtest123"

        # Register
        self.client.post(
            "/api/v1/auth/register",
            json={"email": email, "username": f"lt_{uid}", "password": password},
            name="/auth/register",
        )

        # Login
        res = self.client.post(
            "/api/v1/auth/login",
            json={"email": email, "password": password},
            name="/auth/login",
        )
        if res.status_code == 200:
            self.token = res.json().get("access_token", "")

    def _create_project(self):
        res = self.client.post(
            "/api/v1/projects",
            json={"name": f"Load Test Project {uuid.uuid4().hex[:6]}"},
            headers=self._auth(),
            name="/projects [POST]",
        )
        if res.status_code == 201:
            self.project_id = res.json().get("id", "")

    def _auth(self) -> dict:
        return {"Authorization": f"Bearer {self.token}"}

    @task
    def create_tasks(self):
        if not self.project_id:
            return
        priorities = ["low", "medium", "high", "urgent"]
        for _ in range(3):
            res = self.client.post(
                f"/api/v1/projects/{self.project_id}/tasks",
                json={
                    "title": f"Task {uuid.uuid4().hex[:8]}",
                    "priority": random.choice(priorities),
                },
                headers=self._auth(),
                name="/tasks [POST]",
            )
            if res.status_code == 201:
                self.task_ids.append(res.json().get("id", ""))

    @task
    def list_tasks(self):
        if not self.project_id:
            return
        self.client.get(
            f"/api/v1/projects/{self.project_id}/tasks",
            headers=self._auth(),
            name="/tasks [GET]",
        )

    @task
    def list_tasks_filtered(self):
        if not self.project_id:
            return
        self.client.get(
            f"/api/v1/projects/{self.project_id}/tasks?status=todo",
            headers=self._auth(),
            name="/tasks?status=todo [GET]",
        )

    @task
    def update_task_status(self):
        if not self.task_ids:
            return
        task_id = random.choice(self.task_ids)
        statuses = ["todo", "in_progress", "done"]
        self.client.patch(
            f"/api/v1/projects/{self.project_id}/tasks/{task_id}",
            json={"status": random.choice(statuses)},
            headers=self._auth(),
            name="/tasks/:id [PATCH]",
        )

    @task
    def get_analytics(self):
        self.client.get(
            "/api/v1/analytics/me",
            headers=self._auth(),
            name="/analytics/me [GET]",
        )

    @task
    def list_projects(self):
        self.client.get(
            "/api/v1/projects",
            headers=self._auth(),
            name="/projects [GET]",
        )

    @task
    def health_check(self):
        self.client.get("/health", name="/health [GET]")


class APIUser(HttpUser):
    tasks = [TaskManagerFlow]
    wait_time = between(0.5, 2.0)  # Think time between requests


class ReadHeavyUser(HttpUser):
    """
    Simulates a read-heavy user — only lists and gets, no creates.
    Useful for testing cache effectiveness.
    """
    wait_time = between(0.2, 1.0)

    def on_start(self):
        uid = uuid.uuid4().hex[:8]
        email = f"readonly_{uid}@example.com"
        password = "readonly123"
        self.client.post(
            "/api/v1/auth/register",
            json={"email": email, "username": f"ro_{uid}", "password": password},
            name="/auth/register",
        )
        res = self.client.post(
            "/api/v1/auth/login",
            json={"email": email, "password": password},
            name="/auth/login",
        )
        self.token = res.json().get("access_token", "") if res.status_code == 200 else ""

    def _auth(self):
        return {"Authorization": f"Bearer {self.token}"}

    @task(3)
    def list_projects(self):
        self.client.get("/api/v1/projects", headers=self._auth(), name="/projects [GET]")

    @task(1)
    def analytics(self):
        self.client.get("/api/v1/analytics/me", headers=self._auth(), name="/analytics/me [GET]")

    @task(2)
    def health(self):
        self.client.get("/health", name="/health [GET]")
