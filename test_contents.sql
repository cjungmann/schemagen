-- Here are several constructs that can be used to test the
-- functioning of the schemagen app

CREATE TABLE IF NOT EXISTS Person (
   id    INT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
   lname VARCHAR(24),
   fname VARCHAR(24),
   mname VARCHAR(24),
   birthday DATETIME,

   INDEX(lname),
   INDEX(birthday)
);

CREATE TABLE IF NOT EXISTS AllTypes (
   id             INT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
   title          ENUM('Mr', 'Mrs', 'Ms', 'Dr', 'Dame', 'Sir'),
   name           VARCHAR(80),
   wage           DECIMAL(10,2),
   empid          CHAR(6),
   family_members TINYINT,
   friends        SMALLINT,
   ancestors      MEDIUMINT,
   hairs          INTEGER,
   bloodcells     BIGINT,
   birthday       DATE,
   bedtime        TIME,
   notes          MEDIUMTEXT,
   characteristics SET('smart','beautiful','patient','generous','wise','kind','optimistic','happy','persistent')
);

DELIMITER $

DROP PROCEDURE IF EXISTS Add_Person $
CREATE PROCEDURE Add_Person(lname VARCHAR(24), fname VARCHAR(24), nmame VARCHAR(24), birthday DATETIME)
BEGIN
   INSERT INTO Person (lname, fname, mname, birthday)
          VALUES(lname, fname, mname, birthday);
END $

DROP PROCEDURE IF EXISTS Get_Birthdays $
CREATE PROCEDURE Get_Birthdays(birthday DATETIME)
BEGIN
   SELECT p.id, p.lname, p.fname, p.mname
     FROM Person p
    WHERE p.birthday = birthday;
END $


DELIMITER ;
