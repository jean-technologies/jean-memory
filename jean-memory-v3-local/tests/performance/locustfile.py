"""
Locust load testing configuration for Jean Memory V3 API
Tests the API endpoints under various load conditions

Usage:
    locust -f tests/performance/locustfile.py --host=http://localhost:8766

Load test scenarios:
- Normal usage: 10-50 concurrent users
- Peak usage: 100+ concurrent users  
- Stress test: 200+ concurrent users
"""

import random
import json
from locust import HttpUser, task, between, events
import uuid


class MemoryUser(HttpUser):
    """Simulates a user interacting with Jean Memory V3 API"""
    
    # Wait time between tasks (1-3 seconds)
    wait_time = between(1, 3)
    
    def on_start(self):
        """Called when a user starts - initialize user data"""
        self.user_id = f"load_test_user_{uuid.uuid4().hex[:8]}"
        self.created_memories = []
        self.session_id = None
        
        # Create a session for this user
        self.create_session()
    
    def create_session(self):
        """Create a user session"""
        try:
            response = self.client.post(
                "/sessions/",
                params={"user_id": self.user_id},
                json={"metadata": {"test_type": "load_test"}}
            )
            if response.status_code == 200:
                self.session_id = response.json().get("session_id")
        except Exception as e:
            print(f"Failed to create session: {e}")
    
    @task(3)
    def create_memory(self):
        """Create a new memory (most common operation)"""
        memory_content = self._generate_memory_content()
        
        response = self.client.post(
            "/memories/",
            json={
                "content": memory_content,
                "user_id": self.user_id,
                "metadata": {
                    "category": random.choice(["work", "personal", "learning", "todo"]),
                    "priority": random.choice(["low", "medium", "high"]),
                    "source": "load_test"
                }
            }
        )
        
        if response.status_code == 200:
            memory_data = response.json()
            self.created_memories.append(memory_data["id"])
            
        return response
    
    @task(2)
    def search_memories(self):
        """Search for memories (second most common operation)"""
        search_queries = [
            "important meeting",
            "project deadline", 
            "team collaboration",
            "personal goals",
            "learning notes",
            "follow up",
            "reminder",
            "documentation"
        ]
        
        query = random.choice(search_queries)
        
        response = self.client.get(
            "/memories/search",
            params={
                "query": query,
                "user_id": self.user_id,
                "limit": random.randint(5, 20),
                "threshold": random.uniform(0.3, 0.8)
            }
        )
        
        return response
    
    @task(1)
    def get_specific_memory(self):
        """Get a specific memory by ID"""
        if not self.created_memories:
            return
            
        memory_id = random.choice(self.created_memories)
        
        response = self.client.get(
            f"/memories/{memory_id}",
            params={"user_id": self.user_id}
        )
        
        return response
    
    @task(1)
    def get_stats(self):
        """Get user statistics"""
        response = self.client.get(
            "/stats",
            params={"user_id": self.user_id}
        )
        
        return response
    
    @task(1)
    def check_health(self):
        """Check service health"""
        response = self.client.get("/health")
        return response
    
    def _generate_memory_content(self):
        """Generate realistic memory content for testing"""
        content_templates = [
            "Had a productive meeting with {team} about {topic}. Key takeaways: {details}",
            "Need to follow up on {task} by {date}. Priority: {priority}",
            "Learned about {concept} today. Important points: {details}",
            "Personal reminder: {task} scheduled for {date}",
            "Project {project} update: {status}. Next steps: {details}",
            "Meeting notes from {meeting}: {details}",
            "Research findings on {topic}: {details}",
            "Action item: {task}. Assigned to: {person}. Due: {date}"
        ]
        
        # Sample data for templates
        teams = ["engineering", "product", "design", "marketing", "sales"]
        topics = ["Q1 planning", "feature development", "bug fixes", "user feedback", "roadmap"]
        tasks = ["code review", "documentation", "testing", "deployment", "research"]
        dates = ["next week", "Friday", "end of month", "Q1", "tomorrow"]
        priorities = ["high", "medium", "low"]
        concepts = ["machine learning", "API design", "user experience", "performance optimization"]
        projects = ["Project Alpha", "Beta Release", "Customer Portal", "Mobile App"]
        statuses = ["on track", "delayed", "completed", "blocked"]
        people = ["John", "Sarah", "Mike", "Lisa", "Tom"]
        
        template = random.choice(content_templates)
        
        # Fill in template with random data
        content = template.format(
            team=random.choice(teams),
            topic=random.choice(topics),
            task=random.choice(tasks),
            date=random.choice(dates),
            priority=random.choice(priorities),
            details=f"Detail {random.randint(1, 100)}",
            concept=random.choice(concepts),
            project=random.choice(projects),
            status=random.choice(statuses),
            meeting=f"Meeting {random.randint(1, 50)}",
            person=random.choice(people)
        )
        
        return content


