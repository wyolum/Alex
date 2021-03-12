import sqlite3

class Struct:
    def __init__(self, **kwargs):
        self.attrs = kwargs
        self.__dict__.update(kwargs)
    def keys(self):
        return self.attrs.keys()
    def __getitem__(self, key):
        return self.attrs[key]
    def __repr__(self):
        return f'Struct(**{self.attrs})'
class Table:
    def __init__(self, name, *columns):
        self.name = name
        self.columns = columns

    def create(self, db):
        cols = ['%s' % col for col in self.columns]
        sql = 'CREATE TABLE IF NOT EXISTS %s (%s);' % (self.name, ','.join(cols))
        db.execute(sql)

    def drop(self, db):
        sql = 'DROP TABLE %s' % self.name
        response = input('Warning, dropping table %s\nY to confirm: ' % self.name)
        if response[0] == 'Y':
            db.execute(sql)
            print ('%s Dropped' % self.name)
        else:
            print ('Drop not executed')
    def create_index(self, db, colnames, unique=False):
        idx_name = ''.join(colnames)
        cols = ','.join(colnames)
        unique = ['', 'UNIQUE'][unique]
        sql = 'CREATE %s INDEX %s ON %s(%s)' % (unique, idx_name, self.name, cols)
        db.execute(sql)
    def insert(self, db, values):
        place_holders = ','.join('?' * len(values[0]))
        cols = ','.join([col.name for col in self.columns])
        sql = 'INSERT INTO %s(%s) VALUES (%s);' % (self.name, cols, place_holders)
        #print('sql:', sql)
        rowcount = 0
        for row in values:
            ### add quote to string fields
            try:
                rowcount += db.executemany(sql, [row]).rowcount
            except sqlite3.IntegrityError:
                pass
            db.commit()
        return rowcount

    def delete(self, db, where):
        sql = f'DELETE FROM {self.name} WHERE {where}'
        #<print(sql)
        try:
            cur = db.execute(sql)
            db.commit()
        except sqlite3.OperationalError:
            print(sql)
            raise
        
    def select(self, db, where=None):
        sql = 'SELECT * FROM %s' % self.name
        if where is not None:
            sql += ' WHERE ' + where
        try:
            cur = db.execute(sql)
        except sqlite3.OperationalError:
            print(sql)
            raise
        out = []
        colnames = [col.name for col in self.columns]
        for row in cur.fetchall():
            l = Struct(**dict(zip(colnames, row)))
            out.append(l)
        return out

    def join(self, db, other, col, where=None):
        sql = 'SELECT * FROM %s LEFT JOIN %s ON %s.%s' % (self.name, other.name, self.name, col)
        if where:
            sql += ' WHERE ' + where
        cur = db.execute(sql)
        colnames = [l[0] for l in cur.description]
        out = []
        for row in cur.fetchall():
            l = dict(zip(colnames, row))
            out.append(l)
        return out

class Column:
    def __init__(self, name, type, **kw):
        self.name = name
        self.type = type
        self.kw = kw
    def __str__(self):
        kw = ''
        for k in self.kw:
            if self.kw[k]:
                kw = kw + ' ' + '%s' % (k.upper())
        return '%s %s %s' % (self.name, self.type.name, kw)

class DBType:
    def __init__(self, name):
        self.name = name
class Integer(DBType):
    def __init__(self):
        DBType.__init__(self, 'INTEGER')
        self.convert = int
class Float(DBType):
    def __init__(self):
        DBType.__init__(self, 'FLOAT')
        self.convert = float
class String(DBType):
    def __init__(self):
        DBType.__init__(self, 'STRING')
        self.convert = str
class Boolean(DBType):
    def __init__(self):
        DBType.__init__(self, 'BOOLEAN')
        self.convert = bool
class Text(DBType):
    def __init__(self):
        DBType.__init__(self, 'TEXT')
        self.convert = str
