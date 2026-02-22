from app.db.models import User
from app.repositories.interfaces.base_repository import IRepository
from app.repositories.implementations.sqlalchemy.base_repository import Repository
from app.domain.entitites import UserEntity

class UserRepository(Repository[User, UserEntity]):
    model = User
    entity = UserEntity