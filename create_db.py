from database import Base, engine

# Tabloları oluştur
Base.metadata.create_all(bind=engine)
print("Veritabanı ve tablolar oluşturuldu!")
