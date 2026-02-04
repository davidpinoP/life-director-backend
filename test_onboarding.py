
import asyncio
import httpx

async def test_onboarding():
    url = "http://127.0.0.1:8000/auth/login"
    try:
        # Get a token first (assuming the user exist from previous steps)
        # If not, we might need to register.
        async with httpx.AsyncClient() as client:
            resp = await client.post(url, json={"email": "test@example.com", "password": "password123"})
            if resp.status_code != 200:
                # Try register
                resp = await client.post("http://127.0.0.1:8000/auth/register", json={"email": "test@example.com", "password": "password123"})
                resp = await client.post(url, json={"email": "test@example.com", "password": "password123"})
            
            token = resp.json()["access_token"]
            headers = {"Authorization": f"Bearer {token}"}
            
            # Now test onboarding
            onboarding_data = {
                "primary_goal": "Vivir del ecommerce con Shopify",
                "goal_deadline": "6 meses",
                "hours_work": 8,
                "hours_sleep": 7,
                "hours_exercise": 1,
                "main_obstacle": "Falta de foco",
                "peak_energy_time": "morning",
                "current_activities": [
                    {"name": "Trabajo", "hours_per_week": 40, "priority": 10, "aligned_with_goal": False}
                ]
            }
            
            print("Testing POST /onboarding...")
            resp = await client.post("http://127.0.0.1:8000/onboarding", json=onboarding_data, headers=headers)
            print(f"Status: {resp.status_code}")
            print(f"Response: {resp.text}")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_onboarding())
