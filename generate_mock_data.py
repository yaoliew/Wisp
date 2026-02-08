"""
Generate believable mock call data for the past 3 months
Each transcript will be unique
"""
import asyncio
import aiosqlite
import random
from datetime import datetime, timedelta
from typing import List, Dict, Any

DB_PATH = "wisp_calls.db"

# Mock phone numbers
AREA_CODES = ["212", "310", "415", "617", "312", "404", "713", "214", "206", "303"]
PHONE_NUMBERS = [f"+1{area}{random.randint(1000000, 9999999)}" for area in AREA_CODES for _ in range(10)]

# Scam scenarios with unique variations
SCAM_SCENARIOS = [
    {
        "category": "IRS Scam",
        "templates": [
            "Hello, this is {agent} from the Internal Revenue Service. We have been trying to reach you regarding an outstanding tax debt of ${amount}. If you do not pay immediately, we will issue a warrant for your arrest.",
            "This is {agent} calling from the IRS. Your social security number has been flagged for suspicious activity. You need to verify your identity by providing your bank account information.",
            "IRS here. We've identified fraudulent tax returns filed under your name. To resolve this, you must pay ${amount} in back taxes immediately using gift cards.",
        ]
    },
    {
        "category": "Tech Support Scam",
        "templates": [
            "Hello, this is {agent} from Microsoft Technical Support. We've detected a virus on your computer. We need remote access to fix it immediately.",
            "This is {agent} from Apple Support. Your iCloud account has been compromised. We need your password to secure it.",
            "Windows Security calling. Your computer is sending out malicious software. We can fix this for ${amount} if you provide your credit card now.",
        ]
    },
    {
        "category": "Bank Fraud",
        "templates": [
            "This is {agent} from {bank} Security Department. We've detected unusual activity on your account. We need to verify your account number and PIN.",
            "{bank} Fraud Prevention here. Someone tried to withdraw ${amount} from your account. To stop this, we need your full account details.",
            "This is {agent} calling from {bank}. Your account has been frozen due to suspicious transactions. Please provide your social security number to unlock it.",
        ]
    },
    {
        "category": "Phishing",
        "templates": [
            "Congratulations! You've won ${amount} in our lottery. To claim your prize, we need your bank account information for the wire transfer.",
            "You've been selected for a government grant of ${amount}. We just need your social security number and date of birth to process it.",
            "This is {agent} from the Social Security Administration. Your benefits have been suspended. Call us back immediately at this number to reactivate.",
        ]
    },
    {
        "category": "Romance Scam",
        "templates": [
            "Hi, this is {agent}. We met online last week. I'm stuck in {location} and need ${amount} for a plane ticket home. Can you help me?",
            "Hello, it's {agent}. I'm in the hospital in {location} and need money for surgery. Can you wire ${amount} to my account?",
        ]
    },
]

# Safe call scenarios
SAFE_SCENARIOS = [
    "Hello, this is {agent} from {company}. We're calling to confirm your appointment tomorrow at 2 PM.",
    "Hi, this is {agent} from {company} customer service. We're following up on your recent order. Is everything working well?",
    "This is {agent} from {company}. We wanted to let you know your package will be delivered today between 2-4 PM.",
    "Hello, {agent} here from {company}. We're conducting a customer satisfaction survey. Do you have 5 minutes?",
    "Hi, this is {agent} calling from {company}. We noticed you haven't used our service in a while. We'd love to have you back!",
    "This is {agent} from {company} billing. We're calling to remind you that your payment is due next week.",
    "Hello, {agent} here. I'm calling to schedule a follow-up appointment for your recent visit.",
    "Hi, this is {agent} from {company}. We're reaching out to offer you a special discount on our services.",
]

COMPANIES = ["Amazon", "Apple", "Microsoft", "Google", "Netflix", "Spotify", "Uber", "Lyft", "DoorDash", "Instacart"]
LOCATIONS = ["London", "Paris", "Tokyo", "Sydney", "Dubai", "Singapore", "Toronto", "Mexico City"]
AGENT_NAMES = ["John", "Sarah", "Michael", "Emily", "David", "Jessica", "Robert", "Amanda", "James", "Lisa", "William", "Ashley"]

