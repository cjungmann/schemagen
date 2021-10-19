-- Here are several constructs that can be used to test the
-- functioning of the schemagen app

CREATE TABLE Person (
   id    INT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
   lname VARCHAR(24),
   fname VARCHAR(24),
   mname VARCHAR(24),
   birthday DATETIME,

   INDEX(lname),
   INDEX(birthday)
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