class IntensiveMemoryUser(MemoryUser):
    """More intensive user that creates more load"""
    
    wait_time = between(0.5, 1.5)  # Faster operations
    
    @task(5)
    def create_memory(self):
        """Create memories more frequently"""
        return super().create_memory()
    
    @task(4)
    def search_memories(self):
        """Search more frequently"""
        return super().search_memories()
    
    @task(2)
    def rapid_search_sequence(self):
        """Perform multiple searches in sequence"""
        queries = ["meeting", "project", "task", "important", "urgent"]
        
        for query in queries:
            response = self.client.get(
                "/memories/search",
                params={
                    "query": query,
                    "user_id": self.user_id,
                    "limit": 5,
                    "threshold": 0.5
                }
            )
            
            if response.status_code != 200:
                break


class AdminUser(HttpUser):
    """Simulates admin operations"""
    
    wait_time = between(5, 10)  # Slower, periodic operations
    
    def on_start(self):
        self.user_id = f"admin_user_{uuid.uuid4().hex[:8]}"
    
    @task(1)
    def get_global_stats(self):
        """Get global system statistics"""
        response = self.client.get("/stats")
        return response
    
    @task(1)
    def check_shuttle_stats(self):
        """Check memory shuttle statistics"""
        response = self.client.get(
            "/shuttle/stats",
            params={"user_id": self.user_id}
        )
        return response
    
    @task(1)
    def force_sync(self):
        """Force sync to LTM"""
        response = self.client.post(
            "/shuttle/sync",
            params={"user_id": self.user_id}
        )
        return response


# Custom load test scenarios
@events.test_start.add_listener
def on_test_start(environment, **kwargs):
    """Called when the test starts"""
    print("🚀 Starting Jean Memory V3 Load Test")
    print(f"Target host: {environment.host}")


@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    """Called when the test stops"""
    print("✅ Jean Memory V3 Load Test completed")
    
    # Print summary statistics
    if environment.stats.total.num_requests > 0:
        print(f"\n📊 Load Test Summary:")
        print(f"Total requests: {environment.stats.total.num_requests}")
        print(f"Failed requests: {environment.stats.total.num_failures}")
        print(f"Average response time: {environment.stats.total.avg_response_time:.2f}ms")
        print(f"95th percentile: {environment.stats.total.get_response_time_percentile(0.95):.2f}ms")
        print(f"Requests per second: {environment.stats.total.current_rps:.2f}")


# Load test patterns for different scenarios
class NormalUsageUser(MemoryUser):
    """Normal usage pattern - 10-50 concurrent users"""
    weight = 3
    wait_time = between(2, 5)


class PeakUsageUser(IntensiveMemoryUser):
    """Peak usage pattern - higher frequency operations"""
    weight = 2
    wait_time = between(1, 3)


class BurstUser(MemoryUser):
    """Simulates burst traffic patterns"""
    weight = 1
    wait_time = between(0.1, 0.5)  # Very fast bursts
    
    @task(10)
    def create_memory_burst(self):
        """Create multiple memories in quick succession"""
        for i in range(3):
            super().create_memory()


# Example load test configurations:

# 1. Normal Load Test:
# locust -f locustfile.py --host=http://localhost:8766 -u 25 -r 5 -t 5m

# 2. Peak Load Test:
# locust -f locustfile.py --host=http://localhost:8766 -u 100 -r 10 -t 10m

# 3. Stress Test:
# locust -f locustfile.py --host=http://localhost:8766 -u 200 -r 20 -t 15m

# 4. Endurance Test:
# locust -f locustfile.py --host=http://localhost:8766 -u 50 -r 5 -t 60m