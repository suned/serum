from typing import NamedTuple, List
import argparse
from datetime import datetime
from unittest.mock import MagicMock
import sqlite3
from serum import Dependency, Environment, inject, abstractmethod, immutable


class ListItem(NamedTuple):
    title: str
    comment: str
    due_date = datetime


class Log(Dependency):
    @abstractmethod
    def info(self, message: str):
        pass

    @abstractmethod
    def error(self, message: str):
        pass


class ItemReader(Dependency):
    @abstractmethod
    def more_items(self):
        pass

    @abstractmethod
    def next_item(self) -> ListItem:
        pass


class ItemWriter(Dependency):
    @abstractmethod
    def write_item(self, item: ListItem):
        pass


class Database(Dependency):
    @abstractmethod
    def save_item(self, item: ListItem) -> None:
        pass

    @abstractmethod
    def get_items(self) -> List[ListItem]:
        pass


class Arguments(Dependency):
    @property
    @abstractmethod
    def log_level(self) -> int:
        pass


class ConsoleArguments(Arguments):
    def _parse_args(self):
        parser = argparse.ArgumentParser()
        parser.add_argument(
            '--log-level',
            default=1,
            type=int
        )
        return parser.parse_args()

    @property
    def log_level(self) -> int:
        return self._parse_args().log_level


class MockLog(Log, MagicMock):
    pass


class SQLiteDatabase(Database):
    db_name = immutable('example.db')
    connection = None

    def connect(self):
        if self.connection is None:
            self.connection = sqlite3.connect(self.db_name)

    def get_items(self) -> [ListItem]:


    def save_item(self, item: ListItem) -> None:
        pass


class InMemoryDatabase(SQLiteDatabase):
    db_name = immutable(':memory:')


class SimpleLog(Log):
    arguments = inject(Arguments)

    def info(self, message: str):
        if self.arguments.log_level > 1:
            print('INFO:', message)

    def error(self, message: str):
        if self.arguments.log_level > 0:
            print('ERROR:', message)


class ToDoApplication:
    database = inject(Database)
    log = inject(Log)
    reader = inject(ItemReader)
    writer = inject(ItemWriter)

    def run(self):
        self.report_items()
        self.read_items()

    def read_items(self):
        self.log.info('Reading items...')
        while self.reader.more_items():
            try:
                item = self.read_item()
                self.database.save_item(item)
            except:
                self.log.error('Could not read item')

    def read_item(self):
        item = self.reader.next_item()
        self.log.info('Got item: '.format(str(item)))
        return item

    def report_items(self):
        self.log.info('Reporting Items...')
        for item in self.database.get_items():
            self.writer.write_item(item)

def production_environment() -> Environment:
    return Environment(
        SQLiteDatabase,
        SimpleLog,
        ConsoleArguments,
        ConsoleItemReader,
        ConsoleItemWriter
    )

def dev_environment() -> Environment:
    return Environment(
        InMemoryDatabase,
        SimpleLog,
        ConsoleArguments,
        ConsoleItemReader,
        ConsoleItemWriter
    )

def test_environment() -> Environment:
    return Environment(
        InMemoryDatabase,
        DummyLog,
        DummyArguments,
        DummyItemReader,
        DummyItemWriter,
    )

if __name__ == '__main__':
    with production_environment():
        app = ToDoApplication()
        app.run()
