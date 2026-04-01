from locust import HttpUser, task, between
import random

class AIUser(HttpUser):
    wait_time = between(1, 3)
    
    @task(3)
    def generate_text(self):
        prompts = [
            "Write a story about",
            "Explain quantum computing",
            "What is machine learning",
            "Tell me about AI",
            "How does deep learning work"
        ]
        prompt = random.choice(prompts)
        self.client.post("/api/text/generate", json={
            "prompt": prompt,
            "max_length": 512,
            "temperature": 0.7
        })
    
    @task(2)
    def analyze_image(self):
        # Simulate image upload
        with open('test_image.jpg', 'rb') as f:
            self.client.post("/api/image/analyze", files={'image': f})
    
    @task(1)
    def health_check(self):
        self.client.get("/health")
    
    def on_start(self):
        # Setup code
        pass
    
    def on_stop(self):
        # Cleanup code
        pass
