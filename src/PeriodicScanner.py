import psycopg2


class PeriodicScanner:
    def __init__(self) -> None:
        pass

    def perform_scan(self) -> None:
        """
        Perform a scan based on the selection provided by the database
        """
        pass

    def notify_subscribed_users(self) -> None:
        """
        Notify users if a new result is dropped
        """
        pass


if __name__ == "__main__":
    scanner = PeriodicScanner()
    scanner.perform_scan()
    scanner.notify_subscribed_users()
