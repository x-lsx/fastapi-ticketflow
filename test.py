import app.db.base
from app.db.postgres import Base
print(sorted(Base.metadata.tables))