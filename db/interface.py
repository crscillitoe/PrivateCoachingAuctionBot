from sqlalchemy import create_engine, select, insert, update, func
from sqlalchemy.orm import sessionmaker

from datetime import datetime

from .models import Base, Auction, Bid

from config import Config

from typing import Optional

class DB:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(DB, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        username = Config["MySQL"]["Username"]
        password = Config["MySQL"]["Password"]
        db_host = Config["MySQL"]["Host"]
        db_name = Config["MySQL"]["DBName"]

        self.engine = create_engine(f"mysql+pymysql://{username}:{password}@{db_host}/{db_name}")
        self.session = sessionmaker(self.engine, autoflush=True, autocommit=True)

        Base.metadata.create_all(self.engine)

    def get_current_auction(self) -> Optional[Auction]:
        with self.session() as sess:
            result = sess.execute(
                select(Auction)
                .where(Auction.active == True)
                .where(Auction.start_date <= func.current_date())
                .where(Auction.end_date > func.current_date())
                .order_by(Auction.id.desc())
                .limit(1)
            ).all()

        if len(result) == 0:
            return None

        return result[0][0]

    def get_bid(self, auction_id: int, user_id: int) -> Optional[Bid]:
        with self.session() as sess:
            result = sess.execute(
                select(Bid)
                .where(Bid.auction_id == auction_id)
                .where(Bid.user_id == user_id)
            ).all()

        if len(result) == 0:
            return None

        return result[0][0]

    def make_bid(self, auction_id: int, user_id: int, amount: int) -> None:
        with self.session() as sess:
            sess.execute(
                insert(Bid)
                .values(
                    auction_id=auction_id,
                    user_id=user_id,
                    amount=amount
                )
            )

    def revoke_bid(self, bid_id: int) -> None:
        with self.session() as sess:
            sess.execute(
                update(Bid)
                .where(Bid.id == bid_id)
                .values(revoked=True, revoked_at=datetime.now())
                .execution_options(synchronize_session="fetch")
            )

