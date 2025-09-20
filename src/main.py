
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import os
import json
import asyncio
import random
import time
from typing import List, Dict, Optional
from datetime import datetime

app = FastAPI(title="AI vs AI Cyber Battle Platform", version="1.0.0")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files for the frontend
app.mount("/static", StaticFiles(directory="./static"), name="static")

# WebSocket connection manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def send_personal_message(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except:
                pass

manager = ConnectionManager()

# Data Models
class BattleState(BaseModel):
    battle_id: str
    scenario: str
    attacker_persona: str
    defender_persona: str
    current_phase: str
    threat_level: int
    audience_votes: Dict[str, int]
    battle_log: List[Dict]
    is_active: bool

class Achievement(BaseModel):
    id: str
    name: str
    description: str
    category: str
    rarity: str
    unlocked: bool

class UserProfile(BaseModel):
    user_id: str
    username: str
    level: int
    experience: int
    rank_title: str
    achievements: List[Achievement]
    battles_participated: int
    votes_cast: int

# In-memory storage (replace with database in production)
battles: Dict[str, BattleState] = {}
users: Dict[str, UserProfile] = {}
current_battle_id: Optional[str] = None

# AI Personas
ATTACKER_PERSONAS = {
    "script_kiddie": {
        "name": "Script Kiddie",
        "description": "Novice hacker using basic tools",
        "threat_level": 1,
        "techniques": ["Phishing", "Malware", "Social Engineering"]
    },
    "cybercriminal": {
        "name": "Cybercriminal",
        "description": "Organized crime member with moderate skills",
        "threat_level": 3,
        "techniques": ["Ransomware", "Banking Trojans", "Credential Theft"]
    },
    "apt_group": {
        "name": "APT Group",
        "description": "Advanced Persistent Threat with sophisticated methods",
        "threat_level": 7,
        "techniques": ["Zero-day Exploits", "Living off the Land", "Supply Chain Attacks"]
    },
    "insider_threat": {
        "name": "Insider Threat",
        "description": "Malicious employee with privileged access",
        "threat_level": 5,
        "techniques": ["Data Exfiltration", "Privilege Escalation", "Backdoor Installation"]
    },
    "nation_state": {
        "name": "Nation-State Actor",
        "description": "State-sponsored cyber warfare unit",
        "threat_level": 10,
        "techniques": ["Infrastructure Attacks", "Espionage", "Cyber Warfare"]
    }
}

DEFENDER_PERSONAS = {
    "security_analyst": {
        "name": "Security Analyst",
        "description": "Front-line defender monitoring threats",
        "strategy": "Reactive monitoring and incident response"
    },
    "threat_hunter": {
        "name": "Threat Hunter",
        "description": "Proactive threat detection specialist",
        "strategy": "Proactive hunting and threat intelligence"
    },
    "incident_responder": {
        "name": "Incident Responder",
        "description": "Emergency response and containment expert",
        "strategy": "Rapid containment and forensic analysis"
    },
    "security_architect": {
        "name": "Security Architect",
        "description": "Strategic defense planning specialist",
        "strategy": "Defense-in-depth and architectural security"
    },
    "ai_defender": {
        "name": "AI Defender",
        "description": "Machine learning powered defense system",
        "strategy": "Automated threat detection and response"
    }
}

SCENARIOS = {
    "hospital": {
        "name": "Hospital Under Siege",
        "description": "Critical healthcare infrastructure under cyber attack",
        "context": "A major hospital's systems are being targeted, putting patient lives at risk"
    },
    "banking": {
        "name": "Banking Heist",
        "description": "Financial institution facing sophisticated cyber theft",
        "context": "Attackers are attempting to steal millions from a major bank"
    },
    "telecom": {
        "name": "Telecom Blackout",
        "description": "Communication infrastructure disruption attack",
        "context": "National telecommunications grid under coordinated assault"
    },
    "corporate": {
        "name": "Corporate Espionage",
        "description": "Industrial secrets theft from Fortune 500 company",
        "context": "Competitors attempting to steal trade secrets and IP"
    },
    "government": {
        "name": "Government Breach",
        "description": "State secrets and citizen data at risk",
        "context": "Foreign adversaries targeting classified government systems"
    }
}

# API Endpoints
@app.get("/")
async def read_root():
    return HTMLResponse(content="""
    <h1>🚀 AI vs AI Cyber Battle Platform</h1>
    <p>Revolutionary cybersecurity education platform</p>
    <p>API Documentation: <a href="/docs">/docs</a></p>
    """)

@app.get("/api/health")
async def health_check():
    return {"status": "healthy", "message": "AI vs AI Cyber Battle Platform is running!"}

@app.get("/api/scenarios")
async def get_scenarios():
    return {"scenarios": SCENARIOS}

@app.get("/api/personas")
async def get_personas():
    return {
        "attackers": ATTACKER_PERSONAS,
        "defenders": DEFENDER_PERSONAS
    }

