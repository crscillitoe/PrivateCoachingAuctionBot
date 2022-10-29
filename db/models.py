from sqlalchemy import BigInteger, Boolean, Column, Date, ForeignKey, Integer, DateTime, func
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()

class Auction(Base):
    __tablename__ = "auctions"
    id = Column(Integer, primary_key=True)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    active = Column(Boolean, default=False)

    bids = relationship("Bid", back_populates="auction")

    def __repr__(self):
        return f"Auction(id={self.id!r}, start_date={self.start_date!r}, end_date={self.end_date!r}, active={self.active!r})"


class Bid(Base):
    __tablename__ = "bids"

    id = Column(Integer, primary_key=True)
    auction_id = Column(Integer, ForeignKey("auctions.id"))
    user_id = Column(BigInteger, default=0)
    amount = Column(Integer, default=0)
    placed_at = Column(DateTime, default=func.now())

    auction = relationship("Auction", back_populates="bids")

    def __repr__(self):
        return f"Bid(id={self.id!r}, auction_id={self.auction_id!r}, user_id={self.user_id!r}, amount={self.amount!r})"
