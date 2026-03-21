from fastapi import FastAPI, APIRouter, HTTPException, Depends, status, WebSocket, WebSocketDisconnect
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional, Dict
import uuid
from datetime import datetime, timezone, timedelta
import hashlib
import secrets
import asyncio
import json

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Create the main app
app = FastAPI(title="Lifecycle Bot Dashboard API")

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# Security
security = HTTPBearer(auto_error=False)
SECRET_KEY = os.environ.get('SECRET_KEY', secrets.token_hex(32))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ═══════════════════════════════════════════════════════════════════
# Models
# ═══════════════════════════════════════════════════════════════════

class UserCreate(BaseModel):
    username: str
    password: str

class UserLogin(BaseModel):
    username: str
    password: str

class TokenResponse(BaseModel):
    token: str
    username: str

class BotStatus(BaseModel):
    model_config = ConfigDict(extra="ignore")
    bot_id: str = "default"
    is_running: bool = False
    mode: str = "PAUSED"  # PAUSED, LAUNCH_SNIPE, RANGE_TRADE, AUTO
    wallet_address: Optional[str] = None
    last_heartbeat: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    scan_count: int = 0
    active_tokens: int = 0

class BotStatusUpdate(BaseModel):
    is_running: bool
    mode: str
    wallet_address: Optional[str] = None
    scan_count: int = 0
    active_tokens: int = 0