def generate_unique_transcript(scenario_type: str, index: int) -> str:
    """Generate a unique transcript based on scenario type"""
    if scenario_type == "SCAM":
        scenario = random.choice(SCAM_SCENARIOS)
        template = random.choice(scenario["templates"])
        
        # Make it unique by varying the details
        agent = random.choice(AGENT_NAMES)
        amount = random.randint(500, 50000)
        bank = random.choice(["Chase", "Bank of America", "Wells Fargo", "Citibank"])
        location = random.choice(LOCATIONS)
        
        # Add unique identifier
        unique_id = f"REF-{random.randint(1000, 9999)}-{index}"
        
        transcript = template.format(
            agent=agent,
            amount=amount,
            bank=bank,
            location=location
        )
        
        # Add some variation
        variations = [
            f"\n\nCaller: {transcript}\n\nAI Assistant: I understand. Can you provide me with a reference number?\n\nCaller: Yes, it's {unique_id}.",
            f"\n\nCaller: {transcript}\n\nAI Assistant: I see. When did you first notice this issue?\n\nCaller: It started about {random.randint(1, 7)} days ago.",
            f"\n\nCaller: {transcript}\n\nAI Assistant: Can you verify your account information?\n\nCaller: My account number is {random.randint(100000, 999999)}.",
        ]
        
        return transcript + random.choice(variations)
    
    else:  # SAFE
        template = random.choice(SAFE_SCENARIOS)
        agent = random.choice(AGENT_NAMES)
        company = random.choice(COMPANIES)
        
        # Add unique details
        unique_details = [
            f"\n\nCaller: {template.format(agent=agent, company=company)}\n\nAI Assistant: Thank you for calling. How can I assist you today?\n\nCaller: I wanted to confirm the details.",
            f"\n\nCaller: {template.format(agent=agent, company=company)}\n\nAI Assistant: I'd be happy to help. Let me pull up your account.\n\nCaller: Great, my account number is {random.randint(100000, 999999)}.",
            f"\n\nCaller: {template.format(agent=agent, company=company)}\n\nAI Assistant: Of course. Is there anything specific you'd like to know?\n\nCaller: Yes, I have a few questions about my account.",
        ]
        
        return random.choice(unique_details)

def generate_call_summary(transcript: str, verdict: str) -> str:
    """Generate a brief summary based on transcript and verdict"""
    if verdict == "SCAM":
        if "IRS" in transcript or "tax" in transcript.lower():
            return "Caller claims to be from IRS demanding immediate payment"
        elif "Microsoft" in transcript or "Windows" in transcript or "virus" in transcript.lower():
            return "Tech support scam - claims computer has virus"
        elif "bank" in transcript.lower() or "account" in transcript.lower():
            return "Bank fraud attempt - requesting account information"
        elif "won" in transcript.lower() or "lottery" in transcript.lower() or "grant" in transcript.lower():
            return "Phishing scam - fake prize or grant offer"
        elif "stuck" in transcript.lower() or "hospital" in transcript.lower():
            return "Romance scam - requesting emergency funds"
        else:
            return "Suspicious call requesting personal information"
    else:
        return "Legitimate business call - customer service or appointment"

async def generate_mock_calls(num_calls: int = 200) -> List[Dict[str, Any]]:
    """Generate mock call data for the past 3 months"""
    calls = []
    now = datetime.utcnow()
    start_date = now - timedelta(days=90)  # 3 months ago
    
    # Distribution: 60% SCAM, 30% SAFE, 10% no verdict (SUSPICIOUS)
    verdict_distribution = ["SCAM"] * 120 + ["SAFE"] * 60 + [None] * 20
    
    for i in range(num_calls):
        # Random date within the past 3 months
        days_ago = random.randint(0, 90)
        started_at = start_date + timedelta(days=days_ago, hours=random.randint(0, 23), minutes=random.randint(0, 59))
        
        # Random duration between 30 seconds and 10 minutes
        duration_seconds = random.randint(30, 600)
        ended_at = started_at + timedelta(seconds=duration_seconds)
        
        # Random verdict
        verdict = random.choice(verdict_distribution)
        
        # Generate unique transcript
        if verdict == "SCAM":
            transcript = generate_unique_transcript("SCAM", i)
        elif verdict == "SAFE":
            transcript = generate_unique_transcript("SAFE", i)
        else:
            # Suspicious - mix of both
            transcript = generate_unique_transcript(random.choice(["SCAM", "SAFE"]), i)
        
        summary = generate_call_summary(transcript, verdict or "SUSPICIOUS")
        
        # Random phone numbers
        from_number = random.choice(PHONE_NUMBERS)
        to_number = "+14702282477"  # Wisp phone number
        
        # Status
        if verdict == "SCAM":
            status = "terminated"
            terminated_at = started_at + timedelta(seconds=random.randint(30, 120))
        else:
            status = "ended"
            terminated_at = None
        
        call_data = {
            "call_id": f"call_{i}_{int(started_at.timestamp())}",
            "from_number": from_number,
            "to_number": to_number,
            "started_at": started_at.isoformat(),
            "status": status,
            "screening_verdict": verdict,
            "screening_summary": summary,
            "screened_at": (started_at + timedelta(seconds=random.randint(10, 60))).isoformat(),
            "transcript": transcript,
            "terminated_at": terminated_at.isoformat() if terminated_at else None,
            "transfer_initiated": 0 if verdict == "SCAM" else (1 if verdict == "SAFE" else 0),
            "transfer_target": None if verdict == "SCAM" else to_number,
            "transfer_initiated_at": None if verdict == "SCAM" else (started_at + timedelta(seconds=random.randint(60, 180))).isoformat(),
            "transferred_to": None if verdict == "SCAM" else to_number,
            "transferred_at": None if verdict == "SCAM" else (started_at + timedelta(seconds=random.randint(120, 300))).isoformat(),
            "ended_at": ended_at.isoformat(),
            "created_at": started_at.isoformat(),
            "updated_at": ended_at.isoformat(),
        }
        
        calls.append(call_data)
    
    return calls

