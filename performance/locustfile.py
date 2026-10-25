from locust import HttpUser, task, between


class PythonApiUser(HttpUser):
    wait_time = between(0.5, 1.5)

    @task(3)
    def check_health(self):
        self.client.get("/health")

    @task(2)
    def check_home(self):
        self.client.get("/")

    @task(1)
    def add_numbers(self):
        self.client.post("/add", json={"a": 10, "b": 20})