class TreasurySnapshot(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    treasury_sol: float
    treasury_usd: float
    sol_price: float

class Position(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    mint: str
    symbol: str
    entry_price: float
    entry_time: datetime
    qty_token: float
    cost_sol: float
    current_price: float = 0.0
    current_value_sol: float = 0.0
    unrealized_pnl_pct: float = 0.0
    phase: str = "unknown"
    signal: str = "WAIT"
    entry_score: float = 0.0
    exit_score: float = 0.0

class PositionUpdate(BaseModel):
    mint: str
    symbol: str
    entry_price: float
    entry_time: datetime
    qty_token: float
    cost_sol: float
    current_price: float = 0.0
    current_value_sol: float = 0.0
    unrealized_pnl_pct: float = 0.0
    phase: str = "unknown"
    signal: str = "WAIT"
    entry_score: float = 0.0
    exit_score: float = 0.0

class Trade(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    mint: str
    symbol: str
    entry_price: float
    exit_price: float
    entry_time: datetime
    exit_time: datetime
    qty_token: float
    cost_sol: float
    revenue_sol: float
    pnl_sol: float
    pnl_pct: float
    is_win: bool
    phase_at_entry: str
    phase_at_exit: str
    hold_duration_mins: float

class TradeCreate(BaseModel):
    mint: str
    symbol: str
    entry_price: float
    exit_price: float
    entry_time: datetime
    exit_time: datetime
    qty_token: float
    cost_sol: float
    revenue_sol: float
    pnl_sol: float
    pnl_pct: float
    is_win: bool
    phase_at_entry: str = ""
    phase_at_exit: str = ""
    hold_duration_mins: float = 0.0

class ActivityLog(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    type: str  # TRADE, SCAN, SIGNAL, ERROR, INFO
    message: str
    mint: Optional[str] = None
    symbol: Optional[str] = None

class ActivityLogCreate(BaseModel):
    type: str
    message: str
    mint: Optional[str] = None
    symbol: Optional[str] = None

class WatchlistToken(BaseModel):
    model_config = ConfigDict(extra="ignore")
    mint: str
    symbol: str
    current_price: float
    price_change_1h: float = 0.0
    volume_24h: float = 0.0
    liquidity_usd: float = 0.0
    holder_count: int = 0
    phase: str = "unknown"
    signal: str = "WAIT"
    entry_score: float = 0.0
    exit_score: float = 0.0
    last_update: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class DashboardStats(BaseModel):
    treasury_sol: float = 0.0
    treasury_usd: float = 0.0
    total_pnl_sol: float = 0.0
    total_pnl_pct: float = 0.0
    total_trades: int = 0
    win_count: int = 0
    loss_count: int = 0
    win_rate: float = 0.0
    avg_win_pct: float = 0.0
    avg_loss_pct: float = 0.0
    open_positions: int = 0
    bot_running: bool = False
    bot_mode: str = "PAUSED"

class BulkDataPush(BaseModel):
    """For Android app to push all data at once"""
    bot_status: Optional[BotStatusUpdate] = None
    treasury: Optional[TreasurySnapshot] = None
    positions: Optional[List[PositionUpdate]] = None
    new_trades: Optional[List[TradeCreate]] = None
    activity_logs: Optional[List[ActivityLogCreate]] = None
    watchlist: Optional[List[WatchlistToken]] = None

# ═══════════════════════════════════════════════════════════════════
# Auth Helpers
# ═══════════════════════════════════════════════════════════════════

def hash_password(password: str) -> str:
    return hashlib.sha256((password + SECRET_KEY).encode()).hexdigest()

def create_token(username: str) -> str:
    token_data = f"{username}:{secrets.token_hex(16)}:{datetime.now(timezone.utc).isoformat()}"
    return hashlib.sha256((token_data + SECRET_KEY).encode()).hexdigest()

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    if not credentials:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    token = credentials.credentials
    session = await db.sessions.find_one({"token": token}, {"_id": 0})
    if not session:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    return session["username"]

# ═══════════════════════════════════════════════════════════════════
# Auth Routes
# ═══════════════════════════════════════════════════════════════════

@api_router.post("/auth/register", response_model=TokenResponse)
async def register(user: UserCreate):
    existing = await db.users.find_one({"username": user.username})
    if existing:
        raise HTTPException(status_code=400, detail="Username already exists")
    
    hashed = hash_password(user.password)
    await db.users.insert_one({
        "username": user.username,
        "password": hashed,
        "created_at": datetime.now(timezone.utc).isoformat()
    })
    
    token = create_token(user.username)
    await db.sessions.insert_one({
        "username": user.username,
        "token": token,
        "created_at": datetime.now(timezone.utc).isoformat()
    })
    
    return TokenResponse(token=token, username=user.username)

@api_router.post("/auth/login", response_model=TokenResponse)
async def login(user: UserLogin):
    hashed = hash_password(user.password)
    existing = await db.users.find_one({"username": user.username, "password": hashed})
    if not existing:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    token = create_token(user.username)
    await db.sessions.update_one(
        {"username": user.username},
        {"$set": {"token": token, "updated_at": datetime.now(timezone.utc).isoformat()}},
        upsert=True
    )
    
    return TokenResponse(token=token, username=user.username)

@api_router.get("/auth/me")
async def get_me(username: str = Depends(get_current_user)):
    return {"username": username}

# ═══════════════════════════════════════════════════════════════════
# Bot Status Routes
# ═══════════════════════════════════════════════════════════════════

@api_router.get("/bot/status", response_model=BotStatus)
async def get_bot_status(username: str = Depends(get_current_user)):
    status = await db.bot_status.find_one({"bot_id": "default"}, {"_id": 0})
    if not status:
        return BotStatus()
    
    if isinstance(status.get('last_heartbeat'), str):
        status['last_heartbeat'] = datetime.fromisoformat(status['last_heartbeat'])
    return BotStatus(**status)

@api_router.post("/bot/status")
async def update_bot_status(update: BotStatusUpdate, username: str = Depends(get_current_user)):
    doc = update.model_dump()
    doc['bot_id'] = "default"
    doc['last_heartbeat'] = datetime.now(timezone.utc).isoformat()
    
    await db.bot_status.update_one(
        {"bot_id": "default"},
        {"$set": doc},
        upsert=True
    )
    return {"status": "updated"}

# ═══════════════════════════════════════════════════════════════════
# Treasury Routes
# ═══════════════════════════════════════════════════════════════════

@api_router.get("/treasury/history", response_model=List[TreasurySnapshot])
async def get_treasury_history(
    days: int = 30,
    username: str = Depends(get_current_user)
):
    cutoff = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()
    snapshots = await db.treasury_history.find(
        {"timestamp": {"$gte": cutoff}},
        {"_id": 0}
    ).sort("timestamp", 1).to_list(1000)
    
    for s in snapshots:
        if isinstance(s.get('timestamp'), str):
            s['timestamp'] = datetime.fromisoformat(s['timestamp'])
    return snapshots

@api_router.post("/treasury/snapshot")
async def add_treasury_snapshot(snapshot: TreasurySnapshot, username: str = Depends(get_current_user)):
    doc = snapshot.model_dump()
    doc['timestamp'] = doc['timestamp'].isoformat()
    await db.treasury_history.insert_one(doc)
    
    # Update current treasury
    await db.treasury_current.update_one(
        {"_type": "current"},
        {"$set": {
            "treasury_sol": snapshot.treasury_sol,
            "treasury_usd": snapshot.treasury_usd,
            "sol_price": snapshot.sol_price,
            "updated_at": doc['timestamp']
        }},
        upsert=True
    )
    return {"status": "recorded"}

# ═══════════════════════════════════════════════════════════════════
# Positions Routes
# ═══════════════════════════════════════════════════════════════════

@api_router.get("/positions", response_model=List[Position])
async def get_positions(username: str = Depends(get_current_user)):
    positions = await db.positions.find({}, {"_id": 0}).to_list(100)
    for p in positions:
        if isinstance(p.get('entry_time'), str):
            p['entry_time'] = datetime.fromisoformat(p['entry_time'])
    return positions

@api_router.post("/positions/sync")
async def sync_positions(positions: List[PositionUpdate], username: str = Depends(get_current_user)):
    # Clear old positions and insert new ones
    await db.positions.delete_many({})
    
    for pos in positions:
        doc = pos.model_dump()
        doc['id'] = str(uuid.uuid4())
        doc['entry_time'] = doc['entry_time'].isoformat()
        await db.positions.insert_one(doc)
    
    return {"status": "synced", "count": len(positions)}

@api_router.delete("/positions/{mint}")
async def close_position(mint: str, username: str = Depends(get_current_user)):
    result = await db.positions.delete_one({"mint": mint})
    return {"deleted": result.deleted_count > 0}

# ═══════════════════════════════════════════════════════════════════
# Trade History Routes
# ═══════════════════════════════════════════════════════════════════

@api_router.get("/trades", response_model=List[Trade])
async def get_trades(
    limit: int = 100,
    offset: int = 0,
    username: str = Depends(get_current_user)
):
    trades = await db.trades.find({}, {"_id": 0}).sort("exit_time", -1).skip(offset).limit(limit).to_list(limit)
    for t in trades:
        if isinstance(t.get('entry_time'), str):
            t['entry_time'] = datetime.fromisoformat(t['entry_time'])
        if isinstance(t.get('exit_time'), str):
            t['exit_time'] = datetime.fromisoformat(t['exit_time'])
    return trades

@api_router.post("/trades", response_model=Trade)
async def record_trade(trade: TradeCreate, username: str = Depends(get_current_user)):
    doc = trade.model_dump()
    doc['id'] = str(uuid.uuid4())
    doc['entry_time'] = doc['entry_time'].isoformat()
    doc['exit_time'] = doc['exit_time'].isoformat()
    
    await db.trades.insert_one(doc)
    
    # Log activity
    await db.activity_logs.insert_one({
        "id": str(uuid.uuid4()),
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "type": "TRADE",
        "message": f"{'WIN' if trade.is_win else 'LOSS'} {trade.symbol}: {trade.pnl_pct:+.1f}% ({trade.pnl_sol:+.4f} SOL)",
        "mint": trade.mint,
        "symbol": trade.symbol
    })
    
    doc['entry_time'] = trade.entry_time
    doc['exit_time'] = trade.exit_time
    return Trade(**doc)

@api_router.get("/trades/stats")
async def get_trade_stats(username: str = Depends(get_current_user)):
    trades = await db.trades.find({}, {"_id": 0}).to_list(10000)
    
    if not trades:
        return {
            "total_trades": 0,
            "win_count": 0,
            "loss_count": 0,
            "win_rate": 0.0,
            "total_pnl_sol": 0.0,
            "avg_win_pct": 0.0,
            "avg_loss_pct": 0.0,
            "best_trade_pct": 0.0,
            "worst_trade_pct": 0.0,
            "avg_hold_mins": 0.0
        }
    
    wins = [t for t in trades if t.get('is_win')]
    losses = [t for t in trades if not t.get('is_win')]
    
    return {
        "total_trades": len(trades),
        "win_count": len(wins),
        "loss_count": len(losses),
        "win_rate": len(wins) / len(trades) * 100 if trades else 0,
        "total_pnl_sol": sum(t.get('pnl_sol', 0) for t in trades),
        "avg_win_pct": sum(t.get('pnl_pct', 0) for t in wins) / len(wins) if wins else 0,
        "avg_loss_pct": sum(t.get('pnl_pct', 0) for t in losses) / len(losses) if losses else 0,
        "best_trade_pct": max((t.get('pnl_pct', 0) for t in trades), default=0),
        "worst_trade_pct": min((t.get('pnl_pct', 0) for t in trades), default=0),
        "avg_hold_mins": sum(t.get('hold_duration_mins', 0) for t in trades) / len(trades) if trades else 0
    }

# ═══════════════════════════════════════════════════════════════════
# Activity Log Routes
# ═══════════════════════════════════════════════════════════════════

@api_router.get("/activity", response_model=List[ActivityLog])
async def get_activity(
    limit: int = 50,
    username: str = Depends(get_current_user)
):
    logs = await db.activity_logs.find({}, {"_id": 0}).sort("timestamp", -1).limit(limit).to_list(limit)
    for l in logs:
        if isinstance(l.get('timestamp'), str):
            l['timestamp'] = datetime.fromisoformat(l['timestamp'])
    return logs

@api_router.post("/activity")
async def log_activity(log: ActivityLogCreate, username: str = Depends(get_current_user)):
    doc = log.model_dump()
    doc['id'] = str(uuid.uuid4())
    doc['timestamp'] = datetime.now(timezone.utc).isoformat()
    await db.activity_logs.insert_one(doc)
    return {"status": "logged"}

# ═══════════════════════════════════════════════════════════════════
# Watchlist Routes
# ═══════════════════════════════════════════════════════════════════

@api_router.get("/watchlist", response_model=List[WatchlistToken])
async def get_watchlist(username: str = Depends(get_current_user)):
    tokens = await db.watchlist.find({}, {"_id": 0}).to_list(100)
    for t in tokens:
        if isinstance(t.get('last_update'), str):
            t['last_update'] = datetime.fromisoformat(t['last_update'])
    return tokens

@api_router.post("/watchlist/sync")
async def sync_watchlist(tokens: List[WatchlistToken], username: str = Depends(get_current_user)):
    await db.watchlist.delete_many({})
    for token in tokens:
        doc = token.model_dump()
        doc['last_update'] = doc['last_update'].isoformat()
        await db.watchlist.insert_one(doc)
    return {"status": "synced", "count": len(tokens)}

# ═══════════════════════════════════════════════════════════════════
# Dashboard Aggregate Route
# ═══════════════════════════════════════════════════════════════════

@api_router.get("/dashboard", response_model=DashboardStats)
async def get_dashboard_stats(username: str = Depends(get_current_user)):
    # Get current treasury
    treasury = await db.treasury_current.find_one({"_type": "current"}, {"_id": 0})
    
    # Get trade stats
    trades = await db.trades.find({}, {"_id": 0}).to_list(10000)
    wins = [t for t in trades if t.get('is_win')]
    losses = [t for t in trades if not t.get('is_win')]
    
    # Get position count
    position_count = await db.positions.count_documents({})
    
    # Get bot status
    bot_status = await db.bot_status.find_one({"bot_id": "default"}, {"_id": 0})
    
    total_pnl = sum(t.get('pnl_sol', 0) for t in trades)
    initial_treasury = (treasury.get('treasury_sol', 0) if treasury else 0) - total_pnl
    
    return DashboardStats(
        treasury_sol=treasury.get('treasury_sol', 0) if treasury else 0,
        treasury_usd=treasury.get('treasury_usd', 0) if treasury else 0,
        total_pnl_sol=total_pnl,
        total_pnl_pct=(total_pnl / initial_treasury * 100) if initial_treasury > 0 else 0,
        total_trades=len(trades),
        win_count=len(wins),
        loss_count=len(losses),
        win_rate=len(wins) / len(trades) * 100 if trades else 0,
        avg_win_pct=sum(t.get('pnl_pct', 0) for t in wins) / len(wins) if wins else 0,
        avg_loss_pct=sum(t.get('pnl_pct', 0) for t in losses) / len(losses) if losses else 0,
        open_positions=position_count,
        bot_running=bot_status.get('is_running', False) if bot_status else False,
        bot_mode=bot_status.get('mode', 'PAUSED') if bot_status else 'PAUSED'
    )

# ═══════════════════════════════════════════════════════════════════
# Bulk Data Push (for Android App)
# ═══════════════════════════════════════════════════════════════════

@api_router.post("/sync/bulk")
async def bulk_data_push(data: BulkDataPush, username: str = Depends(get_current_user)):
    results = {}
    
    # Get user_id for WebSocket notifications
    user = await db.users.find_one({"username": username})
    user_id = str(user["_id"]) if user else username
    
    if data.bot_status:
        doc = data.bot_status.model_dump()
        doc['bot_id'] = "default"
        doc['user_id'] = user_id
        doc['last_heartbeat'] = datetime.now(timezone.utc).isoformat()
        await db.bot_status.update_one({"user_id": user_id}, {"$set": doc}, upsert=True)
        results['bot_status'] = "updated"
    
    if data.treasury:
        doc = data.treasury.model_dump()
        doc['user_id'] = user_id
        doc['timestamp'] = doc['timestamp'].isoformat()
        await db.treasury_history.insert_one(doc)
        await db.treasury_current.update_one(
            {"user_id": user_id},
            {"$set": {
                "treasury_sol": data.treasury.treasury_sol,
                "treasury_usd": data.treasury.treasury_usd,
                "sol_price": data.treasury.sol_price,
                "updated_at": doc['timestamp'],
                "user_id": user_id
            }},
            upsert=True
        )
        results['treasury'] = "recorded"
    
    if data.positions is not None:
        await db.positions.delete_many({"user_id": user_id})
        for pos in data.positions:
            doc = pos.model_dump()
            doc['id'] = str(uuid.uuid4())
            doc['user_id'] = user_id
            doc['entry_time'] = doc['entry_time'].isoformat()
            await db.positions.insert_one(doc)
        results['positions'] = f"synced {len(data.positions)}"
    
    if data.new_trades:
        for trade in data.new_trades:
            doc = trade.model_dump()
            doc['id'] = str(uuid.uuid4())
            doc['user_id'] = user_id
            doc['entry_time'] = doc['entry_time'].isoformat()
            doc['exit_time'] = doc['exit_time'].isoformat()
            await db.trades.insert_one(doc)
        results['trades'] = f"added {len(data.new_trades)}"
    
    if data.activity_logs:
        for log in data.activity_logs:
            doc = log.model_dump()
            doc['id'] = str(uuid.uuid4())
            doc['user_id'] = user_id
            doc['timestamp'] = datetime.now(timezone.utc).isoformat()
            await db.activity_logs.insert_one(doc)
        results['activity'] = f"logged {len(data.activity_logs)}"
    
    if data.watchlist is not None:
        await db.watchlist.delete_many({"user_id": user_id})
        for token in data.watchlist:
            doc = token.model_dump()
            doc['user_id'] = user_id
            doc['last_update'] = doc['last_update'].isoformat()
            await db.watchlist.insert_one(doc)
        results['watchlist'] = f"synced {len(data.watchlist)}"
    
    # Notify WebSocket clients of the update
    try:
        dashboard_data = await get_dashboard_data(user_id)
        await notify_user_update(user_id, "sync_update", dashboard_data)
    except Exception as e:
        logger.warning(f"Failed to notify WebSocket clients: {e}")
    
    return {"status": "success", "results": results}

# ═══════════════════════════════════════════════════════════════════
# Health Check
# ═══════════════════════════════════════════════════════════════════

@api_router.get("/")
async def root():
    return {"message": "Lifecycle Bot Dashboard API", "status": "running"}

@api_router.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.now(timezone.utc).isoformat()}

# ═══════════════════════════════════════════════════════════════════
# WebSocket for Real-time Updates
# ═══════════════════════════════════════════════════════════════════

class ConnectionManager:
    """Manages WebSocket connections for real-time dashboard updates"""
    def __init__(self):
        self.active_connections: Dict[str, List[WebSocket]] = {}  # user -> [connections]
    
    async def connect(self, websocket: WebSocket, user_id: str):
        await websocket.accept()
        if user_id not in self.active_connections:
            self.active_connections[user_id] = []
        self.active_connections[user_id].append(websocket)
        logger.info(f"WebSocket connected for user {user_id}")
    
    def disconnect(self, websocket: WebSocket, user_id: str):
        if user_id in self.active_connections:
            if websocket in self.active_connections[user_id]:
                self.active_connections[user_id].remove(websocket)
            if not self.active_connections[user_id]:
                del self.active_connections[user_id]
        logger.info(f"WebSocket disconnected for user {user_id}")
    
    async def broadcast_to_user(self, user_id: str, message: dict):
        """Send update to all connections for a specific user"""
        if user_id in self.active_connections:
            disconnected = []
            for connection in self.active_connections[user_id]:
                try:
                    await connection.send_json(message)
                except Exception:
                    disconnected.append(connection)
            for conn in disconnected:
                self.disconnect(conn, user_id)

ws_manager = ConnectionManager()

@app.websocket("/ws/{token}")
async def websocket_endpoint(websocket: WebSocket, token: str):
    """WebSocket endpoint for real-time dashboard updates"""
    # Validate token - check if session exists
    session = await db.sessions.find_one({"token": token})
    if not session:
        await websocket.close(code=4001, reason="Invalid or expired token")
        return
    
    # Use username as user_id if user_id field doesn't exist
    user_id = session.get("user_id") or session.get("username", "default")
    await ws_manager.connect(websocket, user_id)
    
    try:
        # Send initial state
        dashboard_data = await get_dashboard_data(user_id)
        await websocket.send_json({"type": "init", "data": dashboard_data})
        
        # Keep connection alive and handle incoming messages
        while True:
            try:
                data = await asyncio.wait_for(websocket.receive_text(), timeout=30)
                msg = json.loads(data)
                
                if msg.get("type") == "ping":
                    await websocket.send_json({"type": "pong"})
                elif msg.get("type") == "refresh":
                    dashboard_data = await get_dashboard_data(user_id)
                    await websocket.send_json({"type": "update", "data": dashboard_data})
                    
            except asyncio.TimeoutError:
                # Send heartbeat
                await websocket.send_json({"type": "heartbeat"})
                
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket, user_id)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        ws_manager.disconnect(websocket, user_id)

async def get_dashboard_data(user_id: str) -> dict:
    """Get complete dashboard data for a user"""
    # Try user-specific data first, then fall back to global/default data
    
    # Get bot status
    bot_status = await db.bot_status.find_one({"user_id": user_id}, {"_id": 0})
    if not bot_status:
        bot_status = await db.bot_status.find_one({"bot_id": "default"}, {"_id": 0})
    
    # Get positions (try user-specific, then all)
    positions = await db.positions.find({"user_id": user_id}, {"_id": 0}).to_list(100)
    if not positions:
        positions = await db.positions.find({}, {"_id": 0}).to_list(100)
    
    # Get recent trades
    trades = await db.trades.find({"user_id": user_id}).sort("exit_time", -1).limit(20).to_list(20)
    if not trades:
        trades = await db.trades.find({}).sort("exit_time", -1).limit(20).to_list(20)
    for t in trades:
        t.pop("_id", None)
    
    # Get treasury
    treasury = await db.treasury_current.find_one({"user_id": user_id}, {"_id": 0})
    if not treasury:
        treasury = await db.treasury_current.find_one({"_type": "current"}, {"_id": 0})
    
    # Get watchlist
    watchlist = await db.watchlist.find({"user_id": user_id}, {"_id": 0}).to_list(50)
    if not watchlist:
        watchlist = await db.watchlist.find({}, {"_id": 0}).to_list(50)
    
    # Calculate stats from all trades
    all_trades = await db.trades.find({"user_id": user_id}).to_list(1000)
    if not all_trades:
        all_trades = await db.trades.find({}).to_list(1000)
    
    wins = [t for t in all_trades if t.get("is_win", t.get("pnl_sol", 0) > 0)]
    losses = [t for t in all_trades if not t.get("is_win", t.get("pnl_sol", 0) > 0)]
    
    total_pnl = sum(t.get("pnl_sol", 0) for t in all_trades)
    
    return {
        "bot_status": bot_status or {"is_running": False},
        "positions": positions,
        "trades": trades,
        "treasury": treasury or {"treasury_sol": 0, "treasury_usd": 0},
        "watchlist": watchlist,
        "stats": {
            "total_trades": len(all_trades),
            "wins": len(wins),
            "losses": len(losses),
            "win_rate": len(wins) / len(all_trades) * 100 if all_trades else 0,
            "total_pnl_sol": total_pnl,
            "open_positions": len(positions),
        }
    }

async def notify_user_update(user_id: str, update_type: str, data: dict):
    """Notify user's WebSocket connections of an update"""
    await ws_manager.broadcast_to_user(user_id, {
        "type": update_type,
        "data": data,
        "timestamp": datetime.now(timezone.utc).isoformat()
    })

# Include the router in the main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