async def insert_mock_data():
    """Insert mock data into the database"""
    print("Generating mock call data...")
    calls = await generate_mock_calls(200)
    
    print(f"Generated {len(calls)} mock calls")
    print("Inserting into database...")
    
    async with aiosqlite.connect(DB_PATH) as db:
        for i, call in enumerate(calls):
            try:
                await db.execute("""
                    INSERT OR REPLACE INTO calls (
                        call_id, from_number, to_number, started_at, status,
                        screening_verdict, screening_summary, screened_at, transcript,
                        terminated_at, transfer_initiated, transfer_target, transfer_initiated_at,
                        transferred_to, transferred_at, ended_at, created_at, updated_at
                    ) VALUES (
                        :call_id, :from_number, :to_number, :started_at, :status,
                        :screening_verdict, :screening_summary, :screened_at, :transcript,
                        :terminated_at, :transfer_initiated, :transfer_target, :transfer_initiated_at,
                        :transferred_to, :transferred_at, :ended_at, :created_at, :updated_at
                    )
                """, {
                    "call_id": call.get("call_id"),
                    "from_number": call.get("from_number"),
                    "to_number": call.get("to_number"),
                    "started_at": call.get("started_at"),
                    "status": call.get("status"),
                    "screening_verdict": call.get("screening_verdict"),
                    "screening_summary": call.get("screening_summary"),
                    "screened_at": call.get("screened_at"),
                    "transcript": call.get("transcript"),
                    "terminated_at": call.get("terminated_at"),
                    "transfer_initiated": 1 if call.get("transfer_initiated") else 0,
                    "transfer_target": call.get("transfer_target"),
                    "transfer_initiated_at": call.get("transfer_initiated_at"),
                    "transferred_to": call.get("transferred_to"),
                    "transferred_at": call.get("transferred_at"),
                    "ended_at": call.get("ended_at"),
                    "created_at": call.get("created_at"),
                    "updated_at": call.get("updated_at")
                })
                
                if (i + 1) % 50 == 0:
                    print(f"Inserted {i + 1}/{len(calls)} calls...")
                    await db.commit()
            except Exception as e:
                print(f"Error inserting call {call.get('call_id')}: {e}")
        
        await db.commit()
        print(f"Successfully inserted {len(calls)} mock calls into database!")
        
        # Print some statistics
        async with db.execute("SELECT COUNT(*) FROM calls") as cursor:
            total = (await cursor.fetchone())[0]
            print(f"Total calls in database: {total}")
        
        async with db.execute("SELECT COUNT(*) FROM calls WHERE screening_verdict = 'SCAM'") as cursor:
            scams = (await cursor.fetchone())[0]
            print(f"Scam calls: {scams}")
        
        async with db.execute("SELECT COUNT(*) FROM calls WHERE screening_verdict = 'SAFE'") as cursor:
            safe = (await cursor.fetchone())[0]
            print(f"Safe calls: {safe}")

if __name__ == "__main__":
    asyncio.run(insert_mock_data())
