from app.database import init_database


def main() -> None:
    # Import registers the mobile tables with SQLAlchemy metadata.
    from app.database import mobile_models  # noqa: F401

    init_database()
    print("NTIM-002A mobile database tables are ready.")


if __name__ == "__main__":
    main()