@app.post("/api/battle/start")
async def start_battle(scenario: str, attacker: str, defender: str):
    global current_battle_id
    
    battle_id = f"battle_{int(time.time())}"
    current_battle_id = battle_id
    
    battle = BattleState(
        battle_id=battle_id,
        scenario=scenario,
        attacker_persona=attacker,
        defender_persona=defender,
        current_phase="reconnaissance",
        threat_level=1,
        audience_votes={},
        battle_log=[],
        is_active=True
    )
    
    battles[battle_id] = battle
    
    # Broadcast battle start
    await manager.broadcast(json.dumps({
        "type": "battle_started",
        "battle": battle.dict()
    }))
    
    return {"message": "Battle started", "battle_id": battle_id, "battle": battle}

@app.get("/api/battle/current")
async def get_current_battle():
    if current_battle_id and current_battle_id in battles:
        return {"battle": battles[current_battle_id]}
    return {"battle": None}

@app.post("/api/battle/vote")
async def cast_vote(option: str, user_id: str = "anonymous"):
    if not current_battle_id or current_battle_id not in battles:
        raise HTTPException(status_code=404, detail="No active battle")
    
    battle = battles[current_battle_id]
    if option not in battle.audience_votes:
        battle.audience_votes[option] = 0
    battle.audience_votes[option] += 1
    
    # Broadcast vote update
    await manager.broadcast(json.dumps({
        "type": "vote_update",
        "votes": battle.audience_votes
    }))
    
    return {"message": "Vote cast successfully", "votes": battle.audience_votes}

@app.get("/api/achievements")
async def get_achievements():
    achievements = [
        {"id": "first_vote", "name": "First Vote", "description": "Cast your first vote", "category": "participation", "rarity": "common"},
        {"id": "battle_observer", "name": "Battle Observer", "description": "Watch a complete battle", "category": "engagement", "rarity": "common"},
        {"id": "threat_spotter", "name": "Threat Spotter", "description": "Identify 10 attack techniques", "category": "knowledge", "rarity": "uncommon"},
        {"id": "defense_expert", "name": "Defense Expert", "description": "Successfully defend against APT attack", "category": "skill", "rarity": "rare"},
        {"id": "cyber_legend", "name": "Cyber Legend", "description": "Reach level 50", "category": "progression", "rarity": "legendary"}
    ]
    return {"achievements": achievements}

@app.get("/api/leaderboard")
async def get_leaderboard():
    # Mock leaderboard data
    leaderboard = [
        {"rank": 1, "username": "CyberGuardian", "level": 45, "experience": 12500, "battles": 89},
        {"rank": 2, "username": "ThreatHunter", "level": 42, "experience": 11200, "battles": 76},
        {"rank": 3, "username": "SecurityPro", "level": 38, "experience": 9800, "battles": 65},
        {"rank": 4, "username": "DefenseExpert", "level": 35, "experience": 8900, "battles": 58},
        {"rank": 5, "username": "CyberNinja", "level": 33, "experience": 8200, "battles": 52}
    ]
    return {"leaderboard": leaderboard}

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)
            
            if message["type"] == "battle_action":
                # Simulate AI battle progression
                if current_battle_id and current_battle_id in battles:
                    battle = battles[current_battle_id]
                    
                    # Generate AI action based on personas and audience votes
                    action = await generate_ai_action(battle, message.get("user_input"))
                    battle.battle_log.append(action)
                    
                    # Broadcast action to all connected clients
                    await manager.broadcast(json.dumps({
                        "type": "battle_action",
                        "action": action,
                        "battle_state": battle.dict()
                    }))
            
    except WebSocketDisconnect:
        manager.disconnect(websocket)

async def generate_ai_action(battle: BattleState, user_input: Optional[str] = None):
    """Generate AI action based on current battle state and user input"""
    attacker = ATTACKER_PERSONAS[battle.attacker_persona]
    defender = DEFENDER_PERSONAS[battle.defender_persona]
    
    # Simulate AI decision making
    action_type = random.choice(["attack", "defend", "reconnaissance", "escalation"])
    
    if action_type == "attack":
        technique = random.choice(attacker["techniques"])
        action = {
            "timestamp": datetime.now().isoformat(),
            "type": "attack",
            "actor": attacker["name"],
            "technique": technique,
            "description": f"{attacker['name']} launches {technique} attack",
            "threat_level": attacker["threat_level"],
            "success_probability": random.uniform(0.3, 0.9)
        }
    else:
        action = {
            "timestamp": datetime.now().isoformat(),
            "type": "defense",
            "actor": defender["name"],
            "strategy": defender["strategy"],
            "description": f"{defender['name']} implements {defender['strategy']}",
            "effectiveness": random.uniform(0.4, 0.95)
        }
    
    return action

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

