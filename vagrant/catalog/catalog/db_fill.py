from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database_setup import Base, Category, Item

# Setup the Database for populating
engine = create_engine('sqlite:///itemcatalog.db')
Base.metadata.bind = engine
DBSession = sessionmaker(bind = engine)

session = DBSession()

# Add a Category:
myCategory = Category(name = "Test Category")
session.add(myCategory)
session.commit()

# Read Categories from Database
session.query(Category).all()

# Add Items:
testItem = Item(name = "Test Item",
    description = "This is the first Item in the database! If you see me I work!",
    price = "$1.11", category = myCategory)
session.add(testItem)
session.commit()

# Read Items from Database
session.query(Item).all()